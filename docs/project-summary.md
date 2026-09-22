# Project Summary — Enterprise Policy Q&A Bot

*Written as portable context for discussing a follow-on project. This
document is self-contained — it doesn't assume the reader has access to
the repository, so it restates content rather than just linking to it.*

## What this is

A course assignment: build a RAG (Retrieval-Augmented Generation)
Q&A system over real enterprise policy documents (HR handbooks,
compliance codes of conduct), then stress-test it with 15 questions
across four categories — straightforward single-document questions,
ambiguous queries, questions spanning multiple documents, and questions
the knowledge base genuinely can't answer — and document where
retrieval succeeds, fails, and why.

The project deliberately prioritized *understanding* over speed: the
build process was collaborative and Socratic throughout (structured
design "grilling" sessions before any code, then module-by-module
implementation with explanation at each step), because the point was to
learn how RAG and LangChain actually work internally, not just produce
a working demo.

## Final architecture

**A single Python process, no separate backend API.** Streamlit is both
the UI and the application host. This was a deliberate choice (not a
default) — a network boundary between UI and logic earns its cost when
something needs it (a second client, independent scaling, multiple
users); none of that applied to a local, single-user tool, so
introducing FastAPI + HTTP would have added a layer nothing required.

```
Streamlit process
  UI layer (src/api) — workspace picker, file uploader, chat
    │ calls directly, in-process
    ▼
  Core (src/core) — ingestion pipeline, LangGraph agent,
                     embedding registry, workspace management
    │
    ▼
  Chroma — one vector-store collection per workspace, on disk
    │
    ▼
  Google Gemini API (embeddings + chat generation)
```

### Ingestion pipeline

```
uploaded PDF bytes
  → temp file on disk
  → PyPDFLoader.load()                       → one Document per page
  → RecursiveCharacterTextSplitter
      (chunk_size=800, chunk_overlap=150)     → chunks
  → rate-limited Gemini embeddings            → one 3072-dim vector/chunk
  → Chroma.add_documents()                    → persisted, HNSW-indexed
```

**Loader and splitter were deliberately the naive choice, not the
"correct" one.** `PyPDFLoader` (plain text extraction, tables collapse
into unstructured text) was chosen over `PDFPlumberLoader` (table-aware)
specifically so the failure mode would be visible and understood, not
avoided. Same logic for `RecursiveCharacterTextSplitter` with fixed
size/overlap over a structure-aware splitter. This was an explicit
pedagogical choice: see the naive failure before reaching for
sophistication.

### The RAG agent — LangGraph, not a plain LangChain chain

A 2-node graph: `retrieve` (embeds the question, does a similarity
search) → `generate` (builds a grounding-instructed prompt from the
retrieved chunks, calls the chat model). No memory, no branching, no
retry logic — deliberately linear today.

**Why LangGraph over a simpler chain when the logic itself doesn't need
graph features yet:** the original assignment brief was literally titled
with LangGraph in it, strongly signaling the course wants LangGraph
exposure specifically. More importantly, the *next* phase of coursework
is expected to require **agentic RAG** — retrieval that makes decisions
(grade retrieved chunks, rewrite the query and retry if they're bad,
route between multiple sources). That's structurally a graph problem
(cycles + conditional edges), not something a linear chain can express
without dropping out of the framework's own abstractions. The 2-node
graph today costs about 15 extra lines over a chain, and is the exact
skeleton a `grade_documents` node and a conditional retry edge extend
later — additive, not a rewrite. Building the chain now and migrating
to a graph under later deadline pressure was judged worse than paying
the small cost now, with room to actually understand the model.

The generation prompt includes an explicit grounding instruction:
*"Answer only using the provided context. If the answer isn't in the
context, say so explicitly — do not guess."* This exists specifically so
the "questions the knowledge base can't answer" stress-test category
produces a real "not found" response instead of a hallucination.

### Vector similarity — what "relevant" actually means here

