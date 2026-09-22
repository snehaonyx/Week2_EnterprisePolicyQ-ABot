# Enterprise OnA Bot

## Overview

This repository is scaffolded as a production-grade, agent-agnostic
project: the same architectural rules, testing mandates, and
configuration conventions apply whether the contributor is a human or
an AI coding agent (Claude, Cursor, Windsurf, Cline, Copilot, etc.).

## Architecture Reference

See [AGENTS.md](./AGENTS.md) for the canonical conventions governing
this repository: code boundaries, formatting rules, testing mandates,
12-factor configuration, and the ADR workflow. Every agent-specific
rule file (`CLAUDE.md`, `.cursorrules`, `.windsurfrules`,
`.clinerules`, `.github/copilot-instructions.md`) is a symlink to
`AGENTS.md` — edit that file only.

Architecture decisions are recorded in [docs/adr/](./docs/adr/),
starting with
[0001-record-architecture-decisions.md](./docs/adr/0001-record-architecture-decisions.md).

## Structure

- `src/core/` — business logic and domain models
- `src/api/` — API endpoints and interfaces
- `src/utils/` — shared utility functions
- `config/` — environment-agnostic configuration
- `scripts/` — operational/one-off scripts
- `skills/` — project-authored agent skills, if any
- `.claude/skills/` — Claude Code's skill-discovery path; populated by
  `make init` (not committed — see below)
- `vendor/agent-skills/` — submodule pinning a shared, reusable skill
  library
- `tests/unit/`, `tests/integration/`, `tests/fixtures/` — test suites
- `docs/adr/` — Architecture Decision Records

## Getting Started

```bash
cp .env.example .env
make init
make test
```

`make init` also runs `git submodule update --init --recursive` and links
every skill from `vendor/agent-skills` into `.claude/skills/` (junctions
on Windows, symlinks elsewhere — no admin rights required). Re-run it
after pulling a submodule update.

Run `make help` to see all available commands.
