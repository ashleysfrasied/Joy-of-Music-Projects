#!/usr/bin/env bash
# Copy skill definitions from .cursor/skills/ (canonical) to .claude/skills/.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
SRC="$ROOT/.cursor/skills"
DEST="$ROOT/.claude/skills"

for skill_dir in "$SRC"/*/; do
  skill="$(basename "$skill_dir")"
  if [[ -f "$skill_dir/SKILL.md" ]]; then
    mkdir -p "$DEST/$skill"
    cp "$skill_dir/SKILL.md" "$DEST/$skill/SKILL.md"
    echo "synced $skill"
  fi
done

echo "Done. Edit skills in .cursor/skills/, then run this script."
