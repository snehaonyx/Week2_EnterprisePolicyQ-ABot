#!/usr/bin/env bash
# Symlinks every skill in skills/ into Claude Code's user-level skills
# directory (~/.claude/skills), so all projects on this machine pick them
# up without per-project setup. Safe to re-run; existing entries are skipped.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"

mkdir -p "$SKILLS_DIR"

for skill in "$SCRIPT_DIR"/skills/*/; do
  name="$(basename "$skill")"
  target="$SKILLS_DIR/$name"
  if [ -e "$target" ] || [ -L "$target" ]; then
    echo "Skipping $name: already exists at $target"
    continue
  fi
  ln -s "$(cd "$skill" && pwd)" "$target"
  echo "Linked $name -> $target"
done

echo "Done. Other tools (Codex, OpenCode, ...) have their own global skills directory:"
echo "symlink skills/<name> into it the same way."
