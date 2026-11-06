# Optional Agent Hooks (disabled by default) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every automatic Cortex Toolkit hook (PreToolUse editor guard + session-context injection) opt-in and disabled by default, without removing the hooks.

**Architecture:** A dependency-free bash gate (`hooks/hook-config.sh`) resolves per-project `hooks.*` switches from `.cortex/config.yaml` (overridable per machine by `.cortex/config.local.yaml`). Both packaged bash hooks source it and early-exit with code 0 and zero side effects when the switch is absent or false. The OpenCode plugin applies the same rule in JS before injecting session context. `run-hook.cmd` fails open (exit 0) when no bash is available so a missing shell never blocks MCP calls.

**Tech Stack:** Bash (Git Bash on Windows), Node ESM (OpenCode plugin), POSIX `sed`/`grep`, no new runtime dependencies.

**Spec:** https://github.com/etelyatn/cortex-toolkit/issues/63

## Global Constraints

- Hooks are **disabled by default**; missing config, missing project, missing key, or any value other than a truthy literal means disabled.
- Truthy literals accepted by the switches: `true`, `True`, `TRUE`, `yes`, `Yes`, `YES`, `on`, `On`, `ON`, `1`. Everything else is disabled.
- Opt-in keys (exact): `hooks.editor_guard` (PreToolUse editor guard) and `hooks.session_context` (session context injection), independent of each other.
- Precedence: `.cortex/config.local.yaml` wins over `.cortex/config.yaml` for any key it defines; absent key falls through to `config.yaml`.
- Disabled path must: exit 0, print nothing, invoke no Python, probe no TCP port, create/remove no lock or port file, launch no Editor, and inject no context — even when the project or its config is missing.
- Disabled path must not require the Unreal project to be discoverable.
- Enabled behavior is unchanged: `check-ue-editor.sh` still probes/launches the Editor and can block with exit 2; `session-start.sh` still prints the same context.
- No new runtime dependencies (only bash builtins + `sed`/`grep`/coreutils already required).
- Shell commands run through `rtk` (project rule). Do not use git worktrees.
- Version stays `0.11.1` (releases are bumped in separate `chore(release)` commits).

## Review Focus

- A hook that silently performs a side effect (TCP probe, lock creation, port-file removal, Editor launch, context print) when the switch is absent or false.
- `send`-the-switch precedence: `config.local.yaml: false` must beat `config.yaml: true`, and vice versa.
- Malformed/unreadable config must degrade to disabled, never to an error that blocks a tool call.
- The enabled path regressing (editor guard no longer probing/launching; session context no longer printed).
- Documentation claiming hooks run automatically, or omitting that `hooks.editor_guard: true` can launch the Editor.

---

### Task 1: Opt-in gate for the packaged bash hooks

**Files:**
- Create: `hooks/hook-config.sh`
- Modify: `hooks/check-ue-editor.sh` (top block: replace project resolution; drop the two walk-up helpers)
- Modify: `hooks/session-start.sh` (add gate; base paths on the resolved project dir)
- Modify: `hooks/run-hook.cmd` (final no-bash fallback: exit 0 instead of exit 2)
- Test: `tests/test-hook-optin.sh`

**Interfaces:**
- Consumes: nothing.
- Produces (used by later tasks and by both hooks):
  - `cortex_project_dir` → prints the project dir on stdout, returns 0; returns 1 when none found.
  - `cortex_walk_up_for_project <dir>` → prints the nearest ancestor (≤20 levels) containing `*.uproject` or `.cortex`, returns 0; returns 1 otherwise.
  - `cortex_config_raw_value <file> <key>` → prints `present:<value>` when the key line exists in `file` (value may be empty), and nothing when the file or key is absent.
  - `cortex_hook_enabled <key>` → returns 0 when the effective switch is truthy, 1 otherwise (default disabled).

- [ ] **Step 1: Write the failing test**

Create `tests/test-hook-optin.sh`:

