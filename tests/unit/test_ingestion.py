from core.ingestion import CHUNK_SIZE, load_pdf, split_documents


def test_load_pdf_returns_one_document_per_page(sample_pdf_a_path):
    docs = load_pdf(sample_pdf_a_path)

    assert len(docs) == 2
    assert [d.metadata["page"] for d in docs] == [0, 1]
    assert all(d.metadata["source"] == str(sample_pdf_a_path) for d in docs)


def test_split_documents_produces_multiple_chunks_within_size(sample_pdf_a_path):
    docs = load_pdf(sample_pdf_a_path)

    chunks = split_documents(docs)

    assert len(chunks) > len(docs)
    assert all(len(c.page_content) <= CHUNK_SIZE for c in chunks)


def test_split_documents_preserves_source_and_page_metadata(sample_pdf_a_path):
    docs = load_pdf(sample_pdf_a_path)

    chunks = split_documents(docs)

    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "page" in chunk.metadata


def test_split_documents_does_not_add_category_metadata(sample_pdf_a_path):
    """Regression test for the deliberate decision to drop `category`
    metadata (docs/requirements.md §2) - nothing in the pipeline should
    silently reintroduce it."""
    docs = load_pdf(sample_pdf_a_path)

    chunks = split_documents(docs)

    assert all("category" not in chunk.metadata for chunk in chunks)
