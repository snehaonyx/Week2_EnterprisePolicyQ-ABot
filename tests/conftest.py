from pathlib import Path

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding, Embeddings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf_a_path() -> Path:
    return FIXTURES_DIR / "sample_policy_a.pdf"


@pytest.fixture
def sample_pdf_b_path() -> Path:
    return FIXTURES_DIR / "sample_policy_b.pdf"


@pytest.fixture
def fake_embeddings() -> Embeddings:
    """A real Embeddings implementation with no network call - keeps
    ingestion/vectorstore tests offline and fast."""
    return DeterministicFakeEmbedding(size=16)
