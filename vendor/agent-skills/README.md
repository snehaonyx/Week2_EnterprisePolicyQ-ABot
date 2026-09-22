# agent-skills

A personal library of [Agent Skills](https://www.anthropic.com/news/skills) — `SKILL.md` packages (name + description frontmatter, progressive disclosure of any bundled files) that agentic coding tools discover and load on demand. Kept in one repo so every project on this machine reuses the same skills instead of copy-pasting them.

## Skills

| Skill | Trigger | What it does |
|---|---|---|
| [docx](skills/docx) | creating/editing `.docx`/`.dotx` files | Word document and template generation, editing, analysis |
| [domain-modeling](skills/domain-modeling) | discussing terminology, `CONTEXT.md`, ADRs | Build and sharpen a project's domain model as you design |
| [drawio](skills/drawio) | a diagram someone else will keep editing | Editable `.drawio` diagrams, exported via the draw.io CLI |
| [grill-with-docs](skills/grill-with-docs) | sharpening a plan/design | Interview-style grilling that also produces ADRs/glossary |
| [grilling](skills/grilling) | stress-testing a plan/decision | Relentless round-by-round interview until nothing's left assumed |
| [handoff](skills/handoff) | `/handoff` | Compact the conversation into a handoff doc for the next agent |
| [improve-codebase-architecture](skills/improve-codebase-architecture) | looking for architecture improvements | Scans for deepening opportunities, reports them, then grills through the pick |
| [local-diagrams](skills/local-diagrams) | "flowchart", "sequence diagram", "UML", "architecture diagram" | Offline flowcharts/UML/dependency graphs via Mermaid, PlantUML, Graphviz |
| [writing-for-agents](skills/writing-for-agents) | writing/editing skills, `AGENTS.md`, `CLAUDE.md` | Reference for writing any document an agent consumes |
| [ponytail](skills/ponytail) | `/ponytail`, "be lazy" | Forces the simplest solution that actually works |
| [ponytail-review](skills/ponytail-review) | `/ponytail-review` | Diff review focused on over-engineering |
| [ponytail-audit](skills/ponytail-audit) | `/ponytail-audit` | Whole-repo over-engineering audit |
| [ponytail-debt](skills/ponytail-debt) | `/ponytail-debt` | Harvest `ponytail:` shortcut comments into a ledger |
| [ponytail-gain](skills/ponytail-gain) | `/ponytail-gain` | Ponytail's measured-impact scoreboard |
| [ponytail-help](skills/ponytail-help) | `/ponytail-help` | Quick-reference card for the ponytail family |

## Using this repo in a project

Every skill is a self-contained folder under `skills/<name>/` with a `SKILL.md` plus any files it references — the same layout Claude Code, Codex, and OpenCode each scan for. Nothing tool-specific lives in the skill content itself, so the repo needs no per-tool copies.

**Recommended: link once, use everywhere.** Clone this repo somewhere permanent, then run the installer for your OS:

```bash
# macOS/Linux
./install.sh
```

```powershell
# Windows
./install.ps1
```

Both link every skill folder into `~/.claude/skills/` (Claude Code's user-level skills directory), so any project on the machine picks them up automatically with no per-project setup, and edits here apply immediately everywhere. Re-running either script is safe — existing links are skipped.

If you use another tool with its own global skills directory (Codex, OpenCode, etc.), check that tool's docs for the path and symlink `skills/<name>` into it the same way.

If you'd rather pin a specific version per project instead of a machine-wide link, add this repo as a git submodule under that project's skills directory instead of running the installer.

### External tooling

Most skills need nothing beyond the tool itself. Two need local tools installed once per machine, deliberately kept fully offline (no public API, no Docker, no data leaving the machine) for use in locked-down environments:

- `local-diagrams`: Node.js/npm (for `@mermaid-js/mermaid-cli`), a JRE + [`plantuml.jar`](https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar), and Graphviz (`winget install -e --id Graphviz.Graphviz` / `apt`/`brew install graphviz`). Reuses an already-installed Chrome/Edge for Mermaid rendering instead of downloading a bundled Chromium.
- `drawio`: the draw.io desktop app (`winget install -e --id JGraph.Draw` / [diagrams.net downloads](https://www.drawio.com/) elsewhere) for its CLI export.

## Attribution

Not everything under `skills/` is original work, and the repo's own [LICENSE](LICENSE) (MIT) covers original content only:

- The `ponytail*` family (`ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`) is vendored from [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) — check that repo for its license before redistributing.
- `grilling` is vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (`skills/productivity/grilling`), tracked in [skills-lock.json](skills-lock.json) with its source hash.
- `docx` ships its own [LICENSE.txt](skills/docx/LICENSE.txt) (proprietary) — read it before reuse.
- `local-diagrams` and `drawio` are original skill content, but each wraps a separately-licensed third-party tool: [Mermaid](https://github.com/mermaid-js/mermaid) (MIT), [PlantUML](https://plantuml.com/) (multi-licensed — check its terms), [Graphviz](https://graphviz.org/) (EPL 1.0), and [draw.io/diagrams.net](https://github.com/jgraph/drawio) (Apache 2.0). None of that tooling is vendored here — the skills install and call it.

Everything else in `skills/` is original.
