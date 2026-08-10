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

# No agents ship with the toolkit — skills are the only mechanism. Guard against
# accidental re-introduction of agent definition files or wrapper generation.
if (root / "agents").exists():
    raise SystemExit("agents/ must not exist — toolkit is skills-only")
if (root / ".opencode" / "agents").exists():
    raise SystemExit(".opencode/agents must not exist — toolkit is skills-only")
if (root / "scripts" / "generate-opencode-agents.sh").exists():
    raise SystemExit("generate-opencode-agents.sh must not exist — toolkit is skills-only")

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

# Skills must reference only existing resources/ guides (no dangling agent-era paths)
resources = {p.stem for p in (root / "resources").glob("*.md")}
for skill in sorted((root / "skills").glob("*/SKILL.md")):
    raw = skill.read_text(encoding="utf-8")
    for m in re.finditer(r"resources/([\w-]+)\.md", raw):
        if m.group(1) not in resources:
            raise SystemExit(f"skill {skill.parent.name} references missing resource {m.group(1)}")

# Docs + README
if not (root / ".opencode" / "INSTALL.md").exists():
    raise SystemExit("missing .opencode/INSTALL.md")
if not (root / "docs" / "opencode-setup.md").exists():
    raise SystemExit("missing docs/opencode-setup.md")
readme = (root / "README.md").read_text(encoding="utf-8")
if "OpenCode" not in readme:
    raise SystemExit("README must mention OpenCode")
if "## Agents" in readme:
    raise SystemExit("README must not contain an Agents section")

# Bootstrap handshake: README must lead users with the fetch-instructions prompt, and
# INSTALL.md must present the git-backed plugin spec as the install mechanism BEFORE
# mentioning cortex-init (which only runs after the plugin is installed).
HANDSHAKE = "Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/main/.opencode/INSTALL.md"
if HANDSHAKE not in readme:
    raise SystemExit("README must contain the OpenCode install handshake prompt")
install_md = (root / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")
GIT_SPEC = "cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git"
if GIT_SPEC not in install_md:
    raise SystemExit("INSTALL.md must contain the git-backed plugin spec")
if install_md.find("cortex-init") < install_md.find(GIT_SPEC):
    raise SystemExit("INSTALL.md must present the git-backed install before cortex-init")

print("opencode plugin tests passed")
PY
