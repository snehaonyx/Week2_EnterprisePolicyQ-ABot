# Enterprise Policy Q&A Bot

A RAG pipeline that ingests enterprise policy documents (HR, compliance,
technical) and answers questions against them. The project's purpose is
learning how LangChain's ingestion primitives work, not just producing a
working demo — so this glossary favors precise, house definitions over
textbook ones.

## Language

**Chunk**:
A piece of a source document sized so that its embedding represents one
coherent idea, not an average of many. Chunking exists primarily so
retrieval has something precise to match a query against — a diluted,
whole-document vector loses to a smaller, on-topic one even when the
whole document is short (e.g. 20 pages). Reducing token count for a
model's context window is a secondary, incidental benefit.
_Avoid_: Document (that's the whole loaded file before splitting),
Passage, Snippet (informal synonyms — LangChain's own API calls the
output of a splitter a chunk).

**Embed (ingestion) vs. embed (query)**:
Two distinct operations that happen to share a name. Ingestion-time
embedding runs once per chunk, batched, via `Embeddings.embed_documents()`.
Query-time embedding runs once per question, via `Embeddings.embed_query()`.
Not the same call reused — some embedding models compute the two
differently under the hood, tuned for asymmetric retrieval.
_Avoid_: "Embedding a document" as a generic phrase without specifying
which of the two operations is meant.