```bash
#!/usr/bin/env bash
# Regression tests for the opt-in hook gate (cortex-toolkit issue #63).
#
# Proves: hooks are disabled by default with no side effects and no Python
# dependency; explicit opt-in enables each hook independently; config.local.yaml
# overrides config.yaml; the enabled paths are preserved.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CHECK_HOOK="$ROOT_DIR/hooks/check-ue-editor.sh"
SESSION_HOOK="$ROOT_DIR/hooks/session-start.sh"
GATE_LIB="$ROOT_DIR/hooks/hook-config.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }

assert_eq() {
  [ "$1" = "$2" ] || fail "$3: expected '$1', got '$2'"
}

assert_contains() {
  case "$2" in
    *"$1"*) ;;
    *) fail "$3: expected to contain '$1', got '$2'" ;;
  esac
}

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

PROJECT="$WORK/project"
mkdir -p "$PROJECT/.cortex" "$PROJECT/Saved"
: > "$PROJECT/CortexSandbox.uproject"

# Poisoned python: any hook that shells out to Python fails loudly.
POISON="$WORK/poison"
mkdir -p "$POISON"
for name in python python3; do
  printf '#!/usr/bin/env bash\necho "unexpected python invocation" >&2\nexit 97\n' > "$POISON/$name"
  chmod +x "$POISON/$name"
done

# Fake tasklist: readiness probing never depends on a real Editor.
NO_EDITOR="$WORK/no-editor"
mkdir -p "$NO_EDITOR"
printf '#!/usr/bin/env bash\nexit 0\n' > "$NO_EDITOR/tasklist"
chmod +x "$NO_EDITOR/tasklist"

saved_snapshot() { (cd "$PROJECT" && find Saved -mindepth 1 2>/dev/null | sort) || true; }

# Disabled-path runs: hermetic PATH (poisoned python), no ambient project override.
run_check_hook() {
  ( cd "$1" && env -u UE_PATH -u CORTEX_EDITOR_PID \
      CLAUDE_PROJECT_DIR="$1" PATH="$POISON:$NO_EDITOR:$PATH" bash "$CHECK_HOOK" )
}

# Enabled-path runs: real Python so engine-path resolution is exercised.
run_check_hook_enabled() {
  ( cd "$1" && env -u UE_PATH -u CORTEX_EDITOR_PID \
      CLAUDE_PROJECT_DIR="$1" PATH="$NO_EDITOR:$PATH" bash "$CHECK_HOOK" )
}

run_session_hook() {
  ( cd "$1" && env -u CORTEX_EDITOR_PID \
      CLAUDE_PROJECT_DIR="$1" PATH="$POISON:$NO_EDITOR:$PATH" bash "$SESSION_HOOK" )
}

flag() {
  # $1 = project dir, $2 = key -> "on" / "off"
  ( cd "$1" && CLAUDE_PROJECT_DIR="$1" \
      bash -c '. "$1"; if cortex_hook_enabled "$2"; then echo on; else echo off; fi' \
      _ "$GATE_LIB" "$2" )
}

# --- 1. Default off: config present, no hooks key ---------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "C:/Nonexistent/UE"
YAML
rm -f "$PROJECT/.cortex/config.local.yaml"

BEFORE=$(saved_snapshot)
set +e
OUT=$(run_check_hook "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "default-off check hook exit code"
assert_eq "" "$OUT" "default-off check hook stdout"
assert_eq "" "$(cat "$WORK/err.txt")" "default-off check hook stderr (no python, no failure)"
assert_eq "$BEFORE" "$(saved_snapshot)" "default-off check hook must not write to Saved"
assert_eq off "$(flag "$PROJECT" editor_guard)" "default-off editor_guard flag"

# --- 2. Explicit false -----------------------------------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  editor_guard: false
  session_context: false
YAML
set +e
OUT=$(run_check_hook "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "explicit-off check hook exit code"
assert_eq "" "$OUT" "explicit-off check hook stdout"
assert_eq off "$(flag "$PROJECT" session_context)" "explicit-off session_context flag"

# --- 3. Explicit opt-in reaches the enabled path ---------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  editor_guard: true
YAML
assert_eq on "$(flag "$PROJECT" editor_guard)" "opt-in editor_guard flag"
set +e
OUT=$(run_check_hook_enabled "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 2 "$RC" "opt-in check hook proceeds past the gate (no engine configured)"
assert_contains "engine path could not be determined" "$(cat "$WORK/err.txt")" \
  "opt-in check hook reports the missing engine path"

# --- 4. Precedence: local override wins ------------------------------------
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  editor_guard: false
YAML
assert_eq off "$(flag "$PROJECT" editor_guard)" "config.local.yaml false overrides config.yaml true"
set +e
OUT=$(run_check_hook_enabled "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "override-disabled hook exit code"
assert_eq "" "$(cat "$WORK/err.txt")" "override-disabled hook is silent"

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  session_context: false
YAML
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  session_context: true
YAML
assert_eq on "$(flag "$PROJECT" session_context)" "config.local.yaml true overrides config.yaml false"

# --- 5. Truthy / non-truthy literal handling -------------------------------
rm -f "$PROJECT/.cortex/config.local.yaml"
for value in true True TRUE yes on 1; do
  printf 'hooks:\n  session_context: %s\n' "$value" > "$PROJECT/.cortex/config.yaml"
  assert_eq on "$(flag "$PROJECT" session_context)" "value '$value' enables the switch"
done
for value in false no off 0 maybe '"true"'; do
  printf 'hooks:\n  session_context: %s\n' "$value" > "$PROJECT/.cortex/config.yaml"
  assert_eq off "$(flag "$PROJECT" session_context)" "value '$value' keeps the switch disabled"
done

# --- 6. Missing config / missing project => disabled -----------------------
rm -f "$PROJECT/.cortex/config.yaml" "$PROJECT/.cortex/config.local.yaml"
assert_eq off "$(flag "$PROJECT" session_context)" "missing config is disabled"
NO_PROJECT="$WORK/nothing"
mkdir -p "$NO_PROJECT"
assert_eq off "$(
  cd "$NO_PROJECT" && CLAUDE_PROJECT_DIR="$NO_PROJECT" \
    bash -c '. "$1"; if cortex_hook_enabled session_context; then echo on; else echo off; fi' \
    _ "$GATE_LIB"
)" "project without .cortex/.uproject is disabled"

# --- 7. Session hook: default off, opt-in prints context -------------------
cat > "$PROJECT/.cortex/context.md" <<'MD'
# Team conventions
Always use rtk.
MD
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "C:/Nonexistent/UE"
YAML
set +e
OUT=$(run_session_hook "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "default-off session hook exit code"
assert_eq "" "$OUT" "default-off session hook output"
assert_eq "" "$(cat "$WORK/err.txt")" "default-off session hook stderr"

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  session_context: true
YAML
set +e
OUT=$(run_session_hook "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "opt-in session hook exit code"
assert_contains "# Cortex Project Context" "$OUT" "opt-in session hook injects the context header"
assert_contains "Always use rtk." "$OUT" "opt-in session hook includes context.md"

# --- 8. Switches are independent -------------------------------------------
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  editor_guard: true
YAML
set +e
OUT=$(run_session_hook "$PROJECT" 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "session hook exit code with only editor_guard enabled"
assert_eq "" "$OUT" "session hook ignores the editor_guard switch"

echo "hook opt-in tests passed"
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `rtk bash -lc 'cd cortex-toolkit && bash tests/test-hook-optin.sh'`
Expected: FAIL — `hooks/hook-config.sh` does not exist yet (`. "$GATE_LIB"` / source error).

- [ ] **Step 3: Create `hooks/hook-config.sh`**

```bash
#!/usr/bin/env bash
# Shared gate for Cortex agent hooks (cortex-toolkit issue #63).
#
# Agent hooks are opt-in. This library resolves the effective value of the
# hooks.* switches from the project config and is deliberately dependency-free
# (no python, no Editor, no network) so the disabled path is a cheap,
# side-effect-free early exit on every host.
#
# Configuration, in the project's .cortex directory:
#   config.yaml        hooks: { editor_guard: <bool>, session_context: <bool> }
#   config.local.yaml  per-machine override; wins for the keys it defines
#
# Missing project, missing config, missing key, or an unrecognized value all
# mean "disabled".

