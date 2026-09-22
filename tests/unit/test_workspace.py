import chromadb
import pytest
from chromadb.errors import NotFoundError

from core.workspace import create_workspace, delete_workspace, list_workspaces


def test_create_workspace_returns_info_and_persists_metadata(tmp_path):
    ws = create_workspace(str(tmp_path), "HR Policies", "gemini-embedding-001")

    assert ws.display_name == "HR Policies"
    assert ws.embedding_model == "gemini-embedding-001"
    assert ws.collection_name.startswith("ws-")

    # Independently reopen with a fresh client - metadata must round-trip
    # through disk, not just live in the returned dataclass.
    client = chromadb.PersistentClient(path=str(tmp_path))
    collection = client.get_collection(ws.collection_name)
    assert collection.metadata["display_name"] == "HR Policies"
    assert collection.metadata["embedding_model"] == "gemini-embedding-001"
    assert collection.metadata["created_at"] == ws.created_at


def test_create_workspace_generates_unique_valid_collection_names(tmp_path):
    ws1 = create_workspace(str(tmp_path), "First", "gemini-embedding-001")
    ws2 = create_workspace(str(tmp_path), "Second", "gemini-embedding-001")

    assert ws1.collection_name != ws2.collection_name


def test_list_workspaces_sorted_newest_first(tmp_path):
    """Constructs collections directly with explicit timestamps, rather
    than relying on real wall-clock gaps between two create_workspace()
    calls, to test the sort itself in isolation."""
    client = chromadb.PersistentClient(path=str(tmp_path))
    client.get_or_create_collection(
        "ws-old",
        embedding_function=None,
        metadata={
            "display_name": "Older",
            "embedding_model": "gemini-embedding-001",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )
    client.get_or_create_collection(
        "ws-new",
        embedding_function=None,
        metadata={
            "display_name": "Newer",
            "embedding_model": "gemini-embedding-001",
            "created_at": "2026-01-02T00:00:00+00:00",
        },
    )

    names = [ws.display_name for ws in list_workspaces(str(tmp_path))]
    assert names == ["Newer", "Older"]


def test_list_workspaces_filters_out_collections_missing_expected_metadata(tmp_path):
    """Regression test for the no-migration decision: the orphaned
    pre-workspace `policy_docs` collection (metadata=None) and any
    partially-tagged collection must never appear in the picker."""
    create_workspace(str(tmp_path), "Real Workspace", "gemini-embedding-001")

    client = chromadb.PersistentClient(path=str(tmp_path))
    client.get_or_create_collection("policy_docs", embedding_function=None)  # metadata=None
    client.get_or_create_collection(
        "ws-partial", embedding_function=None, metadata={"display_name": "Partial"}
    )

    names = [ws.display_name for ws in list_workspaces(str(tmp_path))]
    assert names == ["Real Workspace"]


def test_list_workspaces_empty_when_none_created(tmp_path):
    assert list_workspaces(str(tmp_path)) == []


def test_delete_workspace_removes_it(tmp_path):
    ws = create_workspace(str(tmp_path), "Temporary", "gemini-embedding-001")

    delete_workspace(str(tmp_path), ws.collection_name)

    assert list_workspaces(str(tmp_path)) == []
    client = chromadb.PersistentClient(path=str(tmp_path))
    assert ws.collection_name not in [c.name for c in client.list_collections()]


def test_delete_workspace_nonexistent_raises(tmp_path):
    with pytest.raises(NotFoundError):
        delete_workspace(str(tmp_path), "ws-does-not-exist")
