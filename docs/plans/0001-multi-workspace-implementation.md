# Implementation Plan — Multi-Workspace Support

*Mirrored from `~/.claude/plans/harmonic-rolling-cerf.md` into the repo
so it survives outside Claude's app-data directory (see the global
convention this established, `~/.claude/CLAUDE.md`).*

## Context

The app currently has one single, global Chroma corpus — everything
uploaded goes into one collection (`policy_docs`), and "Reset corpus"
wipes the only corpus that exists. The user wants named, persistent
**workspaces**: create one by uploading documents, come back later,
either reopen an existing workspace to keep asking questions against it
(and optionally add more documents), or start a new one. This design was
fully resolved through an explicit grilling session before this plan —
this document sequences *implementation only*, no open architecture
decisions remain except the two small UX defaults noted in §6.

Work happens on git branch `feature/workspaces`, branched from a tagged,
pushed, fully-working baseline (`v1-single-workspace-baseline` / `master`
at commit `0fe1f5a`) — that baseline is the rollback point if anything
here goes wrong; nothing about it needs preserving in this branch's work.

**Resolved design (implemented exactly this):**
1. One Chroma collection per workspace — true physical isolation.
   Workspace list = `chromadb` client's `list_collections()`, filtered to
   collections carrying the metadata shape below.
2. Workspaces are extensible — reopening one and uploading more
   documents just calls the existing `ingest_pdf_bytes` again, same as
   today's cumulative-upload behavior, now scoped to that collection.
3. Storage name is opaque and generated (`ws-<12 hex chars>`); the
   human-typed name lives in that collection's `metadata` as
   `display_name`. Never derive one from the other.
4. Chat history starts empty every time a workspace is opened/reopened —
   session_state only, not persisted; the agent has no memory of its own
   regardless.
5. Landing screen first: pick an existing workspace or create a new one;
   only then does the familiar upload/chat UI appear, scoped to that
   workspace.
6. Embedding model is locked at creation, stored as `embedding_model` in
   the collection's metadata. Reopening a workspace shows it as a
   read-only caption, not an editable dropdown; further uploads always
   use that stored model.
7. "Reset corpus" becomes "delete this workspace" — same primitive
   (delete the collection), returns to the picker afterward. Requires a
   two-click arm/confirm step (asked explicitly — this is more clearly
   destructive than the old "reset the one demo corpus" framing was, so
   no single-click precedent should carry over).
8. No migration — the existing `policy_docs` collection (real data,
   `metadata=None`) is simply abandoned, invisible to the new picker by
   construction (fails the metadata-shape filter). Re-upload into a
   fresh first workspace instead — also fixes the known duplicate-chunk
   issue in that old data for free.
9. `collection_metadata` shape: `display_name` (str), `embedding_model`
   (str), `created_at` (str, ISO 8601 UTC). A workspace must have all
   three keys present to be listed — a strict superset check, so a
   stray/malformed collection can't crash the picker on a missing field.
10. Delete lives inside an opened workspace only, not as a control on
    the picker list itself.

**Verified facts built on:**
- `chromadb.PersistentClient(path).list_collections()` returns objects
  with both `.name` and `.metadata` directly — no per-collection
  reconnect needed to read metadata back.
- `langchain_chroma.Chroma` exposes no public accessor for the
  underlying client — workspace admin (list/create/delete) goes through
  `chromadb.PersistentClient` directly; only build a `Chroma` wrapper
  (via the existing `get_vectorstore`) once a specific workspace's
  collection is being used for actual RAG operations.
- `get_or_create_collection` on an already-existing collection does not
  clobber its stored metadata when called again with `metadata=None` —
  confirmed live. This matters because `get_vectorstore()` (called every
  time a workspace is reopened for RAG use) does exactly that
  internally; reopening is safe.
- `create_workspace` must pass `embedding_function=None` explicitly to
  `get_or_create_collection` — matches what `langchain_chroma` itself
  does internally, avoids the raw client attaching its own default
  embedding function that would conflict with `get_vectorstore()`
  reopening the same collection later.
- `client.delete_collection(name)` raises `chromadb.errors.NotFoundError`
  if the name doesn't exist — a real, testable contract, not a silent
  no-op.

## Steps (all four landed on `feature/workspaces`)

1. **`src/core/workspace.py` (new) + `tests/unit/test_workspace.py` (new)**
   — self-contained: `create_workspace`/`list_workspaces`/`delete_workspace`,
   through the raw `chromadb` client, not `langchain_chroma.Chroma`.
2. **`src/api/app.py` rewrite + `tests/integration/test_app.py` rewrite**
   — picker/workspace screen gate on `st.session_state.active_workspace`;
   cache keys expanded to `(persist_dir, collection_name, model_name)`;
   two-click delete confirm.
3. **`src/core/config.py` cleanup** — removed the now-dead
   `chroma_collection_name`/`CHROMA_COLLECTION_NAME`.
4. **Documentation** — `docs/requirements.md`, `docs/architecture.md`
   updated (FR-4 retitled, new FR-0 block added, acceptance criteria
   extended), plus `docs/adr/0003-collection-per-workspace.md`.

Each step left `uv run pytest` and `uv run ruff check .` clean before
the next began. Final count: 37/37 tests passing.

## Verification performed

Real end-to-end check via `streamlit.testing.v1.AppTest`'s `.exception`
(empty `ElementList()`, confirming a clean boot) after every code
change, plus a manual pass against the real running app: create a
workspace, upload a real document, ask a question, go back, create a
second workspace, confirm the first workspace's content is not
answerable from the second, reopen the first, confirm its documents and
citations are intact and the model is shown read-only, delete it with
the confirm step, confirm it's gone from the picker.