# Print the nearest project directory: $CLAUDE_PROJECT_DIR when set, otherwise
# the closest ancestor of the current (or script) directory containing a
# .uproject file or a .cortex directory. Returns non-zero when none is found.
cortex_project_dir() {
    local start
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        printf '%s\n' "$CLAUDE_PROJECT_DIR"
        return 0
    fi
    for start in "$(pwd)" "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"; do
        [ -n "$start" ] || continue
        if cortex_walk_up_for_project "$start"; then
            return 0
        fi
    done
    return 1
}

# Walk up from a directory (at most 20 levels) looking for a project marker.
cortex_walk_up_for_project() {
    local dir="$1" parent
    for _ in $(seq 1 20); do
        if compgen -G "$dir/*.uproject" >/dev/null 2>&1 || [ -d "$dir/.cortex" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
        parent=$(dirname "$dir")
        [ "$parent" = "$dir" ] && break
        dir="$parent"
    done
    return 1
}

# Look up key in a Cortex config file. Prints "present:<value>" (the value may be
# empty) when the key line exists, and nothing when the file or key is absent, so
# callers can tell a present-but-empty/empty-scalar key apart from a missing key.
cortex_config_raw_value() {
    local file="$1" key="$2" value
    [ -f "$file" ] || return 0
    grep -q "^[[:space:]]*$key[[:space:]]*:" "$file" 2>/dev/null || return 0
    value=$(sed -n "s/^[[:space:]]*$key[[:space:]]*:[[:space:]]*\([^#[:space:]]*\).*/\1/p" "$file" | tail -n 1)
    printf 'present:%s\n' "$value"
}

# Return 0 when the effective hooks.<key> switch is truthy; 1 otherwise.
cortex_hook_enabled() {
    local key="$1" dir value
    dir=$(cortex_project_dir) || return 1
    value=$(cortex_config_raw_value "$dir/.cortex/config.local.yaml" "$key")
    # A present marker wins even when the local value is empty (empty => disabled);
    # fall through to config.yaml only when config.local.yaml does not define the key.
    [ -n "$value" ] || value=$(cortex_config_raw_value "$dir/.cortex/config.yaml" "$key")
    case "$value" in
        present:true|present:True|present:TRUE|present:yes|present:Yes|present:YES|present:on|present:On|present:ON|present:1) return 0 ;;
        *) return 1 ;;
    esac
}
```

- [ ] **Step 4: Gate `hooks/check-ue-editor.sh`**

Replace the header comment and the project-resolution block (the `_walk_up_for_uproject` helper, the `_find_project_dir` helper, and the `if [ -n "${CORTEX_CONFIG_TEST_MODE:-}" ] ...` block). Keep `set -uo pipefail`; the result must be:

```bash
#!/usr/bin/env bash
# PreToolUse guard: ensure Unreal Editor + CortexCore TCP are ready
# before any cortex_mcp tool call.
#
# Opt-in: runs only when hooks.editor_guard is true in the project's
# .cortex/config.yaml (or config.local.yaml); disabled otherwise, including a
# fresh install with no config. See README "Agent Hooks (opt-in)".
#
# Fast path (~50ms): port file valid + TCP responds → exit 0 silently
# Start path: lock-protected editor launch, 180s two-phase poll
# Fail path: exit 2 with Claude-directive stderr

