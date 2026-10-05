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

# A local key that is present but empty/null is a real override: it stays
# disabled and must NOT fall through to the base config's truthy value.
cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
hooks:
  editor_guard: true
YAML
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  editor_guard:
YAML
assert_eq off "$(flag "$PROJECT" editor_guard)" "empty local override disables despite config.yaml true"
cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
hooks:
  editor_guard:  # explicitly off
YAML
assert_eq off "$(flag "$PROJECT" editor_guard)" "commented empty local override disables despite config.yaml true"

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

# Genuinely no discoverable project: copy the packaged hooks outside any Unreal
# project, unset CLAUDE_PROJECT_DIR, and prove the disabled path is a silent no-op.
OUTSIDE="$WORK/outside-project"
mkdir -p "$OUTSIDE/hooks"
cp "$ROOT_DIR/hooks/"*.sh "$OUTSIDE/hooks/"
run_hook_no_project() {
  ( cd "$OUTSIDE" && env -u CLAUDE_PROJECT_DIR -u UE_PATH -u CORTEX_EDITOR_PID \
      PATH="$POISON:$NO_EDITOR:$PATH" bash "$OUTSIDE/hooks/$1" )
}
set +e
OUT=$(run_hook_no_project check-ue-editor.sh 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "no-project check hook exit code"
assert_eq "" "$OUT" "no-project check hook stdout"
assert_eq "" "$(cat "$WORK/err.txt")" "no-project check hook stderr"

set +e
OUT=$(run_hook_no_project session-start.sh 2>"$WORK/err.txt"); RC=$?
set -e
assert_eq 0 "$RC" "no-project session hook exit code"
assert_eq "" "$OUT" "no-project session hook stdout"
assert_eq "" "$(cat "$WORK/err.txt")" "no-project session hook stderr"

# The walk-up helper must fail for a bare directory (no .uproject / .cortex).
if ( cd "$OUTSIDE" && bash -c '. "$1"; cortex_walk_up_for_project "$2" >/dev/null' \
      _ "$OUTSIDE/hooks/hook-config.sh" "$OUTSIDE" ); then
  fail "cortex_walk_up_for_project should fail for a bare temp dir"
fi

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
