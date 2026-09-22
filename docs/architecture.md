# Software Architecture — Enterprise Policy Q&A Bot

Status: Accepted
Implements: `docs/requirements.md`
Decisions referenced: `CONTEXT.md`, `docs/adr/0002-embedding-model-choice.md`,
`docs/adr/0003-collection-per-workspace.md`

## 1. Architecture style

**A single Python process, no network API layer.** Streamlit is both the
UI and the application host; button/chat interactions call functions in
`src/core` directly, in-process. There is no separate backend service.

This was a deliberate choice (design tree round 2, Q7), not a default —
a network boundary earns its cost when something needs it (a second
client, independent scaling, multiple users). None of that applies to a
local, single-user demo, so introducing FastAPI + HTTP here would add a
layer with no corresponding requirement.

```
┌─────────────────────────────────────────────┐
│              Streamlit process               │
│                                               │
│  UI layer (src/api)                          │
│   - file uploader, embedding dropdown,       │
│     chat input/output, reset control         │
│         │ calls directly, in-process         │
│         ▼                                    │
│  Core (src/core)                             │
│   - ingestion pipeline                       │
│   - LangGraph agent (retrieve → generate)    │
│   - embedding model registry                 │
│         │                                    │
│         ▼                                    │
│  Chroma - one collection per workspace,      │
│  under one persist_directory                 │
└─────────────────────────────────────────────┘
         │
         ▼
  Google Gemini API (embeddings + generation)
```

Workspace admin (list/create/delete collections) goes through the raw
`chromadb` client directly, not `langchain_chroma.Chroma` (which exposes
no client accessor); the `Chroma` wrapper is only built once a specific
workspace's collection is being used for actual retrieval/ingestion —
see `docs/adr/0003-collection-per-workspace.md`.

## 2. Module mapping

Repurposing the directories from `AGENTS.md`'s original scaffold (which
assumed an HTTP API) for this architecture's actual shape:

- **`src/api`** — the Streamlit entrypoint and UI glue code. Renamed in
  spirit from "HTTP endpoints" to "the interface layer between the user
  and `src/core`" — still the right directory, different meaning.
- **`src/core`** — ingestion pipeline, the LangGraph graph definition and
  its nodes, the embedding model registry, workspace management
  (`workspace.py` — list/create/delete Chroma collections). No Streamlit
  imports here — this layer must be UI-agnostic so it stays testable
  without a browser.
- **`src/utils`** — small shared helpers (e.g. temp file handling for
  uploaded bytes → a path `PyPDFLoader` can read).

## 3. Ingestion pipeline

Unchanged from the earlier design (see the published ingestion diagram,
pending an update for §6 below):

```
uploaded PDF bytes
  → temp file on disk
  → PyPDFLoader.load()                    → list[Document], one per page
  → RecursiveCharacterTextSplitter(
      chunk_size=800, chunk_overlap=150
    ).split_documents()                    → list[Document] (chunks)
  → embedding_registry[selected].embed_documents(texts)
                                            → list[vector]
  → Chroma.add_documents(chunks)           → persisted, indexed (HNSW)
```

Runs synchronously per upload (NFR-1) — corpus sizes in scope (tens to
~100 pages) complete in low tens of seconds at most; no background job
queue is warranted.

## 4. The LangGraph agent

### State

```python
class GraphState(TypedDict):
    question: str
    documents: list[Document]
    answer: str
```

### Nodes

- **`retrieve(state)`** — calls `vectorstore.as_retriever().invoke(state["question"])`,
  returns `{"documents": [...]}`.
- **`generate(state)`** — builds a prompt from `state["documents"]` and
  `state["question"]`, with an explicit grounding instruction (FR-3.3):
  *"Answer only using the provided context. If the answer isn't in the
  context, say so explicitly — do not guess."* Calls the chat LLM,
  returns `{"answer": ...}`.

### Graph

```
START → retrieve → generate → END
```

Deliberately linear today (round 1, Q1/Q2 — no memory, no branching).
This is the intentional extension point for agentic RAG: a
`grade_documents` node and a conditional edge back to `retrieve` (retry
with a rewritten query if retrieved chunks are graded irrelevant) slot
in without restructuring what exists — the graph shape was chosen
specifically so that extension is additive.

## 5. Models

Two distinct model calls, easy to conflate:

- **Embeddings** — `GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")`.
  Used at ingestion time (`embed_documents`, batched) and at query time
  inside the retriever (`embed_query`, singular). See
  `docs/adr/0002-embedding-model-choice.md` for why this is a real
  switching cost, not a config value.
- **Generation** — `ChatGoogleGenerativeAI`, a Gemini free-tier flash
  model. Reuses the same API key and package as the embedding model —
  no second provider. **Verify the exact current free-tier model string
  before implementation** (these get renamed/deprecated — the same
  research that surfaced `gemini-embedding-001` also found
  `text-embedding-004` had already been deprecated in January 2026;
  assume the chat model list moves just as fast).

