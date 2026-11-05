#!/usr/bin/env python3
"""Generate tests/fixtures/cortex-mcp-surface.json from an UnrealCortex plugin checkout.

The snapshot is the source of truth for tests/test_cortex_tool_names.py: it records the
MCP tools and routed commands a Cortex server actually exposes, so skills and resources
cannot name tools that do not exist.

Run inside the plugin's MCP environment (read-only use of the plugin; never `uv lock`):

    uv run --project <Plugin>/MCP python scripts/sync-cortex-mcp-surface.py --plugin <Plugin>
    uv run --project <Plugin>/MCP python scripts/sync-cortex-mcp-surface.py --plugin <Plugin> --check

--check regenerates in memory and exits 1 when the committed snapshot differs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "cortex-mcp-surface.json"

# Commands the Python router answers itself, before forwarding to the editor
# (routers.py make_router, domain == "core"). They are absent from the native capabilities.
CORE_FACADE_COMMANDS = [
    "get_status",
    "get_capabilities",
    "schema_status",
    "get_data_catalog",
    "switch_editor",
    "batch_query",
]

DOMAIN_REGISTRATION = re.compile(r'RegisterDomain\(\s*TEXT\("(\w+)"\)\s*,\s*TEXT\("([^"]*)"\)\s*,\s*TEXT\("([^"]*)"\)')
DECLARATION = re.compile(r'FCortexCommandInfo\s*\{\s*TEXT\("(\w+)"\)')


def declared_domains(plugin: Path) -> dict[str, dict]:
    """Every domain a native module registers, with the commands its handlers declare.

    Derived from Source/Cortex*/Private (the module's RegisterDomain call plus its
    *CommandHandler.cpp declarations), so a new module cannot be forgotten here. The
    committed capabilities fixture can lag these (it lacked the anim domain,
    umg.rename_widget and reflect.blueprint_catalog).
    """
    domains: dict[str, dict] = {}
    for private in sorted((plugin / "Source").glob("Cortex*/Private")):
        registration = None
        for module_file in private.glob("*Module.cpp"):
            registration = DOMAIN_REGISTRATION.search(module_file.read_text(encoding="utf-8", errors="ignore"))
            if registration:
                break
        if registration is None:
            continue
        names: set[str] = set()
        for handler in private.glob("*CommandHandler.cpp"):
            names.update(DECLARATION.findall(handler.read_text(encoding="utf-8", errors="ignore")))
        domain, title, version = registration.groups()
        domains[domain] = {"name": title, "version": version, "commands": sorted(names)}
    return domains


def provenance(plugin: Path) -> dict:
    """Plugin commit, branch and whether the surface-bearing paths have uncommitted edits."""

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(plugin), *args], capture_output=True, text=True, check=True).stdout.strip()

    return {
        "plugin_commit": git("rev-parse", "HEAD"),
        "plugin_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "plugin_dirty": bool(git("status", "--porcelain", "--", "Source", "MCP/src", "MCP/tests")),
    }


class _RecordingServer:
    """Stands in for FastMCP: records tool names registered through ToolOutputRegistrar."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def tool(self, name=None, description=None, **_kwargs):
        def decorator(fn):
            self.names.append(name or fn.__name__)
            return fn

        return decorator


