# 3. One Chroma collection per workspace

Date: 2026-08-23
Status: Accepted

## Context

The app moved from a single global corpus to named, persistent
**workspaces** the user can create, reopen, and delete. Two real designs
were considered for how a workspace's isolation is actually implemented:

- **Shared collection + metadata filter** — one Chroma collection for
  everything, every chunk tagged with a `workspace_id` field, queries
  and deletes filtered by `where={"workspace_id": ...}`.
- **One physical collection per workspace** — each workspace is its own
  Chroma collection; the human-readable name, embedding model, and
  creation time live in that collection's own `metadata`; the workspace
  list is `chromadb`'s own `list_collections()`, filtered to collections
  carrying that metadata shape.

## Decision

One physical Chroma collection per workspace. The collection's storage
name is opaque and generated (`ws-<12 hex chars>`); the display name,
embedding model, and creation timestamp are stored in the collection's
own `metadata`, never encoded into the name itself.

Workspace admin (list/create/delete) goes through the raw `chromadb`
client directly — `langchain_chroma.Chroma` exposes no accessor for the
underlying client, and these are collection-level operations, not RAG
operations. A `langchain_chroma.Chroma` wrapper is only constructed once
a specific workspace's collection is actually being used for retrieval
or ingestion.

## Consequences

True physical isolation: there is no filter clause that a future change
could forget or get wrong, and no query path can accidentally cross a
workspace boundary — the same reasoning `docs/architecture.md` §7
already applied to guaranteeing a clean reset now extends naturally to
guaranteeing a clean *delete* of exactly one workspace. Deletion reuses
the same trusted `delete_collection` primitive as before, just
parameterized per workspace instead of hardcoded to one name.

The cost: workspace admin code bypasses `langchain_chroma.Chroma`
entirely for the raw `chromadb` client, so there are now two different
ways this codebase talks to Chroma (raw client for admin, LangChain
wrapper for RAG) — a real seam to keep straight, not free. The number of
on-disk collections grows unbounded with workspaces created, with no cap
or expiry; acceptable at local, single-user scale (NFR-3), would need
revisiting if this were ever hosted or multi-tenant.

The pre-existing `policy_docs` collection (real data, no workspace
metadata) is permanently orphaned by this decision — it fails the
metadata-shape filter and simply never appears in the workspace list.
No migration was written; re-uploading into a fresh first workspace was
judged cheaper than migration code for a collection that only ever
existed because of ad hoc testing during development.
