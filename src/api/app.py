"""Streamlit entrypoint - the UI/interface layer only.

All real logic lives in src/core; this file wires it together and
manages Streamlit's own state model. Streamlit reruns this entire
script on every interaction, so anything expensive (embedding client,
vectorstore, compiled graph) is cached via st.cache_resource - built
once, reused across reruns - rather than rebuilt every time
(docs/architecture.md §6).

Two screens, gated by st.session_state.active_workspace:
- picker (active_workspace is None): pick an existing workspace or
  create a new one
- workspace (active_workspace is set): today's upload/chat UI, scoped
  to that workspace's own Chroma collection
"""

import sys
from pathlib import Path

# pyproject.toml deliberately doesn't install this as a package
# (package = false), and pythonpath = ["src"] in [tool.pytest.ini_options]
# only applies to pytest - streamlit run and plain python don't see it.
# This makes `from core...`/`from utils...` resolve regardless of how the
# app is launched (make run, a bare `streamlit run`, an IDE's run button).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

from core.agent import build_graph
from core.config import get_config
from core.embedding_registry import EMBEDDING_REGISTRY
from core.ingestion import ingest_pdf_bytes
from core.vectorstore import get_vectorstore
from core.workspace import WorkspaceInfo, create_workspace, delete_workspace, list_workspaces

st.set_page_config(page_title="Enterprise Policy Q&A Bot")


@st.cache_resource
def _get_embeddings(model_name: str):
    return EMBEDDING_REGISTRY[model_name]()


@st.cache_resource
def _get_vectorstore(persist_dir: str, collection_name: str, model_name: str):
    return get_vectorstore(persist_dir, collection_name, _get_embeddings(model_name))


@st.cache_resource
def _get_graph(persist_dir: str, collection_name: str, model_name: str):
    config = get_config()
    if not config.chat_model_name:
        raise RuntimeError("CHAT_MODEL_NAME is not set - check your .env file.")
    llm = ChatGoogleGenerativeAI(model=config.chat_model_name)
    return build_graph(_get_vectorstore(persist_dir, collection_name, model_name), llm)


def _open_workspace(ws: WorkspaceInfo) -> None:
    st.session_state.active_workspace = ws
    st.session_state.messages = []
    st.session_state.ingested_file_ids = set()
    st.session_state.uploader_key += 1
    st.session_state.confirm_delete = False


def _close_workspace() -> None:
    st.session_state.active_workspace = None
    st.session_state.messages = []
    st.session_state.ingested_file_ids = set()
    st.session_state.uploader_key += 1
    st.session_state.confirm_delete = False


def _init_session_state() -> None:
    if "active_workspace" not in st.session_state:
        st.session_state.active_workspace = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "ingested_file_ids" not in st.session_state:
        st.session_state.ingested_file_ids = set()
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False


def _render_picker() -> None:
    config = get_config()
    st.title("Enterprise Policy Q&A Bot")
    st.header("Workspaces")

    workspaces = list_workspaces(config.chroma_persist_dir)
    if not workspaces:
        st.caption("No workspaces yet - create one below.")
    for ws in workspaces:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{ws.display_name}**  \n{ws.embedding_model} · created {ws.created_at}")
        if col2.button("Open", key=f"open_{ws.collection_name}"):
            _open_workspace(ws)
            st.rerun()

    st.divider()
    st.subheader("Create a new workspace")
    new_name = st.text_input("Workspace name", key="new_workspace_name")
    new_model = st.selectbox(
        "Embedding model", options=list(EMBEDDING_REGISTRY.keys()), key="new_workspace_model"
    )
    if st.button("Create workspace", disabled=not new_name.strip()):
        ws = create_workspace(config.chroma_persist_dir, new_name.strip(), new_model)
        _open_workspace(ws)
        st.rerun()


def _render_workspace() -> None:
    config = get_config()
    ws = st.session_state.active_workspace

    st.title("Enterprise Policy Q&A Bot")
    st.subheader(ws.display_name)
    st.caption(f"Embedding model: {ws.embedding_model}")
    if st.button("← Back to workspaces"):
        _close_workspace()
        st.rerun()

    vectorstore = _get_vectorstore(
        config.chroma_persist_dir, ws.collection_name, ws.embedding_model
    )

    uploaded_files = st.file_uploader(
        "Upload policy PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.file_id in st.session_state.ingested_file_ids:
                continue
            with st.status(f"Ingesting {uploaded_file.name}...", expanded=True) as status:
                status.write(
                    "Free-tier rate limits mean large documents embed in "
                    "paced batches - this can take several minutes."
                )
                chunk_count = ingest_pdf_bytes(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                    vectorstore,
                    on_progress=status.write,
                )
                status.update(
                    label=f"Ingested {uploaded_file.name}: {chunk_count} chunks",
                    state="complete",
                )
            st.session_state.ingested_file_ids.add(uploaded_file.file_id)

    if not st.session_state.confirm_delete:
        if st.button("Delete this workspace"):
            st.session_state.confirm_delete = True
            st.rerun()
    else:
        st.warning(f'Delete "{ws.display_name}" permanently? This cannot be undone.')
        col_a, col_b = st.columns(2)
        if col_a.button("Confirm delete", type="primary"):
            delete_workspace(config.chroma_persist_dir, ws.collection_name)
            _get_vectorstore.clear()
            _get_graph.clear()
            _close_workspace()
            st.rerun()
        if col_b.button("Cancel"):
            st.session_state.confirm_delete = False
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    question = st.chat_input("Ask a question about the ingested policies")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        graph = _get_graph(config.chroma_persist_dir, ws.collection_name, ws.embedding_model)
        result = graph.invoke({"question": question})
        answer = result["answer"]
        documents = result["documents"]

        with st.chat_message("assistant"):
            st.write(answer)
            if documents:
                with st.expander("Sources"):
                    for doc in documents:
                        source = doc.metadata.get("source", "unknown")
                        page = doc.metadata.get("page", "?")
                        st.caption(f"{source}, page {page}")

        st.session_state.messages.append({"role": "assistant", "content": answer})


_init_session_state()

if st.session_state.active_workspace is None:
    _render_picker()
else:
    _render_workspace()
