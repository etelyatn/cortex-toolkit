#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

fail() {
  echo "FAIL: $*" >&2
  exit 1
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

PYTHON_BIN=$(python_bin)

"$PYTHON_BIN" - "$ROOT_DIR" <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = root / ".codex-plugin" / "plugin.json"
marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
hooks_path = root / "hooks" / "hooks.json"

if not manifest_path.exists():
    raise SystemExit(f"missing Codex plugin manifest: {manifest_path}")

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("name") != "cortex-toolkit":
    raise SystemExit("plugin manifest name must be cortex-toolkit")

version = manifest.get("version", "")
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"plugin version must be strict semver, got {version!r}")

if manifest.get("skills") != "./skills/":
    raise SystemExit("plugin manifest must expose ./skills/")

if "mcpServers" in manifest and not (root / ".mcp.json").exists():
    raise SystemExit("manifest must not declare mcpServers without a root .mcp.json")

interface = manifest.get("interface") or {}
for key in ("displayName", "shortDescription", "longDescription", "developerName", "category", "capabilities"):
    if not interface.get(key):
        raise SystemExit(f"manifest interface.{key} is required")

if not marketplace_path.exists():
    raise SystemExit(f"missing Codex marketplace: {marketplace_path}")

marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
plugins = marketplace.get("plugins") or []
entry = next((plugin for plugin in plugins if plugin.get("name") == "cortex-toolkit"), None)
if entry is None:
    raise SystemExit("marketplace must include cortex-toolkit entry")

policy = entry.get("policy") or {}
if policy.get("installation") != "AVAILABLE":
    raise SystemExit("marketplace policy.installation must be AVAILABLE")
if policy.get("authentication") != "ON_INSTALL":
    raise SystemExit("marketplace policy.authentication must be ON_INSTALL")
if not entry.get("category"):
    raise SystemExit("marketplace entry category is required")

source = entry.get("source") or {}
if source.get("source") != "url":
    raise SystemExit("marketplace source must be url")
if source.get("url") != "https://github.com/etelyatn/cortex-toolkit.git":
    raise SystemExit("marketplace source.url must point to cortex-toolkit")
if source.get("ref") != "main":
    raise SystemExit("marketplace source.ref must be main")

if not hooks_path.exists():
    raise SystemExit(f"missing Codex-discovered hooks config: {hooks_path}")

hooks_manifest = json.loads(hooks_path.read_text(encoding="utf-8"))
hooks = hooks_manifest.get("hooks") or {}
pre_tool_use = hooks.get("PreToolUse") or []
session_start = hooks.get("SessionStart") or []
if len(pre_tool_use) != 1:
    raise SystemExit("hooks.json must define one PreToolUse hook group")
if len(session_start) != 1:
    raise SystemExit("hooks.json must define one SessionStart hook group")
if pre_tool_use[0].get("matcher") != "mcp__cortex_mcp__.*":
    raise SystemExit("PreToolUse hook must guard cortex_mcp tool calls")

docs_to_check = [
    root / "README.md",
    root / ".codex" / "INSTALL.md",
    root / "docs" / "codex-setup.md",
]
for doc_path in docs_to_check:
    contents = doc_path.read_text(encoding="utf-8")
    if "not packaged for Codex" in contents:
        raise SystemExit(f"{doc_path.relative_to(root)} must not say hooks are not packaged")
    if "trust" not in contents.lower():
        raise SystemExit(f"{doc_path.relative_to(root)} must explain Codex hook trust")

print("codex plugin tests passed")
PY