set -uo pipefail

TOOLKIT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)
CORTEX_CONFIG_LOADER="$TOOLKIT_ROOT/lib/cortex_config.py"

# shellcheck source=hooks/hook-config.sh
. "$TOOLKIT_ROOT/hooks/hook-config.sh"

if [ -n "${CORTEX_CONFIG_TEST_MODE:-}" ]; then
    # Internal test entrypoints (tests/test-check-ue-editor-config.sh) drive
    # individual functions directly and bypass the opt-in gate.
    if [ -z "${PROJECT_DIR:-}" ]; then
        echo "PROJECT_DIR is required when CORTEX_CONFIG_TEST_MODE is set" >&2
        exit 2
    fi
else
    # Opt-in gate: no project or no explicit opt-in → no-op with no side effects.
    PROJECT_DIR=$(cortex_project_dir) || exit 0
    cortex_hook_enabled editor_guard || exit 0
fi

LOCK_DIR="$PROJECT_DIR/Saved/cortex-ue-editor-starting.lock"
RESTART_LOCK="$PROJECT_DIR/Saved/CortexRestarting.lock"
```

Everything from `_python_bin()` onward is unchanged (but `TOOLKIT_ROOT` and `CORTEX_CONFIG_LOADER` are now defined above, so delete their later definitions if any remain).

- [ ] **Step 5: Gate `hooks/session-start.sh`**

Replace the script with:

```bash
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
```

- [ ] **Step 6: Make `hooks/run-hook.cmd` fail open when bash is unavailable**

In `hooks/run-hook.cmd`, replace the final fallback

```bat
echo Cortex Toolkit hook requires Git Bash or another bash.exe on PATH. >&2
exit /b 2
```

with

```bat
REM No bash available: no-op instead of blocking. A missing shell must never
REM fail MCP tool calls; the hook simply does not run.
exit /b 0
```

- [ ] **Step 7: Run the new test and the existing hook tests**

Run: `rtk bash -lc 'cd cortex-toolkit && bash tests/test-hook-optin.sh && bash tests/test-check-ue-editor-config.sh'`
Expected: `hook opt-in tests passed` and `check-ue-editor config tests passed`.

- [ ] **Step 8: Commit**

```bash
cd cortex-toolkit
git add hooks/hook-config.sh hooks/check-ue-editor.sh hooks/session-start.sh hooks/run-hook.cmd tests/test-hook-optin.sh
git commit -m "feat(hooks): gate packaged agent hooks behind explicit opt-in"
```

---

### Task 2: Opt-in gate for the OpenCode session-context plugin

**Files:**
- Modify: `.opencode/plugins/cortex.js`
- Test: `tests/test-opencode-hooks.sh`

**Interfaces:**
- Consumes: the `hooks.session_context` key semantics from Task 1 (same truthy set, same precedence).
- Produces: nothing consumed by other tasks.

- [ ] **Step 1: Write the failing test**

Create `tests/test-opencode-hooks.sh`:

```bash
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

