---
name: local-diagrams
description: Draw flowcharts, sequence diagrams, architecture diagrams, UML, and dependency graphs to present engineering workflows or problems to stakeholders. Renders fully offline through local CLI tools (Mermaid, PlantUML, Graphviz) — no public API, no server, no container, diagram text never leaves the machine. Use when the user asks to draw, diagram, chart, or visualize a workflow, process, architecture, class structure, or dependency graph, or says "flowchart", "sequence diagram", "UML diagram", "architecture diagram", or "diagram this".
---

# Local Diagrams

Pick the syntax by what's being drawn, write the diagram source as a file, then render it with `scripts/render.ps1` (Windows) or `scripts/render.sh` (macOS/Linux). Everything runs locally — no network call at render time.

## Choosing a renderer

| Use for | Write this syntax | File extension |
|---|---|---|
| Flowcharts, sequence/state diagrams, Gantt charts, simple ER diagrams | [Mermaid](https://mermaid.js.org/) | `.mmd` |
| UML (class/component/deployment/activity), C4 architecture diagrams | [PlantUML](https://plantuml.com/) | `.puml` |
| Dependency/network graphs, org charts, anything needing precise node-edge layout | [Graphviz DOT](https://graphviz.org/doc/info/lang.html) | `.dot` or `.gv` |

When more than one would work, prefer Mermaid — it's the least verbose to write and read back.

## Rendering

```powershell
./scripts/render.ps1 -InputFile diagram.mmd -OutputFile diagram.svg
```

```bash
./scripts/render.sh diagram.mmd diagram.svg
```

Output format (svg/png/pdf) is inferred from the output file's extension. SVG is the default choice — it stays sharp at any size and is the easiest to embed.

## Examples

**Mermaid** (`diagram.mmd`):
```
flowchart TD
    A[Request received] --> B{Valid?}
    B -->|yes| C[Process]
    B -->|no| D[Reject]
```

**PlantUML** (`diagram.puml`):
```
@startuml
class Order {
  +id: string
  +submit()
}
Order --> LineItem
@enduml
```

**Graphviz** (`diagram.dot`):
```
digraph deps {
  ServiceA -> ServiceB -> Database
  ServiceA -> Cache
}
```

## Requirements

- Mermaid: `@mermaid-js/mermaid-cli` (`mmdc`) via npm, plus a Chromium-based browser already installed (Chrome or Edge — the render script finds one automatically; override with `LOCAL_DIAGRAMS_CHROME_PATH` if needed). No bundled-Chromium download is required or performed.
- PlantUML: a JRE, plus `plantuml.jar` at `%LOCALAPPDATA%\plantuml\plantuml.jar` (Windows) / `~/.local/share/plantuml/plantuml.jar` (macOS/Linux), or point `PLANTUML_JAR` at another location.
- Graphviz: `dot` on PATH.

## Presenting to management

Once rendered, hand the SVG/PNG to the `docx` skill to embed it in a Word report, or drop it straight into a chat/artifact response. Prefer PlantUML's C4 support or a Mermaid flowchart for anything that needs to read as "here's the problem" at a glance — keep it to one diagram per point being made, not one diagram trying to show everything.
