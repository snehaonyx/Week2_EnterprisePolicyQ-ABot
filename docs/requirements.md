# Software Requirements — Enterprise Policy Q&A Bot

Status: Accepted
Last resolved: 2026-08-23, via grilling session (see `CONTEXT.md`, `docs/adr/`)

## 1. Purpose

A local, single-user application that lets a user upload enterprise
policy documents (PDF), ingest them into a searchable vector index, and
ask questions answered by a RAG agent grounded in those documents. Its
purpose is to serve the course assignment's actual deliverable: ingest
real documents, then stress-test retrieval with 15 questions and
document where it succeeds, fails, and why.

## 2. Scope

### In scope

- Create named **workspaces** — each an isolated corpus, physically
  separate from every other workspace (see `docs/adr/0003-collection-per-workspace.md`).
- Pick an existing workspace or create a new one from a landing screen;
  reopening a workspace preserves its documents.
- Upload one or more PDF documents through the UI, into the active
  workspace.
- Select an embedding model from a dropdown when creating a workspace
  (one option today, designed for more later) — locked for that
  workspace's lifetime once created.
- Ingest uploaded documents: load → chunk → embed → store, cumulatively
  within the active workspace.
- Ask questions through a chat interface; each question answered
  independently (no conversational memory).
- Each answer cites its source document(s) and page number(s).
- Delete a workspace (with a confirm step) to permanently remove it and
  start fresh.

### Out of scope (explicitly deferred, not silently omitted)

- **Multi-user support, authentication, deployment** — this is a local,
  single-user tool (see design tree round 2, Q3).
- **Conversational memory** across chat turns (round 2, Q2). Each
  question is answered independently of prior turns; the UI still shows
  chat history for readability within a session, but the agent does not
  use it — and that displayed history is not persisted either: reopening
  a workspace always starts with an empty chat, even though its
  documents are still there (workspaces design, Q4).
- **Agentic retrieval loops** (query rewriting, relevance grading and
  retry, multi-source routing). The `generate`/`retrieve` graph is
  deliberately a straight line today. This is the intended extension
  point for when later coursework requires agentic RAG — see
  `docs/architecture.md` §5.
- **Document category/topic metadata.** Considered and dropped (round
  3, Q9) — it was scaffolding for a fixed, known 2-document corpus and
  doesn't generalize to arbitrary uploads. `source` (filename) + `page`
  remain as citation metadata.
- **Non-PDF uploads.** The loader (`PyPDFLoader`) is PDF-specific by
  design; other formats are a future extension, not a current
  requirement.

## 3. Actors

- **User** — the only actor. Creates and opens workspaces, uploads
  documents, selects the embedding model per workspace, asks questions,
  deletes workspaces. No distinction between "admin" and "end user" —
  out of scope per §2.

## 4. Functional Requirements

### FR-0 — Workspaces

- FR-0.1: On load, the user sees a landing screen listing existing
  workspaces (if any) and a control to create a new one.
- FR-0.2: Creating a workspace requires a name and an embedding model
  (from the FR-2 registry); creation opens that workspace immediately.
- FR-0.3: Opening an existing workspace restores its documents; the
  embedding model it was created with is shown but not editable (FR-2.3
  already required this — a workspace makes it a concrete constraint,
  not just a documented one).
- FR-0.4: A workspace is physically isolated from every other workspace
  — a question asked in one workspace can never be answered using
  another workspace's documents.
- FR-0.5: A workspace can be deleted from within itself, with a
  two-step confirm; deletion returns the user to the landing screen.

### FR-1 — Document upload & ingestion

- FR-1.1: User can upload one or more PDF files via the UI, into the
  active workspace.
- FR-1.2: Each uploaded file is loaded (one `Document` per page), split
  into chunks (800 chars, 150 overlap), embedded, and added to the
  active workspace's vector store.
- FR-1.3: Uploads are cumulative — a second upload adds to the active
  workspace's corpus rather than replacing it (required for
  cross-document questions; see acceptance criteria §7), and this
  applies across sessions too — reopening a workspace and uploading
  more documents still adds to what's already there (FR-0.3).
- FR-1.4: Ingestion runs synchronously; the UI shows progress/completion
  for the current upload.
