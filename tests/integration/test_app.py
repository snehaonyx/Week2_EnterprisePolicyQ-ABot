"""End-to-end test of the Streamlit app via AppTest - runs the real
script headlessly, with the embedding model and chat LLM swapped for
fakes so this stays offline (no real Gemini API calls).

AppTest runs in-process and shares sys.modules, so patching module
attributes before at.run() is picked up by the app's own imports -
verified directly before relying on it here.
"""

from pathlib import Path

import streamlit as st
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parent.parent.parent / "src" / "api" / "app.py"


class _FakeChatModel:
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        return AIMessage(content="This is a fake grounded answer.")


def _make_app_test(monkeypatch, tmp_path) -> AppTest:
    # st.cache_resource is a global, process-wide cache - clearing it
    # between tests prevents one test's cached vectorstore/graph (keyed
    # partly on this test's own tmp_path) from leaking into another.
    st.cache_resource.clear()

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path))
    monkeypatch.setenv("CHAT_MODEL_NAME", "fake-model")
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key")

    import core.embedding_registry as embedding_registry_module

    monkeypatch.setitem(
        embedding_registry_module.EMBEDDING_REGISTRY,
        "gemini-embedding-001",
        lambda: DeterministicFakeEmbedding(size=16),
    )
    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI", _FakeChatModel)

    return AppTest.from_file(str(APP_PATH), default_timeout=15)


def _click_button(at: AppTest, label: str) -> None:
    next(b for b in at.button if b.label == label).click()


def _click_open(at: AppTest) -> None:
    """Clicks the (only, in these tests) workspace-row 'Open' button -
    those share a label but are distinguished by their key prefix."""
    next(b for b in at.button if b.key and b.key.startswith("open_")).click()


def _create_workspace(at: AppTest, name: str) -> AppTest:
    """Fills the picker's create-workspace form and submits it. Caller
    must have already called at.run() at least once."""
    at.text_input(key="new_workspace_name").set_value(name)
    _click_button(at, "Create workspace")
    at.run()
    return at


def _upload(at: AppTest, sample_pdf_path: Path) -> AppTest:
    at.file_uploader[0].set_value(
        (sample_pdf_path.name, sample_pdf_path.read_bytes(), "application/pdf")
    )
    at.run()
    return at


def test_picker_shown_on_first_load_with_no_workspaces(monkeypatch, tmp_path):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()

    assert not at.exception
    assert len(at.file_uploader) == 0
    assert len(at.text_input) == 1
    assert any(b.label == "Create workspace" for b in at.button)


def test_creating_workspace_opens_it(monkeypatch, tmp_path):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()

    _create_workspace(at, "HR Policies")

    assert not at.exception
    assert len(at.file_uploader) == 1
    assert any("HR Policies" in h.value for h in at.subheader)


def test_create_upload_ask_shows_grounded_answer(monkeypatch, tmp_path, sample_pdf_a_path):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()
    _create_workspace(at, "HR Policies")
    _upload(at, sample_pdf_a_path)
    assert any(s.state == "complete" and "Ingested" in s.label for s in at.status)

    at.chat_input[0].set_value("How many sick days do I get?")
    at.run()

    assert not at.exception
    roles_and_content = [(m.name, m.markdown[0].value) for m in at.chat_message]
    assert ("user", "How many sick days do I get?") in roles_and_content
    assert ("assistant", "This is a fake grounded answer.") in roles_and_content


def test_reopening_workspace_preserves_documents_and_locks_model(
    monkeypatch, tmp_path, sample_pdf_a_path
):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()
    _create_workspace(at, "HR Policies")
    _upload(at, sample_pdf_a_path)

    _click_button(at, "← Back to workspaces")
    at.run()
    assert len(at.file_uploader) == 0  # back on the picker

    open_buttons = [b for b in at.button if b.key and b.key.startswith("open_")]
    assert len(open_buttons) == 1
    _click_open(at)
    at.run()

    assert not at.exception
    assert len(at.file_uploader) == 1  # reopened into the workspace screen
    assert len(at.selectbox) == 0  # model not offered as an editable choice

    at.chat_input[0].set_value("How many sick days do I get?")
    at.run()
    roles_and_content = [(m.name, m.markdown[0].value) for m in at.chat_message]
    assert ("assistant", "This is a fake grounded answer.") in roles_and_content


def test_chat_history_does_not_persist_across_reopen(monkeypatch, tmp_path, sample_pdf_a_path):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()
    _create_workspace(at, "HR Policies")
    _upload(at, sample_pdf_a_path)
    at.chat_input[0].set_value("How many sick days do I get?")
    at.run()
    assert len(at.chat_message) > 0

    _click_button(at, "← Back to workspaces")
    at.run()
    _click_open(at)
    at.run()

    assert len(at.chat_message) == 0


def test_delete_requires_confirm(monkeypatch, tmp_path, sample_pdf_a_path):
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()
    _create_workspace(at, "HR Policies")
    _upload(at, sample_pdf_a_path)

    _click_button(at, "Delete this workspace")
    at.run()

    # Still on the workspace screen, not deleted yet - a warning and the
    # confirm/cancel controls are showing instead.
    assert len(at.file_uploader) == 1
    assert len(at.warning) == 1
    assert any(b.label == "Confirm delete" for b in at.button)

    _click_button(at, "Cancel")
    at.run()
    assert len(at.file_uploader) == 1  # cancel returns to the normal workspace screen
    assert len(at.warning) == 0

    _click_button(at, "Delete this workspace")
    at.run()
    _click_button(at, "Confirm delete")
    at.run()

    assert not at.exception
    assert len(at.file_uploader) == 0  # back on the picker
    assert not any("HR Policies" in w.value for w in at.markdown)


def test_workspaces_are_physically_isolated(monkeypatch, tmp_path, sample_pdf_a_path):
    """The whole point of collection-per-workspace: a question asked in
    one workspace must never be answered from another workspace's
    documents.

    The fake chat model always returns the same canned text regardless
    of input, so the answer text can't prove isolation - but the
    retrieved documents can. Workspace B has nothing uploaded to it; if
    its collection were somehow sharing A's data (an isolation bug),
    B's retrieval would return A's real chunks. The UI only renders a
    "Sources" expander when documents were actually retrieved, so its
    absence is the direct, visible proof that nothing leaked from A."""
    at = _make_app_test(monkeypatch, tmp_path)
    at.run()
    _create_workspace(at, "Workspace A")
    _upload(at, sample_pdf_a_path)
    _click_button(at, "← Back to workspaces")
    at.run()

    _create_workspace(at, "Workspace B")
    assert len(at.file_uploader) == 1  # in B now, nothing uploaded to it

    at.chat_input[0].set_value("How many sick days do I get?")
    at.run()

    assert not at.exception
    assistant_messages = [m for m in at.chat_message if m.name == "assistant"]
    assert len(assistant_messages) == 1
    assert len(at.expander) == 0  # no Sources shown - nothing was retrieved from A
