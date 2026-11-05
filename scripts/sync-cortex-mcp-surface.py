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

# Native modules whose command handlers declare each domain's commands.
MODULE_DOMAINS = {
    "CortexCore": "core",
    "CortexData": "data",
    "CortexGraph": "graph",
    "CortexBlueprint": "blueprint",
    "CortexUMG": "umg",
    "CortexMaterial": "material",
    "CortexEditor": "editor",
    "CortexLevel": "level",
    "CortexQA": "qa",
    "CortexReflect": "reflect",
    "CortexStateTree": "statetree",
}
DECLARATION = re.compile(r'FCortexCommandInfo\s*\{\s*TEXT\("(\w+)"\)')


def declared_commands(plugin: Path) -> dict[str, set[str]]:
    """Commands the native handlers declare. The capabilities fixture can lag these."""
    declared: dict[str, set[str]] = {}
    for module, domain in MODULE_DOMAINS.items():
        for handler in (plugin / "Source" / module / "Private").glob("*CommandHandler.cpp"):
            text = handler.read_text(encoding="utf-8", errors="ignore")
            declared.setdefault(domain, set()).update(DECLARATION.findall(text))
    return declared


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
    # The committed capabilities fixture can lag the handlers (umg.rename_widget, reflect.blueprint_catalog
    # were declared but missing). A command a handler declares is live, so add it after the fixture names.
    for domain, names in declared_commands(plugin).items():
        known = domains.setdefault(domain, [])
        known.extend(sorted(names - set(known)))
    # A legacy wrapper whose name is also a live routed command (e.g. add_widget) is not
    # provably stale from the name alone, so the lint must not flag it.
    legacy -= {command for names in domains.values() for command in names}
    legacy -= set(CORE_FACADE_COMMANDS)
    return {
        "exposed_tools": exposed,
        "domains": domains,
        "facade_commands": {"core": list(CORE_FACADE_COMMANDS)},
        "legacy_tools": sorted(legacy),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plugin", required=True, type=Path, help="UnrealCortex plugin directory")
    parser.add_argument("--check", action="store_true", help="compare with the committed snapshot instead of writing")
    args = parser.parse_args()

    text = json.dumps(generate(args.plugin.resolve()), indent=2) + "\n"
    if args.check:
        current = SNAPSHOT.read_text(encoding="utf-8") if SNAPSHOT.is_file() else ""
        if current.replace("\r\n", "\n") != text:
            print(f"DRIFT: {SNAPSHOT} differs from the plugin surface; rerun without --check.", file=sys.stderr)
            return 1
        print("surface snapshot is current")
        return 0
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
