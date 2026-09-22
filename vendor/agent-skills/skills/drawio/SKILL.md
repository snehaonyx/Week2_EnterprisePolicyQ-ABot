---
name: drawio
description: Create an editable diagram (.drawio file) that a non-technical stakeholder can open and tweak by hand afterward — architecture diagrams, process maps, org charts meant to outlive the conversation. Use when the user wants a diagram someone else will keep editing, or mentions "draw.io", "drawio", "diagrams.net", or "editable diagram". For a diagram that's just being rendered once and shown, prefer the `local-diagrams` skill instead — it's faster to author.
---

# draw.io

Author diagrams as `.drawio` files (mxGraph XML), then export to an image for sharing. Unlike `local-diagrams`, the source file stays fully editable afterward in the free draw.io desktop app or web editor — use this when the deliverable is something management or another team will open and modify themselves, not just view.

## Authoring

Copy [`TEMPLATE.drawio`](TEMPLATE.drawio) and edit it: each box is an `mxCell` with `vertex="1"`, each arrow is an `mxCell` with `edge="1"` and `source`/`target` pointing at box IDs. Geometry (`x`, `y`, `width`, `height`) is in pixels on an 850×1100 page — lay boxes out left-to-right or top-to-bottom in increments of ~140px to avoid overlap.

Common `style` values:
- Box: `rounded=1;whiteSpace=wrap;html=1;`
- Decision diamond: `rhombus;whiteSpace=wrap;html=1;`
- Arrow: `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;`

## Exporting

```
drawio --export --format svg --embed-diagram -o out.svg in.drawio
```

`--embed-diagram` keeps the full diagram XML embedded in the exported file, so opening `out.svg` (or a PNG/PDF exported the same way) back in draw.io recovers the editable source — don't drop this flag for anything meant to stay editable downstream. Swap `--format` for `png` or `pdf` as needed.

If `drawio` isn't on PATH, check `%LOCALAPPDATA%\Programs\draw.io\draw.io.exe` (Windows, installed via `winget install -e --id JGraph.Draw`), `/Applications/draw.io.app/Contents/MacOS/draw.io` (macOS), or `drawio`/`draw.io` on PATH after an apt/flatpak install (Linux).

## Presenting to management

Export to SVG or PNG and hand it to the `docx` skill for a Word report, or share the `.drawio` source directly if the recipient has (or can get) the free draw.io app and will want to adjust it themselves.