Embeddings are 3072-dimensional vectors from `gemini-embedding-001`.
Retrieval uses cosine similarity, `k=4` (Chroma's default), across the
*entire* workspace regardless of which document a chunk came from.

This was directly investigated with real data during the project: two
documents were ingested into one workspace (a 96-page HR handbook and
an 11-page compliance code of conduct). Questions about HR topics (sick
leave, etc.) exclusively retrieved chunks from the HR handbook — not
because of any recency bias or bug, but because the compliance
document's *best* matches for those queries scored meaningfully worse
(cosine distance ~0.73–0.80) than the handbook's *worst* match in the
top 8 (~0.55–0.66). The retrieval was behaving correctly: it doesn't
force representation from a document that has nothing relevant to say
on a topic. This is a genuinely useful thing to understand before
picking cross-document stress-test questions — a real cross-document
question needs a topic both documents actually cover, not just two
documents that both happen to be uploaded.

### Multi-workspace support (the most recent major addition)

The app evolved from "one single global corpus" to named, persistent
**workspaces** — each one an isolated corpus you can create, reopen
later (preserving its documents), add more documents to, or delete.

**Design decision: one physical Chroma collection per workspace**, not
one shared collection with a `workspace_id` metadata filter. The
alternative (shared collection + filter) was seriously considered and
rejected — physical separation means no filter clause can ever be
forgotten or written wrong, which is a much stronger isolation guarantee
than "remember to filter correctly on every query and delete." The
collection's *storage* name is an opaque generated ID; the human-typed
display name, the embedding model it was created with, and its creation
timestamp live in the collection's own metadata — Chroma's
`list_collections()` then serves as a free workspace registry, no
separate database needed. Reopening a workspace shows its embedding
model as read-only (not editable) — a real constraint, not a UI
nicety: vectors from different embedding models live in incompatible
spaces, so letting someone add documents to an existing workspace with
a different model would silently corrupt retrieval.

Deleting a workspace requires a two-click arm/confirm step — deliberately
more friction than the earlier single-corpus "reset" button had, because
deleting a named, potentially-reused workspace reads as more clearly
destructive than resetting "the one demo corpus" ever did.

## Key technical decisions and why (condensed)

| Decision | Choice | Why |
|---|---|---|
| Orchestration | LangChain + LangGraph | Assignment brief's own title; forward-compatible with agentic RAG |
| PDF loader | `PyPDFLoader` | Naive first, deliberately — see real failure modes |
| Splitter | `RecursiveCharacterTextSplitter`, 800/150 | Naive first, deliberately |
| Embeddings | `gemini-embedding-001` | Free tier; see ADR on switching cost below |
| Chat model | Gemini flash-tier | Same provider/key as embeddings, no second API |
| Vector store | Chroma, local, one collection per workspace | Zero infra for local use; true workspace isolation |
| UI | Streamlit | Native chat/upload/dropdown widgets, no separate frontend needed |
| Backend | None — Streamlit calls core logic in-process | No requirement ever demanded a network boundary |

**Embedding model lock-in (a genuine gotcha, worth an ADR):** vectors
from different embedding models are not comparable. Switching embedding
models isn't a config change — it requires re-embedding and
re-ingesting the entire corpus from scratch. This is why the embedding
model is chosen once per workspace and then locked.

## Real bugs found — none of them caught by mocked tests

These only surfaced by actually running against the real Gemini API and
the real Streamlit rerun model, not from unit tests with fakes. Worth
carrying forward as lessons for any future LLM-app work:

1. **`AIMessage.content` is not always a plain string.** Gemini's real
   API returns structured content blocks (`[{'type': 'text', 'text':
   ..., 'extras': {...}}]`), not a bare string like most mocked chat
   models return. Fixed by using `.text` (a real `str` subclass that
   normalizes this) instead of `.content`.
2. **`streamlit run` doesn't see pytest's `pythonpath` config.** A
   `pyproject.toml` `pythonpath = ["src"]` entry only applies to pytest
   — running the app directly threw `ModuleNotFoundError`. Fixed with an
   explicit `sys.path` insertion at the top of the entrypoint script.
3. **Free-tier embedding rate limits are metered per item, not per HTTP
   call.** A 96-page document producing ~400 chunks blew through
   Google's 100-requests/minute quota almost immediately, even though
   LangChain batches up to 100 texts into one logical call — confirmed
   via a real 429 error and the provider's own usage dashboard (RPM
   graph pegged at the limit; token usage nowhere near its own limit,
   proving requests, not payload size, were the bottleneck). Fixed with
   a wrapper that paces batches under the ceiling and retries with
   backoff.
4. **Streamlit's file uploader keeps returning the same file across
   unrelated reruns.** Since Streamlit reruns the whole script on every
   interaction (a chat message, any button click), a naive
   "if uploaded_files: ingest them" check would silently re-ingest the
   same file on every subsequent interaction. Fixed by tracking
   already-ingested file IDs in session state, with the upload widget's
   own `key` incremented on reset/workspace-switch so it visibly clears.
