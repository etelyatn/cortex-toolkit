#!/usr/bin/env bash
# Cortex session-start hook — injects project memory into session context.
# Runs at session start/resume/clear/compact.
#
# Opt-in: runs only when hooks.session_context is true in the project's
# .cortex/config.yaml (or config.local.yaml); disabled otherwise.

set -uo pipefail

TOOLKIT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)
# shellcheck source=hooks/hook-config.sh
. "$TOOLKIT_ROOT/hooks/hook-config.sh"

PROJECT_DIR=$(cortex_project_dir) || exit 0
cortex_hook_enabled session_context || exit 0

CORTEX_DIR="$PROJECT_DIR/.cortex"
CONTEXT_FILE="$CORTEX_DIR/context.md"

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
