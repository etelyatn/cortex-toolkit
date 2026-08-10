#!/usr/bin/env bash
# Developer tool: regenerate committed .opencode/agents/*.md wrappers from canonical agents/*.md.
# Run BEFORE committing after editing any agents/*.md body or frontmatter.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
AGENTS_DIR="$ROOT_DIR/agents"
OUT_DIR="$ROOT_DIR/.opencode/agents"

mkdir -p "$OUT_DIR"

for f in "$AGENTS_DIR"/*.md; do
  name=$(basename "$f" .md)
  desc=$(awk '/^description:/{sub(/^description: /, ""); print; exit}' "$f")
  mode=$(awk '/^  opencode:/{f=1; next} f && /^    mode:/{sub(/^    mode: /, ""); print; exit}' "$f")
  color=$(awk '/^  opencode:/{f=1; next} f && /^    color:/{sub(/^    color: /, ""); print; exit}' "$f")
  body=$(awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$f")

  {
    echo "---"
    echo "description: $desc"
    echo "mode: ${mode:-subagent}"
    if [ -n "${color:-}" ]; then echo "color: $color"; fi
    echo "---"
    echo ""
    printf '%s\n' "$body"
  } > "$OUT_DIR/$name.md"
  echo "generated .opencode/agents/$name.md"
done
