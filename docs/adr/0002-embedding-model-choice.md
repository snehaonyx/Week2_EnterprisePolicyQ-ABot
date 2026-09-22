# 2. Use Google gemini-embedding-001 for embeddings

Date: 2026-08-22
Status: Accepted

## Context

The ingestion pipeline needs an embedding model to turn document chunks
into vectors. Options considered:

- **OpenAI** (`text-embedding-3-small`) — best-known quality, most
  tutorials assume it, but requires a funded billing account even
  though per-call cost is small.
- **Local** (`sentence-transformers` via `HuggingFaceEmbeddings`) — zero
  cost, no API key, but adds local compute/setup friction and different
  failure modes than hosted options.
- **Google** (`gemini-embedding-001` via `langchain-google-genai`) —
  hosted, free tier, API-key-only setup, LangChain-supported.

## Decision

Use Google's `gemini-embedding-001` via the `langchain-google-genai`
package's `GoogleGenerativeAIEmbeddings`.

## Consequences

No cost and no billing setup for a project this size, at the cost of
depending on Google's free-tier rate limits (currently 1,500 requests/day
on comparable free-tier models as of Aug 2026 — verify current limits
before scaling past this project).

This choice locks in an embedding space: vectors from different
embedding models are not compatible in the same similarity search.
Switching embedding models later means re-embedding and re-ingesting the
entire corpus from scratch, not a config change — treat this as a real
switching cost, not a swappable implementation detail.