### Embedding registry

```python
EMBEDDING_REGISTRY: dict[str, Callable[[], Embeddings]] = {
    "gemini-embedding-001": lambda: GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    ),
}
```

The dropdown's options are `EMBEDDING_REGISTRY.keys()` — adding a second
model later is one dict entry (round 2, Q5), not a refactor.

## 6. State management in Streamlit (read before implementing)

Streamlit reruns the entire script top to bottom on every interaction —
every chat message, every button click. Anything expensive that isn't
deliberately cached gets rebuilt on every single rerun. This is the most
common first-time-Streamlit mistake, and it is designed around here
explicitly rather than left to be discovered the hard way:

- **`st.cache_resource`** — for expensive, shared, effectively-singleton
  objects: the embedding model client, the Chroma connection, the
  compiled LangGraph app. Constructed once, reused across reruns and
  across users (irrelevant for single-user, but it's the semantically
  correct tool). Keyed on `(persist_dir, collection_name, model_name)` —
  different workspaces are different physical collections even when
  they share an embedding model, so `model_name` alone is not a safe
  cache key once more than one workspace exists.
- **`st.session_state`** — for state specific to this browser session:
  `active_workspace` (the screen gate — `None` shows the workspace
  picker, otherwise the upload/chat UI for that workspace), the
  displayed chat message list (FR-3.5, reset on every workspace
  open/close), the currently selected embedding model (only relevant
  while creating a new workspace — locked once created), an "ingestion
  in progress" flag, and `confirm_delete` (the two-step delete arm/undo
  state, also reset on workspace open/close so it can't leak between
  workspaces).

Rule of thumb used throughout: if rebuilding it costs an API call or a
disk read, it belongs in `cache_resource`; if it's just "what has this
user done so far," it belongs in `session_state`.

## 7. Workspace deletion (FR-4.2)

Deletion must clear the actual on-disk Chroma collection backing the
workspace, not just UI state:

```python
# core/workspace.py
def delete_workspace(persist_directory: str, collection_name: str) -> None:
    chromadb.PersistentClient(path=persist_directory).delete_collection(collection_name)
```

Clearing only `session_state` while leaving the on-disk collection
intact would make the vector store and the UI disagree about what's
ingested — a stale-data bug that would surface confusingly mid-demo, and
would also defeat the point of workspace isolation (a "deleted"
workspace whose collection still exists is still queryable by anyone
who reopens it). The UI additionally requires a two-step confirm (arm,
then confirm) before calling this — deleting a named, potentially
long-lived workspace reads as more clearly destructive than the old
single-corpus "reset" ever did, so no single-click precedent carries
over.

## 8. Technology stack

| Layer | Choice | Rationale (round/Q) |
|---|---|---|
| UI | Streamlit | Round 2, Q6 — native upload + chat + dropdown widgets |
| Orchestration | LangChain + LangGraph | Round 1, Q1 — assignment brief's own title, and forward-compatible with agentic RAG |
| Loader | `PyPDFLoader` | Ingestion round, Q6 — naive first, deliberately |
| Splitter | `RecursiveCharacterTextSplitter` (800/150) | Ingestion round, Q7 — naive first, deliberately |
| Embeddings | `gemini-embedding-001` | Ingestion round Q4 — free tier; ADR 0002 |
| Generation LLM | Gemini flash-tier via `ChatGoogleGenerativeAI` | This session — reuses embedding provider/key |
| Vector store | Chroma, local, persisted, one collection per workspace | Ingestion round Q5 — zero infra for local use; ADR 0003 — physical workspace isolation |

## 9. Deployment / running locally

No deployment target — local only (requirements §2, out of scope). Run
via `streamlit run src/api/app.py` (or equivalent Makefile target once
implemented), with a Gemini API key available as an environment variable
per `AGENTS.md`'s 12-factor config rule (`.env`, never hardcoded).

## 10. Known limitations (by design, not oversight)

Each of these is a deferred decision from `docs/requirements.md` §2, not
an unconsidered gap:

- No conversational memory — every question is independent.
- No agentic retrieval loop — the graph doesn't retry or route yet.
- No document category/topic metadata — dropped, see round 3 Q9.
- No multi-user support, auth, or deployment story.
- PDF-only ingestion.
- Workspace deletion is only reachable from inside an opened workspace,
  not as a control on the picker list itself — a deliberate first-cut
  scoping choice (workspaces design, point 10), not an oversight.
- No workspace name uniqueness check — two workspaces may share a
  display name; only the opaque, always-unique collection name
  distinguishes them internally.
- No migration path from the pre-workspace single global corpus — the
  original `policy_docs` collection is permanently orphaned by design
  (workspaces design, point 8).

## Pending

The published ingestion architecture diagram predates the decision to
drop `category` metadata (round 3, Q9) — it still shows `category` in
several places. Needs an update pass to match this document.
