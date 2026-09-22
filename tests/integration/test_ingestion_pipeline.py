from langchain_core.embeddings import DeterministicFakeEmbedding, Embeddings

from core.ingestion import ingest_pdf_bytes
from core.vectorstore import get_vectorstore


def test_cumulative_ingestion_across_two_uploads(
    tmp_path, fake_embeddings, sample_pdf_a_path, sample_pdf_b_path
):
    """Proves FR-1.3: a second upload adds to the existing corpus rather
    than replacing it - required for cross-document questions to work."""
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", fake_embeddings)

    count_a = ingest_pdf_bytes(sample_pdf_a_path.read_bytes(), "sample_policy_a.pdf", vectorstore)
    count_b = ingest_pdf_bytes(sample_pdf_b_path.read_bytes(), "sample_policy_b.pdf", vectorstore)

    assert count_a > 0
    assert count_b > 0

    all_chunks = vectorstore.similarity_search("policy", k=count_a + count_b)
    sources = {chunk.metadata["source"] for chunk in all_chunks}
    assert sources == {"sample_policy_a.pdf", "sample_policy_b.pdf"}


def test_ingested_chunks_cite_the_real_filename_not_the_temp_path(
    tmp_path, fake_embeddings, sample_pdf_a_path
):
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", fake_embeddings)

    ingest_pdf_bytes(sample_pdf_a_path.read_bytes(), "sample_policy_a.pdf", vectorstore)

    results = vectorstore.similarity_search("policy", k=10)
    assert all(chunk.metadata["source"] == "sample_policy_a.pdf" for chunk in results)
    assert all(".tmp" not in chunk.metadata["source"] for chunk in results)


class _FakeBatchAwareEmbeddings(Embeddings):
    """Mimics _RateLimitedEmbeddings's public on_batch contract (without
    real batching/sleeping), so ingest_pdf_bytes's progress-wiring logic
    can be tested without the real rate-limited wrapper."""

    def __init__(self):
        self._inner = DeterministicFakeEmbedding(size=16)
        self.on_batch = None

    def embed_query(self, text):
        return self._inner.embed_query(text)

    def embed_documents(self, texts):
        if self.on_batch:
            self.on_batch(1, 1)
        return self._inner.embed_documents(texts)


def test_ingest_pdf_bytes_reports_progress_and_restores_previous_hook(tmp_path, sample_pdf_a_path):
    embeddings = _FakeBatchAwareEmbeddings()
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", embeddings)
    messages: list[str] = []

    def original_hook(i, n):
        raise AssertionError("original hook should not be called during ingest_pdf_bytes")

    embeddings.on_batch = original_hook

    ingest_pdf_bytes(
        sample_pdf_a_path.read_bytes(),
        "sample_policy_a.pdf",
        vectorstore,
        on_progress=messages.append,
    )

    assert any("Loading" in m for m in messages)
    assert any("Split" in m for m in messages)
    assert any("batch 1 of 1" in m for m in messages)
    assert embeddings.on_batch is original_hook  # restored after the call, not left dangling