# A whitespace-only local value is also present and shadows config.yaml.
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
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `rtk bash -lc 'cd cortex-toolkit && bash tests/test-opencode-hooks.sh'`
Expected: FAIL — default-off case reports the plugin still injected session context.

- [ ] **Step 3: Add the gate to `.opencode/plugins/cortex.js`**

Add after `assembleContext` (or near the top-level helpers):

```js
const TRUTHY = new Set(['true', 'True', 'TRUE', 'yes', 'Yes', 'YES', 'on', 'On', 'ON', '1']);

// Opt-in gate mirroring hooks/hook-config.sh: session context is disabled
// unless hooks.session_context is truthy in .cortex/config.yaml, with a
// per-machine override in .cortex/config.local.yaml. A key line present in
// config.local.yaml — even with an empty or comment-only value — shadows
// config.yaml and evaluates to disabled.
function hookEnabled(projectDir, key) {
  const assignment = new RegExp(`^[ \\t]*${key}[ \\t]*:[ \\t]*([^#\\s]+)`, 'm');
  const emptyAssignment = new RegExp(`^[ \\t]*${key}[ \\t]*:[ \\t]*(#.*)?$`, 'm');
  for (const file of ['config.local.yaml', 'config.yaml']) {
    const configPath = path.join(projectDir, '.cortex', file);
    if (!fs.existsSync(configPath)) continue;
    const text = fs.readFileSync(configPath, 'utf8');
    const match = text.match(assignment);
    if (match) return TRUTHY.has(match[1]);
    if (emptyAssignment.test(text)) return false;
  }
  return false;
}
```

Then gate the two injection hooks:

```js
    'experimental.chat.messages.transform': async (_input, output) => {
      if (!hookEnabled(projectDir, 'session_context')) return;
      // ... existing body unchanged ...
    },

    'experimental.session.compacting': async (_input, output) => {
      if (!hookEnabled(projectDir, 'session_context')) return;
      output.context = output.context || [];
      output.context.push(getProjectContextOnly());
    }
```

The `config` hook (skills registration) is unchanged.

- [ ] **Step 4: Run the new test and the existing OpenCode test**

Run: `rtk bash -lc 'cd cortex-toolkit && bash tests/test-opencode-hooks.sh && bash tests/test-opencode-plugin.sh'`
Expected: `opencode hook opt-in tests passed` and `opencode plugin tests passed`.

- [ ] **Step 5: Commit**

```bash
cd cortex-toolkit
git add .opencode/plugins/cortex.js tests/test-opencode-hooks.sh
git commit -m "feat(opencode): gate session-context injection behind opt-in"
```

---

### Task 3: Document the opt-in model across hosts

**Files:**
- Modify: `README.md`
- Modify: `.codex/INSTALL.md`
- Modify: `docs/codex-setup.md`
- Modify: `docs/cursor-setup.md`
- Modify: `docs/opencode-setup.md`
- Modify: `.opencode/INSTALL.md`
- Modify: `templates/config.yaml`
- Modify: `skills/cortex-setup/SKILL.md`

**Interfaces:**
- Consumes: the exact key names and truthy semantics from Tasks 1–2.
- Produces: nothing consumed by other tasks.

- [ ] **Step 1: Add the README section and update the platform table**

In `README.md`, change the Hooks row of the Platform Support table to say hooks are opt-in and disabled by default for every host, then add a new `## Agent Hooks (opt-in)` section (after `## Getting Started`, before `## Skills`) containing exactly:

```markdown
## Agent Hooks (opt-in)

Cortex ships agent hooks, but they are **disabled by default**. A fresh
installation, or a project that has not opted in, performs no automatic
pre-tool checks, editor management, or session-context injection.

Enable them per project in `.cortex/config.yaml`:

```yaml
hooks:
  editor_guard: true      # PreToolUse: verify Cortex MCP readiness before cortex_mcp calls
  session_context: true   # SessionStart: inject .cortex context into the session
```

Both switches are independent and default to `false`. Per-machine overrides go
in `.cortex/config.local.yaml` (git-ignored) and win for the keys they define.

| Switch | Hook | Enabled behavior | Side effects |
|--------|------|------------------|--------------|
| `hooks.editor_guard` | `PreToolUse` (`mcp__cortex_mcp__.*`) | Probes the Cortex MCP endpoint before `cortex_mcp` calls | If the Unreal Editor is not running, launches it and waits up to ~180s; can remove stale port files and create startup locks; can block the call with exit code 2 |
| `hooks.session_context` | `SessionStart` (and the OpenCode plugin) | Prints `.cortex/context.md`, available domain contexts, and the config summary | Adds context to the session |

Scope: opt-in is **per project** (`<project>/.cortex/`). There is no global or
per-agent opt-in; hosts that cannot read the project config treat hooks as
disabled. When disabled, the hook wrappers exit immediately: they do not probe
ports, launch the Editor, create or remove lock/port files, inject context, or
require Python. Hook wrappers need Git Bash; when no bash is available they
no-op instead of blocking calls.

`cortex-editor` remains the explicit way to start or reconnect the Editor, and
connection failures from real MCP calls are still reported normally.

### Migration from auto-enabled hooks

Earlier toolkit versions ran these hooks automatically after install. After
upgrading, hooks stay off until you add the `hooks:` block above. If you relied
on automatic Editor startup or session-context injection, opt in explicitly;
otherwise start the Editor on demand with the `cortex-editor` skill.
```

- [ ] **Step 2: Update the Codex docs**

In `.codex/INSTALL.md` and `docs/codex-setup.md`, change the hook sentences so they state hooks are opt-in and disabled by default, name `hooks.editor_guard` / `hooks.session_context`, and keep the Codex trust explanation (the `test-codex-plugin.sh` check requires the word "trust" in `README.md`, `.codex/INSTALL.md`, and `docs/codex-setup.md`, and must not reintroduce "not packaged for Codex"). Example wording for `.codex/INSTALL.md`:

```markdown
Codex discovers `hooks/hooks.json` automatically after install. On first use,
review and trust the hooks when prompted. Hooks are **opt-in and disabled by
default**: the PreToolUse editor guard runs only when `hooks.editor_guard: true`
is set in `.cortex/config.yaml`, and the SessionStart context hook runs only
when `hooks.session_context: true` is set. With no config, hooks are trusted but
do nothing.
```

And in the Limitations list, change the trust bullet to note the default-off behavior.

- [ ] **Step 3: Update the Cursor and OpenCode docs**

- `docs/cursor-setup.md`: add a note that hooks (when the Cursor version fires them) are opt-in and disabled without config, naming the two keys.
- `docs/opencode-setup.md`: add that the plugin registers skills unconditionally but injects session context only when `hooks.session_context: true`.
- `.opencode/INSTALL.md`: mention the opt-in context injection alongside the skill registration sentence.

- [ ] **Step 4: Document the switches in the config template**

In `templates/config.yaml`, append:

```yaml

# Agent hooks are opt-in and disabled by default. Uncomment to enable; see the
# toolkit README "Agent Hooks (opt-in)" section.
# hooks:
#   editor_guard: false     # PreToolUse: check/launch the Unreal Editor before cortex_mcp calls
#   session_context: false  # SessionStart: inject .cortex context into the session
```

- [ ] **Step 5: Mention the opt-in in `cortex-setup`**

In `skills/cortex-setup/SKILL.md`, add to Init Mode (after the numbered steps, before the "If the plugin is missing" lines) a short paragraph:

```markdown
Agent hooks are opt-in and disabled by default. Do not enable them unless the
user asks: mention `hooks.editor_guard` and `hooks.session_context` in
`.cortex/config.yaml` only if they want automatic editor checks or session
context injection.
```

- [ ] **Step 6: Verify documentation checks and grep for stale claims**

Run: `rtk bash -lc "cd cortex-toolkit && bash tests/test-codex-plugin.sh && bash tests/test-opencode-plugin.sh"` and then
`rtk grep -rn "hooks automatically\|automatically.*hook" README.md .codex/INSTALL.md docs/ templates/ skills/` (expect no claim that hooks run automatically without opt-in).

- [ ] **Step 7: Commit**

```bash
cd cortex-toolkit
git add README.md .codex/INSTALL.md docs/codex-setup.md docs/cursor-setup.md docs/opencode-setup.md .opencode/INSTALL.md templates/config.yaml skills/cortex-setup/SKILL.md
git commit -m "docs(hooks): document opt-in hook configuration and migration"
```

---

## Verification (run after all tasks)

- `rtk bash -lc 'cd cortex-toolkit && bash tests/test-hook-optin.sh'`
- `rtk bash -lc 'cd cortex-toolkit && bash tests/test-opencode-hooks.sh'`
- `rtk bash -lc 'cd cortex-toolkit && bash tests/test-check-ue-editor-config.sh && bash tests/test-config-loader.sh && bash tests/test-codex-plugin.sh && bash tests/test-opencode-plugin.sh && bash tests/test-skill-taxonomy.sh'`
- `rtk bash -lc 'cd cortex-toolkit && uv run pytest tests/test_typed_blueprint_authoring_guidance.py -q'` (if `uv` is available)
- Real disabled-path smoke inside this workspace: `rtk bash -lc 'cd cortex-toolkit && CLAUDE_PROJECT_DIR=D:/UnrealProjects/CortexSandbox bash hooks/check-ue-editor.sh'` must exit 0 silently, and the same for `hooks/session-start.sh`.
