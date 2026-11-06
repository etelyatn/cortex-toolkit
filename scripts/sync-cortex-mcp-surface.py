#!/usr/bin/env python3
"""Generate tests/fixtures/cortex-mcp-surface.json from an UnrealCortex plugin checkout.

The snapshot is the source of truth for tests/test_cortex_tool_names.py: it records the
MCP tools, routed commands and their declared parameter names a Cortex server actually
exposes, so skills and resources cannot name tools or parameters that do not exist.

Run inside the plugin's MCP environment (read-only use of the plugin; never `uv lock`):

    uv run --frozen --project <Plugin>/MCP python scripts/sync-cortex-mcp-surface.py --plugin <Plugin> --ref <commit-ish>
    uv run --frozen --project <Plugin>/MCP python scripts/sync-cortex-mcp-surface.py --plugin <Plugin> --ref origin/main --check

With --ref every source file (native handlers, MCP python tree, fixtures) is read from that
git revision (`git show` / `git archive`), never from the working tree, so the snapshot is
reproducible and the header records a measured commit. Without --ref the working tree is read
and the header records its HEAD and whether the surface paths are dirty.

Native handler declarations are authoritative for every domain they declare: the plugin's capabilities
fixture is registration input only and can lag, so a command or parameter only the fixture lists is
excluded and reported as FIXTURE-ONLY instead of resurrecting a removed native name.

--check fails only when the committed snapshot names a tool, domain, command or parameter the
source no longer has. Plugin additions never invalidate a documented name; they are reported.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
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

# Parameters native handlers read without declaring them. Documented examples may use them. The
# parameters the Python layer owns (pagination, projection) are derived per command in generate().
HONOURED_UNDECLARED_PARAMS = {"graph.get_subgraph": ["compact", "node_id"], "level.spawn_actor": ["level"]}

DOMAIN_REGISTRATION = re.compile(r'RegisterDomain\(\s*TEXT\("(\w+)"\)\s*,\s*TEXT\("([^"]*)"\)\s*,\s*TEXT\("([^"]*)"\)')
# `FCortexCommandInfo{TEXT("x"), ...}` and the `Commands.Add({TEXT("x"), TEXT("desc")})` form.
DECLARATION = re.compile(r'(?:FCortexCommandInfo\s*|Commands\.Add\(\s*)\{\s*TEXT\("(\w+)"\)\s*,')
PARAM = re.compile(r'\.(?:Required|Optional)\(\s*TEXT\("(\w+)"\)|\.Param\(\s*TEXT\("(\w+)"\)')
# Convenience builders on FCortexCommandInfo (ICortexDomainHandler.h) that declare a fixed parameter.
PARAM_HELPERS = {"OptionalBatchItems": "items", "OptionalExpectedFingerprint": "expected_fingerprint"}
HELPER_PARAM = re.compile(r"\.(" + "|".join(PARAM_HELPERS) + r")\(")


def declared_params(text: str) -> set[str]:
    """Parameter names declared in one command declaration's text (every builder form)."""
    names = {first or second for first, second in PARAM.findall(text)}
    names.update(PARAM_HELPERS[helper] for helper in HELPER_PARAM.findall(text))
    return names


class Tree:
    """Read access to the plugin sources, from a git revision or the working tree."""

    def __init__(self, plugin: Path, ref: str | None) -> None:
        self.plugin = plugin
        self.ref = ref
        self._names: list[str] | None = None

    def _git(self, *args: str) -> bytes:
        return subprocess.run(["git", "-C", str(self.plugin), *args], capture_output=True, check=True).stdout

    def names(self) -> list[str]:
        if self._names is None:
            if self.ref:
                self._names = self._git("ls-tree", "-r", "--name-only", self.ref).decode().splitlines()
            else:
                self._names = [p.relative_to(self.plugin).as_posix() for p in self.plugin.rglob("*") if p.is_file()]
        return self._names

    def read(self, rel: str) -> str:
        if self.ref:
            return self._git("show", f"{self.ref}:{rel}").decode("utf-8", errors="ignore")
        return (self.plugin / rel).read_text(encoding="utf-8", errors="ignore")

    def module_files(self, suffix: str) -> dict[str, list[str]]:
        """Map each Source/Cortex*/Private directory to its files ending in `suffix`."""
        found: dict[str, list[str]] = {}
        for name in self.names():
            parts = name.split("/")
            if len(parts) == 4 and parts[0] == "Source" and parts[1].startswith("Cortex") and parts[2] == "Private":
                if parts[3].endswith(suffix):
                    found.setdefault(parts[1], []).append(name)
        return found

    def mcp_root(self, scratch: Path) -> Path:
        if not self.ref:
            return self.plugin / "MCP"
        data = self._git("archive", self.ref, "MCP")
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(scratch)
        return scratch / "MCP"


