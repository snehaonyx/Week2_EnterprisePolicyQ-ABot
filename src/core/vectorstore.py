"""Chroma vector store: creation, and a real reset.

Reset must clear the actual on-disk collection, not just UI/session
state (docs/architecture.md §7) - otherwise stale vectors silently
pollute later searches after a user thinks they've started fresh.
"""

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings


def get_vectorstore(persist_directory: str, collection_name: str, embeddings: Embeddings) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )


def reset_collection(
    persist_directory: str, collection_name: str, embeddings: Embeddings
) -> Chroma:
    """Deletes the on-disk collection, then returns a fresh, empty one
    at the same location."""
    vectorstore = get_vectorstore(persist_directory, collection_name, embeddings)
    vectorstore.delete_collection()
    return get_vectorstore(persist_directory, collection_name, embeddings)
