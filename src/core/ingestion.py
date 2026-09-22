"""Load and chunk PDF documents.

Deliberately the naive choices first (see docs/architecture.md §3):
PyPDFLoader over PDFPlumberLoader (tables collapse into plain text -
that failure mode is worth seeing), RecursiveCharacterTextSplitter with
fixed size/overlap over a structure-aware splitter.

Note: PyPDFLoader lives in langchain-community, which upstream has
marked as being sunset in favor of standalone integration packages.
Still the correct import today; worth re-checking if this starts
warning louder or breaks in a future dependency bump.
"""

from collections.abc import Callable
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.uploaded_file import temp_file_from_bytes

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def load_pdf(path: Path) -> list[Document]:
    """One Document per page, via PyPDFLoader."""
    return PyPDFLoader(str(path)).load()


def split_documents(documents: list[Document]) -> list[Document]:
    """Split into fixed-size, overlapping chunks. source/page metadata
    carries through automatically; no other metadata is added here."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_documents(documents)


def ingest_pdf_bytes(
    file_bytes: bytes,
    filename: str,
    vectorstore: Chroma,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """Loads, chunks, and adds a PDF's bytes to vectorstore.

    Returns the number of chunks added. Overrides the `source` metadata
    with the real filename - PyPDFLoader would otherwise populate it
    with the throwaway temp file path, which means nothing as a
    citation (FR-3.4).

    on_progress, if given, is called with human-readable milestone
    strings - kept as a plain str callback (not Streamlit-specific) so
    this stays UI-agnostic and testable without a browser
    (docs/architecture.md §2). If the vectorstore's embedding function
    supports batch-level progress (an `on_batch` attribute - see
    _RateLimitedEmbeddings), it's wired to on_progress for the duration
    of this call only, then restored, since that embeddings instance is
    cached/reused across calls that shouldn't report to a stale caller.
    """

    def _report(message: str) -> None:
        if on_progress:
            on_progress(message)

    with temp_file_from_bytes(file_bytes, suffix=".pdf") as path:
        _report(f"Loading {filename}...")
        docs = load_pdf(path)
        chunks = split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = filename
        _report(f"Split {filename} into {len(chunks)} chunks. Embedding...")

        embeddings = vectorstore.embeddings
        supports_batch_progress = on_progress and hasattr(embeddings, "on_batch")
        previous_hook = getattr(embeddings, "on_batch", None) if supports_batch_progress else None
        if supports_batch_progress:
            embeddings.on_batch = lambda i, n: _report(f"Embedding {filename}: batch {i} of {n}...")
        try:
            vectorstore.add_documents(chunks)
        finally:
            if supports_batch_progress:
                embeddings.on_batch = previous_hook
    return len(chunks)
