#!/usr/bin/env bash
# Regression tests for the opt-in gate in the OpenCode plugin (issue #63).
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PLUGIN="$ROOT_DIR/.opencode/plugins/cortex.js"

fail() { echo "FAIL: $*" >&2; exit 1; }
assert_contains() {
  case "$2" in
    *"$1"*) ;;
    *) fail "$3: expected to contain '$1', got '$2'" ;;
  esac
}

command -v node >/dev/null 2>&1 || fail "node is required for OpenCode plugin tests"

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
PROJECT="$WORK/project"
mkdir -p "$PROJECT/.cortex"
cat > "$PROJECT/.cortex/context.md" <<'MD'
# Team conventions
Always use rtk.
MD

cat > "$WORK/probe.mjs" <<'JS'
import { pathToFileURL } from 'node:url';

const [pluginPath, projectDir] = process.argv.slice(2);
const { CortexPlugin } = await import(pathToFileURL(pluginPath).href);
const hooks = await CortexPlugin({ directory: projectDir });

// Skills registration is not gated.
const config = {};
await hooks.config(config);
console.log('SKILLS:' + JSON.stringify(config.skills && config.skills.paths || []));

const output = { messages: [{ info: { role: 'user' }, parts: [{ type: 'text', text: 'hello' }] }] };
await hooks['experimental.chat.messages.transform']({}, output);
console.log('INJECTED:' + (output.messages[0].parts.length > 1 ? output.messages[0].parts[0].text : ''));

const compact = {};
await hooks['experimental.session.compacting']({}, compact);
console.log('COMPACT:' + JSON.stringify(compact.context || []));
JS

run_probe() {
  ( cd "$PROJECT" && node "$WORK/probe.mjs" "$PLUGIN" "$PROJECT" )
}

# --- default off -----------------------------------------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "C:/Nonexistent/UE"
YAML
OUT=$(run_probe)
assert_contains "skills" "$(printf '%s\n' "$OUT" | grep '^SKILLS:')" "skills directory stays registered"
assert_contains "INJECTED:" "$OUT" "probe ran"
case "$OUT" in
  *"INJECTED:# Cortex Project Context"*) fail "default-off plugin must not inject session context" ;;
esac
case "$OUT" in
  *"COMPACT:[]"*) ;;
  *) fail "default-off plugin must not push compaction context: $OUT" ;;
esac

# --- opt-in ----------------------------------------------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  session_context: true
YAML
OUT=$(run_probe)
assert_contains "INJECTED:# Cortex Project Context" "$OUT" "opt-in plugin injects session context"
assert_contains "Always use rtk." "$OUT" "opt-in plugin includes context.md"
case "$OUT" in
  *"COMPACT:[]"*) fail "opt-in plugin must push compaction context" ;;
esac

# --- local override wins ---------------------------------------------------
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  session_context: false
YAML
OUT=$(run_probe)
case "$OUT" in
  *"INJECTED:# Cortex Project Context"*) fail "config.local.yaml false must disable injection" ;;
esac

# An empty local value still shadows config.yaml and means disabled.
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  session_context:
YAML
OUT=$(run_probe)
case "$OUT" in
  *"INJECTED:# Cortex Project Context"*) fail "empty config.local.yaml value must shadow config.yaml" ;;
esac

# A whitespace-only local value (no comment) still counts as present/disabled.
printf 'hooks:\n  session_context:%s\n' '   ' > "$PROJECT/.cortex/config.local.yaml"
OUT=$(run_probe)
case "$OUT" in
  *"INJECTED:# Cortex Project Context"*) fail "whitespace-only config.local.yaml value must shadow config.yaml" ;;
esac

rm -f "$PROJECT/.cortex/config.local.yaml"
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  editor_guard: true
YAML
OUT=$(run_probe)
case "$OUT" in
  *"INJECTED:# Cortex Project Context"*) fail "editor_guard must not enable session context" ;;
esac

echo "opencode hook opt-in tests passed"
