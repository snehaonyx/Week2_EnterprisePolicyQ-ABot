#!/usr/bin/env bash
# Links every skill in vendor/agent-skills/skills/ into this project's
# Claude Code skills directory (.claude/skills/), so the project picks up
# the vendored skill library without a machine-wide install. Uses plain
# symlinks (no special privilege needed on macOS/Linux). Safe to re-run;
# existing entries are left alone.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vendor_skills_dir="$repo_root/vendor/agent-skills/skills"
target_skills_dir="$repo_root/.claude/skills"

if [ ! -d "$vendor_skills_dir" ]; then
  echo "Vendor skills dir not found at $vendor_skills_dir - did you run 'git submodule update --init'?" >&2
  exit 1
fi

mkdir -p "$target_skills_dir"

for skill_dir in "$vendor_skills_dir"/*/; do
  name="$(basename "$skill_dir")"
  target="$target_skills_dir/$name"
  if [ -e "$target" ]; then
    echo "Skipping $name: already exists at $target"
    continue
  fi
  ln -s "$skill_dir" "$target"
  echo "Linked $name -> $target"
done

echo "Done."
