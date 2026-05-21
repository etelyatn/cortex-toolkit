#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOADER="$ROOT_DIR/lib/cortex_config.py"

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

run_loader() {
  "$PYTHON_BIN" "$LOADER" --project-dir "$1" --get "$2"
}

python_bin() {
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  fail "python or python3 is required"
}

make_project() {
  local dir
  dir=$(mktemp -d)
  mkdir -p "$dir/.cortex"
  echo "$dir"
}

PROJECT=$(make_project)
trap 'rm -rf "$PROJECT"' EXIT
PYTHON_BIN=$(python_bin)

cat > "$PROJECT/.cortex/config.yaml" <<'YAML'
engine:
  path: "C:/Base/UE_5.6"
  version: "5.6"

domains:
  - data
  - blueprint

references:
  design: docs/design.md
YAML

assert_eq "C:/Base/UE_5.6" "$(run_loader "$PROJECT" engine.path)" "base engine.path is used when no local config exists"
assert_eq "5.6" "$(run_loader "$PROJECT" engine.version)" "base engine.version is available"

cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
engine:
  path: "D:/Local/UE_5.6-source"

references:
  qa: docs/qa.md
YAML

assert_eq "D:/Local/UE_5.6-source" "$(run_loader "$PROJECT" engine.path)" "local engine.path overrides base path"
assert_eq "5.6" "$(run_loader "$PROJECT" engine.version)" "local engine merge preserves base version"
assert_eq "docs/design.md" "$(run_loader "$PROJECT" references.design)" "base reference survives local merge"
assert_eq "docs/qa.md" "$(run_loader "$PROJECT" references.qa)" "local reference is added"

cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
domains:
  - reflect
YAML

assert_eq "reflect" "$(run_loader "$PROJECT" domains)" "local list replaces base list"

cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
engine:
  path: "D:/Broken
YAML

if "$PYTHON_BIN" "$LOADER" --project-dir "$PROJECT" --get engine.path >"$PROJECT/out.txt" 2>"$PROJECT/err.txt"; then
  fail "malformed local YAML should fail"
fi

if ! grep -q "config.local.yaml" "$PROJECT/err.txt"; then
  fail "malformed local YAML error should name config.local.yaml"
fi

cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
engine:
	path: "D:/Tabbed/UE"
YAML

if "$PYTHON_BIN" "$LOADER" --project-dir "$PROJECT" --get engine.path >"$PROJECT/out.txt" 2>"$PROJECT/err.txt"; then
  fail "tab-indented local YAML should fail"
fi

if ! grep -q "tabs are not supported" "$PROJECT/err.txt"; then
  fail "tab-indented local YAML error should explain unsupported tabs"
fi

cat > "$PROJECT/.cortex/config.local.yaml" <<'YAML'
engine:
  path: "D:/Local/UE"
    version: "bad-indent"
YAML

if "$PYTHON_BIN" "$LOADER" --project-dir "$PROJECT" --get engine.version >"$PROJECT/out.txt" 2>"$PROJECT/err.txt"; then
  fail "over-indented local YAML should fail"
fi

if ! grep -q "invalid indentation" "$PROJECT/err.txt"; then
  fail "over-indented local YAML error should explain invalid indentation"
fi

echo "config loader tests passed"
