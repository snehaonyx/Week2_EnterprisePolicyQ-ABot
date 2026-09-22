"""Registry of available embedding models, keyed for the UI dropdown.

One entry today (see docs/adr/0002-embedding-model-choice.md); adding a
second model later is a new dict entry, not a refactor.
"""

import math
import time
from collections.abc import Callable

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# GoogleGenerativeAIError isn't re-exported from the public
# langchain_google_genai package - this is the only import path for it.
from langchain_google_genai._common import GoogleGenerativeAIError

# Google's free tier meters embed_content by item, not by HTTP call -
# confirmed via a real 429 (limit: 100, quotaId ending
# "PerMinutePerUserPerProjectPerModel-FreeTier") plus the AI Studio usage
# dashboard, which showed RPM peaking at the 100 limit while TPM stayed
# around 1/3 of its own 30K limit for the same requests. A single
# document of a few hundred chunks, sent via LangChain's default
# batch_size=100 with no pacing, blows through this in two back-to-back
# calls. This wrapper paces batches under the ceiling and retries with a
# fixed backoff as a safety net.
_BATCH_SIZE = 90
_DELAY_BETWEEN_BATCHES_SECONDS = 65
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 70


class _RateLimitedEmbeddings(Embeddings):
    """Wraps an Embeddings implementation so embed_documents() paces
    itself under the free-tier per-minute quota.

    embed_query() (a single call at question-time) passes straight
    through - it's never the bottleneck.
    """

    def __init__(self, inner: Embeddings):
        self._inner = inner
        # Public on purpose - the UI layer sets this right before a call
        # it wants progress reported for, and clears it after. Not passed
        # via the constructor because this instance is cached/reused
        # (st.cache_resource) across many later calls that shouldn't
        # report to a UI element from a previous, no-longer-valid rerun.
        self.on_batch: Callable[[int, int], None] | None = None

    def embed_query(self, text: str) -> list[float]:
        return self._inner.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        total_batches = math.ceil(len(texts) / _BATCH_SIZE)
        for batch_index, start in enumerate(range(0, len(texts), _BATCH_SIZE), start=1):
            batch = texts[start : start + _BATCH_SIZE]
            if self.on_batch:
                self.on_batch(batch_index, total_batches)
            if start > 0:
                time.sleep(_DELAY_BETWEEN_BATCHES_SECONDS)
            results.extend(self._embed_batch_with_retry(batch))
        return results

    def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        for _ in range(_MAX_RETRIES - 1):
            try:
                return self._inner.embed_documents(batch)
            except GoogleGenerativeAIError:
                time.sleep(_RETRY_BACKOFF_SECONDS)
        return self._inner.embed_documents(batch)  # final attempt - let it raise


EMBEDDING_REGISTRY: dict[str, Callable[[], Embeddings]] = {
    "gemini-embedding-001": lambda: _RateLimitedEmbeddings(
        GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
    ),
}
