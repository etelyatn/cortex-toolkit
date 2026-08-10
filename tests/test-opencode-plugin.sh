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

# Plugin
plugin_path = root / ".opencode" / "plugins" / "cortex.js"
if not plugin_path.exists():
    raise SystemExit(f"missing OpenCode plugin: {plugin_path}")
plugin = plugin_path.read_text(encoding="utf-8")
if "export const CortexPlugin" not in plugin:
    raise SystemExit("plugin must export CortexPlugin")
for hook in ("config", "messages.transform", "session.compacting"):
    if hook not in plugin:
        raise SystemExit(f"plugin must register hook {hook!r}")

# Root package.json
package_path = root / "package.json"
if not package_path.exists():
    raise SystemExit(f"missing root package.json: {package_path}")
pkg = json.loads(package_path.read_text(encoding="utf-8"))
if pkg.get("type") != "module":
    raise SystemExit("package.json type must be module")
if pkg.get("main") != ".opencode/plugins/cortex.js":
    raise SystemExit("package.json main must point at the OpenCode plugin")

codex_manifest = json.loads((root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
codex_version = codex_manifest.get("version", "")
if pkg.get("version") != codex_version:
    raise SystemExit("package.json version must match .codex-plugin/plugin.json")
cursor_manifest = json.loads((root / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
if cursor_manifest.get("version") != codex_version:
    raise SystemExit("cursor plugin version must match codex plugin version")

# Agent wrappers exist + body sync + no banned patterns
agents_dir = root / ".opencode" / "agents"
canon_dir = root / "agents"
if not agents_dir.is_dir():
    raise SystemExit(f"missing generated agents dir: {agents_dir}")

def _body(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    return text.split("---", 2)[2] if text.startswith("---") else text

for canon in sorted(canon_dir.glob("*.md")):
    wrapper = agents_dir / canon.name
    if not wrapper.exists():
        raise SystemExit(f"missing OpenCode agent wrapper for {canon.name}")
    wrapper_text = wrapper.read_text(encoding="utf-8")
    frontmatter = wrapper_text.split("---", 2)[1]
    if not wrapper_text.startswith("---\ndescription: "):
        raise SystemExit(f"agent wrapper {canon.name} must start with description frontmatter")
    if "\nname:" in frontmatter:
        raise SystemExit(f"agent wrapper {canon.name} must not carry a name field")
    if "mode: subagent" not in frontmatter:
        raise SystemExit(f"agent wrapper {canon.name} must declare mode: subagent")
    color_match = re.search(r"(?m)^color: (.+)$", frontmatter)
    if color_match:
        color_value = color_match.group(1).strip().strip('"')
        valid_color = bool(re.fullmatch(r"#[0-9a-fA-F]{6}", color_value)) or color_value in (
            "primary", "secondary", "accent", "success", "warning", "error", "info",
        )
        if not valid_color:
            raise SystemExit(f"agent wrapper {canon.name} has invalid OpenCode color {color_value!r}")
    if _body(canon).strip() != _body(wrapper).strip():
        raise SystemExit(f"agent body drift: {canon.name}")
    for banned in ("subagent_type", "AskUserQuestion", "Skill tool", "Task tool", "max_turns", "/cortex-", "/mcp"):
        if banned in wrapper_text:
            raise SystemExit(f"agent wrapper {canon.name} contains banned pattern {banned!r}")

# Banned-pattern compliance across skills (cortex-init Step 7 exempt)
BANNED = ("subagent_type", "AskUserQuestion", "Skill tool", "Task tool", "max_turns", "/cortex-", "/mcp")
for skill in sorted((root / "skills").glob("*/SKILL.md")):
    if skill.parent.name == "cortex-init":
        continue
    raw = skill.read_text(encoding="utf-8")
    text = raw.split("---", 2)[2] if raw.startswith("---") else raw
    for banned in BANNED:
        if banned in text:
            raise SystemExit(f"skill {skill.parent.name} contains banned pattern {banned!r}")

# Banned-pattern compliance across canonical agent bodies
for canon in sorted(canon_dir.glob("*.md")):
    raw = canon.read_text(encoding="utf-8")
    body = raw.split("---", 2)[2] if raw.startswith("---") else raw
    for banned in BANNED:
        if banned in body:
            raise SystemExit(f"agent {canon.stem} contains banned pattern {banned!r}")

# Docs + README
if not (root / ".opencode" / "INSTALL.md").exists():
    raise SystemExit("missing .opencode/INSTALL.md")
if not (root / "docs" / "opencode-setup.md").exists():
    raise SystemExit("missing docs/opencode-setup.md")
readme = (root / "README.md").read_text(encoding="utf-8")
if "OpenCode" not in readme:
    raise SystemExit("README must mention OpenCode")

print("opencode plugin tests passed")
PY
