#!/usr/bin/env bash
# Cortex session-start hook — injects project memory into session context.
# Runs at session start/resume/clear/compact.

CORTEX_DIR=".cortex"
CONTEXT_FILE="$CORTEX_DIR/context.md"

# No .cortex/ directory — skip silently
if [ ! -d "$CORTEX_DIR" ]; then
  exit 0
fi

echo "# Cortex Project Context"
echo ""

# Inject shared project context
if [ -f "$CONTEXT_FILE" ]; then
  cat "$CONTEXT_FILE"
  echo ""
fi

# List available domain contexts
DOMAIN_DIR="$CORTEX_DIR/domains"
if [ -d "$DOMAIN_DIR" ]; then
  domains=$(ls "$DOMAIN_DIR"/*.md 2>/dev/null | xargs -I{} basename {} .md)
  if [ -n "$domains" ]; then
    echo "## Available Domain Contexts"
    echo ""
    echo "Read these files when working in a specific domain:"
    for d in $domains; do
      echo "- \`.cortex/domains/${d}.md\`"
    done
    echo ""
  fi
fi

# Show config summary if available
CONFIG_FILE="$CORTEX_DIR/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
  echo "## Project Configuration"
  echo ""
  echo "See \`.cortex/config.yaml\` for shared engine defaults, active domains, and doc references."
  echo "Optional per-machine overrides live in ignored \`.cortex/config.local.yaml\`."
fi
