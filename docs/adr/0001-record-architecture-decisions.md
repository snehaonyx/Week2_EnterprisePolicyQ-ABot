# 1. Record Architecture Decisions

Date: 2026-08-22
Status: Accepted

## Context

We need a lightweight, versioned method to capture architectural design
choices, so that future contributors (human or AI agent) can understand
not just what the code does, but why it was built that way.

## Decision

We will store Architecture Decision Records (ADRs) as Markdown documents
in `docs/adr/`, numbered sequentially (`NNNN-short-title.md`), each
recording Context, Decision, and Consequences.

## Consequences

Major structural and interface decisions will require an accompanying
ADR. This adds a small amount of process overhead but keeps the
rationale behind the codebase's architecture discoverable without
relying on tribal knowledge or buried commit messages.