def generate(plugin: Path) -> dict:
    mcp_root = plugin / "MCP"
    fixtures = mcp_root / "tests" / "fixtures"
    capabilities = json.loads((fixtures / "capabilities_cache_full.json").read_text(encoding="utf-8"))
    legacy_snapshot = json.loads((fixtures / "mcp_tool_signature_snapshot.json").read_text(encoding="utf-8"))

    sys.path.insert(0, str(mcp_root / "src"))
    sys.path.insert(0, str(mcp_root))
    from cortex_mcp import server  # registers against a real FastMCP; no editor required

    declared = declared_domains(plugin)
    # Register against the fixture plus every natively declared domain, so optional domains
    # (anim, gen) get their router tools exactly as a live editor would publish them.
    for domain, body in declared.items():
        capabilities["domains"].setdefault(
            domain,
            {
                "name": body["name"],
                "version": body["version"],
                "commands": [{"name": name, "description": "", "params": []} for name in body["commands"]],
            },
        )
    server.load_capabilities_cache = lambda: capabilities
    recorder = _RecordingServer()
    server._register_explicit_tools(recorder, server._connection)

    exposed = sorted(set(recorder.names))
    legacy: set[str] = set()
    for tools in legacy_snapshot.values():
        legacy.update(tools if isinstance(tools, list) else tools.keys())
    legacy -= set(exposed)

    domains = {
        domain: [command["name"] for command in body["commands"]]
        for domain, body in capabilities["domains"].items()
    }
    # A command a handler declares is live even when the fixture lags: add it after the fixture names.
    for domain, body in declared.items():
        known = domains.setdefault(domain, [])
        known.extend(sorted(set(body["commands"]) - set(known)))
    # A legacy wrapper whose name is also a live routed command (e.g. add_widget) is not
    # provably stale from the name alone, so the lint must not flag it.
    legacy -= {command for names in domains.values() for command in names}
    legacy -= set(CORE_FACADE_COMMANDS)
    return {
        "provenance": provenance(plugin),
        "exposed_tools": exposed,
        "domains": domains,
        "facade_commands": {"core": list(CORE_FACADE_COMMANDS)},
        "legacy_tools": sorted(legacy),
    }


def removed_names(committed: dict, fresh: dict) -> list[str]:
    """Names the committed snapshot lists that the plugin surface no longer has.

    One-directional: plugin additions never invalidate a documented name, so they are not drift.
    """
    missing: list[str] = []
    for tool in committed.get("exposed_tools", []):
        if tool not in fresh["exposed_tools"]:
            missing.append(f"exposed tool {tool}")
    for domain, commands in committed.get("domains", {}).items():
        live = fresh["domains"].get(domain)
        if live is None:
            missing.append(f"domain {domain}")
            continue
        missing.extend(f"{domain}.{command}" for command in commands if command not in live)
    for domain, commands in committed.get("facade_commands", {}).items():
        missing.extend(
            f"{domain} facade {command}" for command in commands if command not in fresh["facade_commands"].get(domain, [])
        )
    return missing


def added_names(committed: dict, fresh: dict) -> list[str]:
    """Plugin names not yet in the snapshot (informational)."""
    added = [f"exposed tool {t}" for t in fresh["exposed_tools"] if t not in committed.get("exposed_tools", [])]
    for domain, commands in fresh["domains"].items():
        known = committed.get("domains", {}).get(domain, [])
        added.extend(f"{domain}.{c}" for c in commands if c not in known)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plugin", required=True, type=Path, help="UnrealCortex plugin directory")
    parser.add_argument("--check", action="store_true", help="fail when the snapshot names something the plugin lacks")
    parser.add_argument("--provenance-commit", help="record this commit in the header instead of the plugin HEAD")
    parser.add_argument("--provenance-branch", help="record this branch in the header instead of the plugin branch")
    args = parser.parse_args()

    snapshot = generate(args.plugin.resolve())
    if args.provenance_commit or args.provenance_branch:
        # Header only: use when the surface was verified equal to a shipped commit.
        snapshot["provenance"] = {
            "plugin_commit": args.provenance_commit or snapshot["provenance"]["plugin_commit"],
            "plugin_branch": args.provenance_branch or snapshot["provenance"]["plugin_branch"],
            "plugin_dirty": False,
        }
    if args.check:
        current = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.is_file() else {}
        removed = removed_names(current, snapshot)
        if removed:
            print(f"DRIFT: snapshot names absent from the plugin surface: {', '.join(removed)}", file=sys.stderr)
            return 1
        added = added_names(current, snapshot)
        print(f"surface snapshot valid; {len(added)} plugin addition(s) not in snapshot: {', '.join(added[:20])}")
        return 0
    text = json.dumps(snapshot, indent=2) + "\n"
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
