#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

python_bin() {
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  echo "python or python3 is required" >&2
  exit 1
}

PYTHON_BIN=$(python_bin)

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
skills_dir = root / "skills"
actual = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
expected = sorted([
    "cortex-setup",
    "cortex-editor",
    "cortex-build",
    "cortex-blueprint",
    "cortex-bp-migrate",
    "cortex-data",
    "cortex-umg",
    "cortex-material",
    "cortex-level",
    "cortex-statetree",
    "cortex-animation",
    "cortex-reflect",
    "cortex-test",
    "cortex-qa",
])
if actual != expected:
    raise SystemExit(f"expected skill dirs {expected}, got {actual}")

forbidden = [
    "cortex-start",
    "cortex-help",
    "cortex-init",
    "cortex-schema-refresh",
    "cortex-status",
    "cortex-restart",
    "cortex-qa-init",
    "cortex-qa-run",
    "cortex-qa-interactive",
    "cortex-reparent",
    "cortex-ui",
]

scan_suffixes = {".md", ".json", ".sh", ".yaml", ".yml"}
skip_paths = {
    Path("tests/test-skill-taxonomy.sh"),
}
for path in root.rglob("*"):
    if not path.is_file() or path.suffix not in scan_suffixes:
        continue
    rel_path = path.relative_to(root)
    if rel_path in skip_paths:
        continue
    text = path.read_text(encoding="utf-8")
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"stale skill reference {needle} in {rel_path}")

required_public_mentions = {
    "README.md": ["cortex-setup", "cortex-editor", "cortex-build", "cortex-blueprint", "cortex-bp-migrate", "cortex-data", "cortex-umg", "cortex-material", "cortex-level", "cortex-statetree", "cortex-animation", "cortex-reflect", "cortex-test", "cortex-qa"],
    "templates/context-block.md": ["cortex-setup", "cortex-editor", "cortex-build", "cortex-umg", "cortex-animation", "cortex-qa"],
}
for rel, required in required_public_mentions.items():
    text = (root / rel).read_text(encoding="utf-8")
    missing = [needle for needle in required if needle not in text]
    if missing:
        raise SystemExit(f"{rel} is missing public skill references: {missing}")

manifest_paths = [
    root / ".codex-plugin" / "plugin.json",
    root / ".claude-plugin" / "plugin.json",
    root / ".cursor-plugin" / "plugin.json",
]
versions = []
for path in manifest_paths:
    data = json.loads(path.read_text(encoding="utf-8"))
    versions.append(data["version"])
if len(set(versions)) != 1:
    raise SystemExit(f"plugin manifest versions diverged: {versions}")

marketplace = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
market_version = marketplace["metadata"]["version"]
plugin_version = marketplace["plugins"][0]["version"]
if market_version != plugin_version or market_version != versions[0]:
    raise SystemExit("marketplace versions must match plugin manifests")

print("skill taxonomy tests passed")
PY
