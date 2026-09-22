# Repository Conventions & Workflow Directives

This document is the single source of truth for how humans and AI coding
agents should work in this repository. Tool-specific rule files
(`CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `.clinerules`,
`.github/copilot-instructions.md`) are symlinks to this file — edit this
file only.

## Architecture & Code Boundaries

- `src/core/` — business logic, domain models. No framework or transport
  concerns here.
- `src/api/` — API endpoints, request/response handling, routing. Thin
  layer that delegates to `src/core/`.
- `src/utils/` — small, dependency-free helper functions shared across
  the codebase. Nothing project-specific belongs here.
- `config/` — environment-agnostic configuration files (no secrets).
- `scripts/` — one-off or operational scripts (setup, migration, data
  tooling), not part of the application runtime.
- `skills/` — project-authored agent skills (`SKILL.md` packages), if any
  are written specifically for this project.
- `.claude/skills/` — Claude Code's actual skill-discovery directory.
  Populated by `make init`, which links each skill from the
  `vendor/agent-skills` submodule in here (junctions on Windows, symlinks
  elsewhere). Not committed — see `scripts/link-skills.ps1` /
  `scripts/link-skills.sh`. Run `make init` after cloning, or after
  pulling a submodule update, to (re)populate it.
- `vendor/agent-skills/` — git submodule pinning a shared, reusable skill
  library (<https://github.com/Rohit15190/agent-skills>). Treat as
  read-only from this project; edit skills upstream and bump the
  submodule pointer to pick up changes.
- `docs/adr/` — Architecture Decision Records.
- `docs/handoff.md` — running, append-only session handoff log (newest
  entry at top, dated). When asked to prepare a handoff, append a new
  dated section here rather than writing a separate file — never
  overwrite or delete earlier entries.

## Code Formatting

- Indentation: 2 spaces by default; 4 spaces for Python, Go, and Rust
  (see `.editorconfig`, which is authoritative).
- UTF-8 encoding, LF line endings, trailing whitespace trimmed, final
  newline required on every file.
- Run the project's linter/formatter (`make lint`) before committing;
  do not hand-format around a linter's decisions.

## Testing Mandates

- All new features and bug fixes must include unit tests in
  `tests/unit/`.
- Cross-component or end-to-end behavior belongs in
  `tests/integration/`.
- Shared test data/fixtures live in `tests/fixtures/`, not inline in
  test files, when reused across more than one test.
- `make test` must pass before a change is considered complete.

## 12-Factor Configuration Rules

- Never hardcode secrets, credentials, or environment-specific values
  in source code.
- All configuration is read from environment variables. Document every
  variable a service needs in `.env.example` with a safe placeholder or
  default — never commit a real `.env`.
- Config must be strictly separated from code: the same build artifact
  should run in any environment given a different set of environment
  variables.
- Treat backing services (databases, queues, external APIs) as
  attached resources, addressable via config, swappable without a code
  change.

## ADR (Architecture Decision Record) Workflow

- Any decision with lasting architectural impact (new dependency,
  structural change, interface contract, data model shift) must be
  recorded as an ADR in `docs/adr/`.
- Use the next sequential number and the pattern
  `NNNN-short-title.md` (see `docs/adr/0001-record-architecture-decisions.md`
  for the template/precedent).
- An ADR records Context, Decision, and Consequences — not a full
  design doc. Keep it short enough to read in two minutes.

## Quality Gate

Before submitting or merging any code change:

```bash
make lint
make test
```

Both must pass. If either cannot be run in the current environment,
say so explicitly rather than claiming the gate passed.
