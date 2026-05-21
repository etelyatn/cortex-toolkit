#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
HOOK="$ROOT_DIR/hooks/check-ue-editor.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_eq() {
  local expected="$1"
  local actual="$2"
  local message="$3"
  if [ "$actual" != "$expected" ]; then
    fail "$message: expected '$expected', got '$actual'"
  fi
}

PROJECT=$(mktemp -d)
trap 'rm -rf "$PROJECT"' EXIT
mkdir -p "$PROJECT/.cortex"

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "C:/Project/UE"
YAML

RESULT=$(CORTEX_CONFIG_TEST_MODE=resolve_engine_path PROJECT_DIR="$PROJECT" UE_PATH="D:/Fallback/UE" "$HOOK")
assert_eq "C:/Project/UE" "$RESULT" "project config wins over UE_PATH"

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  version: "5.7"
YAML

RESULT=$(CORTEX_CONFIG_TEST_MODE=resolve_engine_path PROJECT_DIR="$PROJECT" UE_PATH="D:/Fallback/UE" "$HOOK")
assert_eq "D:/Fallback/UE" "$RESULT" "UE_PATH is used when project config has no engine.path"

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "D:/Broken
YAML

if CORTEX_CONFIG_TEST_MODE=resolve_engine_path PROJECT_DIR="$PROJECT" UE_PATH="D:/Fallback/UE" "$HOOK" >"$PROJECT/out.txt" 2>"$PROJECT/err.txt"; then
  fail "malformed project config should fail instead of falling back to UE_PATH"
fi

if ! grep -q "Failed to read Cortex config" "$PROJECT/err.txt"; then
  fail "malformed project config error should mention Cortex config read failure"
fi

echo "check-ue-editor config tests passed"
