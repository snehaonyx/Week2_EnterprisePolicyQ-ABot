from langchain_core.embeddings import Embeddings
from langchain_google_genai._common import GoogleGenerativeAIError

from core.embedding_registry import (
    _BATCH_SIZE,
    _MAX_RETRIES,
    EMBEDDING_REGISTRY,
    _RateLimitedEmbeddings,
)


def test_registry_has_expected_key():
    assert set(EMBEDDING_REGISTRY.keys()) == {"gemini-embedding-001"}


def test_factory_builds_an_embeddings_instance(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy-key-for-construction-only")

    embeddings = EMBEDDING_REGISTRY["gemini-embedding-001"]()

    assert isinstance(embeddings, Embeddings)


class _FakeInnerEmbeddings(Embeddings):
    """Records what it's called with; can be told to fail N times
    before succeeding, to test retry behavior without a real API."""

    def __init__(self, fail_times: int = 0):
        self.calls: list[list[str]] = []
        self._fail_times = fail_times

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if len(self.calls) <= self._fail_times:
            raise GoogleGenerativeAIError("simulated rate limit")
        return [[float(len(t))] for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text))]


def test_embed_documents_splits_into_batches_under_batch_size(monkeypatch):
    monkeypatch.setattr("core.embedding_registry.time.sleep", lambda _seconds: None)
    inner = _FakeInnerEmbeddings()
    wrapped = _RateLimitedEmbeddings(inner)
    texts = [f"text {i}" for i in range(_BATCH_SIZE + 5)]

    results = wrapped.embed_documents(texts)

    assert len(results) == len(texts)
    assert len(inner.calls) == 2
    assert len(inner.calls[0]) == _BATCH_SIZE
    assert len(inner.calls[1]) == 5


def test_embed_documents_sleeps_between_batches_not_before_first(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("core.embedding_registry.time.sleep", sleep_calls.append)
    inner = _FakeInnerEmbeddings()
    wrapped = _RateLimitedEmbeddings(inner)
    texts = [f"text {i}" for i in range(_BATCH_SIZE + 5)]

    wrapped.embed_documents(texts)

    assert len(sleep_calls) == 1  # one gap between two batches, none before the first


def test_embed_documents_retries_after_rate_limit_then_succeeds(monkeypatch):
    monkeypatch.setattr("core.embedding_registry.time.sleep", lambda _seconds: None)
    inner = _FakeInnerEmbeddings(fail_times=1)
    wrapped = _RateLimitedEmbeddings(inner)

    results = wrapped.embed_documents(["one text"])

    assert results == [[8.0]]
    assert len(inner.calls) == 2  # one failed attempt, one that succeeded


def test_embed_documents_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr("core.embedding_registry.time.sleep", lambda _seconds: None)
    inner = _FakeInnerEmbeddings(fail_times=_MAX_RETRIES)
    wrapped = _RateLimitedEmbeddings(inner)

    try:
        wrapped.embed_documents(["one text"])
        raise AssertionError("expected GoogleGenerativeAIError to propagate")
    except GoogleGenerativeAIError:
        pass

    assert len(inner.calls) == _MAX_RETRIES


def test_embed_query_passes_through_without_batching(monkeypatch):
    sleep_calls: list[float] = []
    monkeypatch.setattr("core.embedding_registry.time.sleep", sleep_calls.append)
    inner = _FakeInnerEmbeddings()
    wrapped = _RateLimitedEmbeddings(inner)

    result = wrapped.embed_query("a question")

    assert result == [10.0]
    assert sleep_calls == []