5. **`st.cache_resource` is a global, process-wide cache keyed only on
   the decorated function's arguments** — not on anything read from
   inside the function body. A vector store factory that read
   `persist_directory` from an environment variable internally, while
   only caching on `model_name`, meant switching contexts (or, in
   testing, switching test cases) could silently reuse a stale cached
   vector store pointing at the wrong location. Fixed by making every
   relevant parameter (`persist_dir`, `collection_name`, `model_name`)
   part of the explicit cache key.

## What's tested

37 tests (unit + integration), all passing. Integration tests use
Streamlit's own `AppTest` framework to run the real app script headlessly
— confirmed to execute in-process (so mocking works correctly) rather
than in an isolated subprocess. Key coverage: cumulative multi-document
ingestion, citation correctness, the rerun/duplicate-ingestion fix, and
(for the workspace feature) a dedicated test proving physical isolation
— a question asked in an empty second workspace retrieves zero
documents even though a first workspace has real, relevant content,
proving nothing leaks across the collection boundary.

## What's explicitly deferred (not oversights — considered and rejected)

- **Conversational memory.** Every question is answered independently;
  the agent has no memory of prior turns. Chat history is shown in the
  UI for readability within a session but isn't fed back into the
  agent, and doesn't persist across closing/reopening a workspace.
- **Agentic retrieval loops** (query rewriting, relevance grading and
  retry, multi-source routing). The graph is linear by design — this is
  the flagged extension point for when it's actually needed.
- **Document category/topic metadata.** Tried, then explicitly dropped
  — it was scaffolding for a fixed, known 2-document corpus and doesn't
  generalize to arbitrary uploads.
- **Multi-user support, authentication, hosted deployment.** Local,
  single-user tool by design.
- **Non-PDF ingestion.** The loader is PDF-specific.
- **No workspace name uniqueness enforcement**, and **workspace deletion
  is only reachable from inside an opened workspace**, not from the
  picker list — both simplest-first-cut choices, not fundamental limits.

## Current state / what's NOT done yet

The infrastructure is complete and verified against the real API, but
**the assignment's actual deliverable — ingesting real documents, asking
the 15 stress-test questions, and writing up where retrieval succeeds,
fails, and why — has not yet been produced.** Everything above is the
tool built to do that; the analysis itself is still open work.

## How this project was worked on (useful context for a next session)

- Design decisions went through explicit structured interview rounds
  (a design tree walked frontier-by-frontier: batches of independent
  questions, each with a recommended answer and reasoning, resolved
  before moving to dependent questions) before any implementation began
  — twice: once for the core ingestion/agent design, once for the
  multi-workspace feature.
- Implementation proceeded module by module, each one explained, tested,
  and verified (including against the real live API where relevant) before
  moving to the next — not large unexplained code dumps.
- Library API assumptions were repeatedly verified against what was
  actually installed (introspecting the real installed package) rather
  than trusted from training-data memory, because the installed versions
  (LangChain 1.x, LangGraph 1.x) are meaningfully newer than what most
  tutorials assume — guessing wrong here cost real time more than once
  early on, verifying first did not.
- The collaborator (a human learning RAG/LangChain via a course) has
  been explicit throughout: wants to understand the *why*, not just
  receive finished code.

## Natural extension points for a follow-on project

Directly suggested by the deferred-items list above, roughly in order of
how contained each one is:

1. **Agentic retrieval** — add a `grade_documents` node and a conditional
   edge back to `retrieve` (retry with a rewritten query if retrieved
   chunks are graded irrelevant). The graph shape already exists for
   this; it's additive, not a redesign.
2. **A second embedding model in the registry** — the registry and the
   per-workspace embedding-model lock were both built assuming this was
   coming; adding one is meant to be a single dict entry.
3. **Conversational memory** — LangGraph supports checkpointing for
   exactly this; deliberately not wired up yet.
4. **Cross-workspace search / comparison** — currently workspaces are
   strictly isolated by design; a "search across all my workspaces"
   feature would be a genuinely new capability, not a natural extension
   of the current isolation model.
5. **Non-PDF ingestion** (docx, plain text, HTML) — the loader layer is
   the only place this touches.
6. **Deployment / multi-user** — everything from auth to a hosted vector
   store would be new territory; today's architecture assumes local and
   single-user throughout (session state, no request isolation).