- FR-1.5: A workspace's corpus persists across app restarts (on-disk
  Chroma collection, one per workspace), so a demo doesn't require
  re-uploading every session.

### FR-2 — Embedding model selection

- FR-2.1: A dropdown lists available embedding models, sourced from a
  registry (not hardcoded to the UI) — currently one entry
  (`gemini-embedding-001`).
- FR-2.2: Adding a second embedding model in the future is a registry
  entry, not a refactor.
- FR-2.3: (Documented constraint, not a UI requirement) — because
  embedding spaces are not comparable across models, changing the
  selected embedding model after documents are already ingested
  requires re-ingesting the corpus. See `docs/adr/0002-embedding-model-choice.md`.

### FR-3 — Chat / question answering

- FR-3.1: User asks a question via a chat input.
- FR-3.2: The system retrieves relevant chunks from the vector store and
  generates an answer grounded in them, via a 2-node LangGraph graph
  (`retrieve` → `generate`).
- FR-3.3: If the retrieved context does not contain the answer, the
  system says so explicitly rather than guessing — required for the
  assignment's "documents the knowledge base can't answer" stress-test
  category to be meaningful.
- FR-3.4: Each answer displays its source(s): filename and page
  number(s) of the chunks used.
- FR-3.5: Chat history is displayed in the UI for readability within a
  session, independent of FR-3.2's statelessness (UI concern, not agent
  memory — see §2 deferred items). It does not persist across opening
  and reopening a workspace (§2, FR-0.3).

### FR-4 — Workspace deletion

- FR-4.1: User can delete the active workspace via a UI control,
  requiring a two-step confirm (arm, then confirm) before anything is
  removed.
- FR-4.2: Deletion removes the on-disk vector store collection backing
  that workspace, not just UI-visible state — a deletion that leaves
  stale vectors queryable would silently corrupt later results, and
  would defeat the point of workspace isolation (FR-0.4).

## 5. Non-Functional Requirements

- **NFR-1 (Performance)**: Ingestion of a single document (up to ~100
  pages) should complete within a few seconds to low tens of seconds,
  consistent with local, small-corpus use — no requirement for
  background/async processing.
- **NFR-2 (Cost)**: Must run within free-tier limits of the chosen
  Google Gemini APIs (embedding + generation) for a corpus of this size.
- **NFR-3 (Portability)**: Must run on a single local machine with no
  external infrastructure beyond an internet connection and a Gemini API
  key — no database server, no container orchestration.
- **NFR-4 (Traceability)**: Every generated answer must be traceable to
  the specific source chunk(s) it drew from (supports FR-3.4 and the
  assignment's documentation requirement).

## 6. Assumptions & Constraints

- The user has (or can obtain) a Google AI Studio API key with access to
  the free tier.
- Documents are real, publicly available PDFs (policy handbooks, codes
  of conduct) — not confidential material.
- Single browser session, single machine — no concurrency concerns.

## 7. Acceptance Criteria

Tied directly to the assignment's actual deliverable:

- [ ] At least 2 real documents can be uploaded and ingested through the
      UI, cumulatively, into one workspace, without restarting the app.
- [ ] 15 stress-test questions can be asked through the chat UI,
      covering: straightforward single-document questions, ambiguous
      queries, questions spanning both uploaded documents, and questions
      the corpus cannot answer.
- [ ] Each answer's source citations are visible and correct.
- [ ] Unanswerable questions produce an explicit "not found in the
      documents" response, not a hallucinated answer.
- [ ] A second workspace, created separately, cannot answer questions
      using the first workspace's documents (FR-0.4).
- [ ] Closing and reopening a workspace preserves its documents and
      citations; its embedding model is shown but not editable; its chat
      history is empty again (FR-0.3, FR-3.5).
- [ ] Deleting a workspace requires the two-step confirm, and afterward
      produces a genuinely empty result — verifiable by creating a new
      workspace and confirming the deleted one's documents are
      unreachable — not stale answers from before the deletion.

## 8. Glossary

Domain vocabulary (chunk, embed vs. embed_query, etc.) is defined in
`CONTEXT.md`, not duplicated here.
