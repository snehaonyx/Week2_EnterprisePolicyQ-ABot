from langchain_core.documents import Document

from core.vectorstore import get_vectorstore, reset_collection


def test_get_vectorstore_stores_and_retrieves(tmp_path, fake_embeddings):
    vectorstore = get_vectorstore(str(tmp_path), "test_collection", fake_embeddings)
    vectorstore.add_documents([Document(page_content="hello world", metadata={"source": "a.pdf"})])

    results = vectorstore.similarity_search("hello", k=1)

    assert len(results) == 1
    assert results[0].metadata["source"] == "a.pdf"


def test_reset_collection_clears_existing_data(tmp_path, fake_embeddings):
    persist_dir = str(tmp_path)
    vectorstore = get_vectorstore(persist_dir, "test_collection", fake_embeddings)
    vectorstore.add_documents([Document(page_content="hello world", metadata={"source": "a.pdf"})])

    fresh = reset_collection(persist_dir, "test_collection", fake_embeddings)

    assert fresh.similarity_search("hello", k=5) == []