def declared_domains(tree: Tree) -> dict[str, dict]:
    """Every domain a native module registers, with the commands (and parameter names) its handlers declare.

    Derived from Source/Cortex*/Private (the module's RegisterDomain call plus its
    *CommandHandler.cpp declarations), so a new module cannot be forgotten here. The
    committed capabilities fixture can lag these.
    """
    modules = tree.module_files("Module.cpp")
    handlers = tree.module_files("CommandHandler.cpp")
    domains: dict[str, dict] = {}
    for module in sorted(modules):
        registration = None
        for rel in modules[module]:
            registration = DOMAIN_REGISTRATION.search(tree.read(rel))
            if registration:
                break
        if registration is None:
            continue
        commands: dict[str, set[str]] = {}
        for rel in handlers.get(module, []):
            text = tree.read(rel)
            starts = list(DECLARATION.finditer(text))
            for index, match in enumerate(starts):
                end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
                commands.setdefault(match.group(1), set()).update(declared_params(text[match.end():end]))
        domain, title, version = registration.groups()
        domains[domain] = {"name": title, "version": version, "commands": commands}
    return domains


def provenance(tree: Tree) -> dict:
    """Plugin commit and branch; dirty is measured for a working tree and false for a git revision."""
    git = lambda *a: tree._git(*a).decode().strip()  # noqa: E731
    if tree.ref:
        return {"plugin_commit": git("rev-parse", tree.ref), "plugin_ref": tree.ref, "plugin_dirty": False}
    return {
        "plugin_commit": git("rev-parse", "HEAD"),
        "plugin_ref": git("rev-parse", "--abbrev-ref", "HEAD"),
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


def reconcile_surface(fixture_domains: dict, declared: dict[str, dict]) -> tuple[dict, dict, dict]:
    """Merge the capabilities fixture with native declarations; native declarations are authoritative.

    For a domain whose handlers declare commands, the supported commands and each command's
    parameters come from the declarations alone. A name only the fixture has (a command or
    parameter the handlers dropped while the fixture lags) is NOT carried over: it is returned
    in `fixture_only` so drift detection can see the removal. A domain the handlers do not
    declare keeps the fixture contract. Returns (domains, command_params, fixture_only).
    """
    domains: dict[str, list[str]] = {}
    command_params: dict[str, dict[str, list[str]]] = {}
    fixture_only: dict[str, list[str]] = {}
    for domain, body in fixture_domains.items():
        fixture = {c["name"]: {p["name"] for p in c.get("params", [])} for c in body["commands"]}
        native = declared.get(domain, {}).get("commands")
        if not native:
            domains[domain] = list(fixture)
            command_params[domain] = {name: sorted(params) for name, params in fixture.items()}
            continue
        # Fixture order first (a stable snapshot diff), then commands only the handlers declare.
        ordered = [name for name in fixture if name in native] + sorted(set(native) - set(fixture))
        domains[domain] = ordered
        command_params[domain] = {name: sorted(native[name]) for name in ordered}
        stale = [name for name in fixture if name not in native]
        stale += [f"{name} param {p}" for name, params in fixture.items() if name in native for p in sorted(params - native[name])]
        if stale:
            fixture_only[domain] = stale
    for domain, body in declared.items():
        if domain not in fixture_domains:
            domains[domain] = sorted(body["commands"])
            command_params[domain] = {name: sorted(params) for name, params in body["commands"].items()}
    return domains, command_params, fixture_only


def generate(plugin: Path, ref: str | None) -> dict:
    tree = Tree(plugin, ref)
    with tempfile.TemporaryDirectory() as scratch:
        mcp_root = tree.mcp_root(Path(scratch))
        capabilities = json.loads(tree.read("MCP/tests/fixtures/capabilities_cache_full.json"))
        legacy_snapshot = json.loads(tree.read("MCP/tests/fixtures/mcp_tool_signature_snapshot.json"))

        sys.path.insert(0, str(mcp_root / "src"))
        sys.path.insert(0, str(mcp_root))
        from cortex_mcp import server  # registers against a real FastMCP; no editor required
        from cortex_mcp.tools import routers

        if ref and Path(server.__file__).resolve().is_relative_to(plugin.resolve()):
            raise SystemExit("refusing to read the plugin working tree while --ref is set")

        declared = declared_domains(tree)
        domains, command_params, fixture_only = reconcile_surface(capabilities["domains"], declared)
        # Register against the declared commands plus every natively declared domain, so optional
        # domains (anim, gen) get their router tools exactly as a live editor would publish them,
        # and a command the handlers dropped is not registered from the stale fixture.
        for domain, body in declared.items():
            entry = capabilities["domains"].setdefault(
                domain, {"name": body["name"], "version": body["version"], "commands": []}
            )
            kept = {c["name"]: c for c in entry["commands"]}
            entry["commands"] = [
                kept.get(name, {"name": name, "description": "", "params": []}) for name in sorted(body["commands"])
            ]
        server.load_capabilities_cache = lambda: capabilities
        recorder = _RecordingServer()
        server._register_explicit_tools(recorder, server._connection)
        # Parameters the Python router owns, per command: limit/cursor exist only on the cache-owned
        # paginated reads; the capabilities projection owns `detail`. Any other command forwards the
        # field to a strict native contract, which refuses it.
        python_owned: dict[str, list[str]] = {}
        for qualified in sorted(routers.CACHED_PAGE_ARRAYS):
            python_owned[qualified] = ["cursor", "limit"]
        python_owned["core.get_capabilities"] = ["detail"]

    exposed = sorted(set(recorder.names))
    legacy: set[str] = set()
    for tools in legacy_snapshot.values():
        legacy.update(tools if isinstance(tools, list) else tools.keys())
    legacy -= set(exposed)

    for qualified, params in HONOURED_UNDECLARED_PARAMS.items():
        domain, command = qualified.split(".", 1)
        command_params[domain][command] = sorted(set(command_params[domain][command]) | set(params))
    # A legacy wrapper whose name is also a live routed command (e.g. add_widget) is not
    # provably stale from the name alone, so the lint must not flag it.
    legacy -= {command for names in domains.values() for command in names}
    legacy -= set(CORE_FACADE_COMMANDS)
    return {
        "provenance": provenance(tree),
        "exposed_tools": exposed,
        "domains": domains,
        "command_params": command_params,
        "python_owned_params": python_owned,
        "facade_commands": {"core": list(CORE_FACADE_COMMANDS)},
        "fixture_only": fixture_only,
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
    for domain, commands in committed.get("command_params", {}).items():
        for command, params in commands.items():
            live_params = fresh.get("command_params", {}).get(domain, {}).get(command)
            if live_params is None:
                continue  # the command itself is reported above
            missing.extend(f"{domain}.{command} param {p}" for p in params if p not in live_params)
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
    parser.add_argument("--plugin", required=True, type=Path, help="UnrealCortex plugin directory (a git checkout for --ref)")
    parser.add_argument("--ref", help="read every source from this git revision instead of the working tree")
    parser.add_argument("--check", action="store_true", help="fail when the snapshot names something the source lacks")
    args = parser.parse_args()

    snapshot = generate(args.plugin.resolve(), args.ref)
    for domain, names in snapshot["fixture_only"].items():
        print(f"FIXTURE-ONLY (stale plugin capabilities fixture, not in handler declarations; excluded): {domain}: {', '.join(names)}", file=sys.stderr)
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
