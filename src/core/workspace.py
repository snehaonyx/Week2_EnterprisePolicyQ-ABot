"""Workspace management: one Chroma collection per workspace, discovered
by scanning collection metadata (docs/adr/0003-collection-per-workspace.md).

Goes through the raw chromadb client, not langchain_chroma's Chroma
wrapper - Chroma exposes no client accessor, and list/create/delete here
are collection-admin operations, not RAG operations. Only build a
langchain Chroma wrapper (core.vectorstore.get_vectorstore) once a
workspace's collection is being used for retrieval/ingestion.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

import chromadb

_EXPECTED_METADATA_KEYS = {"display_name", "embedding_model", "created_at"}


@dataclass(frozen=True)
class WorkspaceInfo:
    collection_name: str  # opaque storage id, e.g. "ws-3f9a2b7c1e4d"
    display_name: str
    embedding_model: str
    created_at: str  # ISO 8601, UTC


def _client(persist_directory: str) -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=persist_directory)


def _generate_collection_name() -> str:
    return f"ws-{secrets.token_hex(6)}"


def create_workspace(
    persist_directory: str, display_name: str, embedding_model: str
) -> WorkspaceInfo:
    created_at = datetime.now(UTC).isoformat()
    collection_name = _generate_collection_name()
    _client(persist_directory).get_or_create_collection(
        name=collection_name,
        embedding_function=None,
        metadata={
            "display_name": display_name,
            "embedding_model": embedding_model,
            "created_at": created_at,
        },
    )
    return WorkspaceInfo(collection_name, display_name, embedding_model, created_at)


def list_workspaces(persist_directory: str) -> list[WorkspaceInfo]:
    workspaces = []
    for collection in _client(persist_directory).list_collections():
        metadata = collection.metadata or {}
        if not _EXPECTED_METADATA_KEYS.issubset(metadata.keys()):
            continue  # not one of ours - e.g. the orphaned pre-workspace `policy_docs`
        workspaces.append(
            WorkspaceInfo(
                collection_name=collection.name,
                display_name=metadata["display_name"],
                embedding_model=metadata["embedding_model"],
                created_at=metadata["created_at"],
            )
        )
    workspaces.sort(key=lambda w: w.created_at, reverse=True)
    return workspaces


def delete_workspace(persist_directory: str, collection_name: str) -> None:
    _client(persist_directory).delete_collection(collection_name)
