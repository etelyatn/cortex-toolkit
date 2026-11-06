"""Lint skills/resources/templates/docs/README for tool names the live Cortex MCP surface lacks.

The source of truth is tests/fixtures/cortex-mcp-surface.json, generated from an UnrealCortex
plugin checkout by scripts/sync-cortex-mcp-surface.py (issue #74).
"""

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SURFACE = json.loads((ROOT / "tests" / "fixtures" / "cortex-mcp-surface.json").read_text(encoding="utf-8"))

DOMAINS: dict[str, set[str]] = {domain: set(commands) for domain, commands in SURFACE["domains"].items()}
for _domain, _commands in SURFACE["facade_commands"].items():
    DOMAINS[_domain] |= set(_commands)
LEGACY = set(SURFACE["legacy_tools"])
EXPOSED = set(SURFACE["exposed_tools"])
ALL_COMMANDS = set().union(*DOMAINS.values())
# Pre-consolidation wrappers were named <domain>_<command> (graph_list_nodes). Such a name that is
# neither an exposed tool nor a live command is stale even when it was never in the legacy snapshot.
WRAPPER_DOMAINS = ("graph", "blueprint", "umg", "material", "statetree", "level", "qa", "reflect", "anim", "gen")
# The raw TCP batch envelope {"command": "batch", ...} is native and legitimate; core_cmd has no `batch`.
# Pre-consolidation wrappers also came as <command>_<noun> (reparent_blueprint, save_blueprint).
COMMAND_NOUN_DOMAINS = {"blueprint": "blueprint", "graph": "graph", "material": "material", "widget": "umg",
                        "level": "level", "datatable": "data", "statetree": "statetree", "scenario": "qa"}
NATIVE_ONLY_COMMANDS = {"batch"}
FILE_SUFFIXES = {"py", "json", "md", "cpp", "h", "log", "ini", "txt", "uasset", "cs", "yml", "yaml", "sh", "js", "ts"}
# Tools named by older docs that never existed under that name on the consolidated surface.
EXTRA_STALE = {"run_scenario"}
COMMAND_PARAMS: dict[str, dict[str, set[str]]] = {
    domain: {command: set(params) for command, params in commands.items()}
    for domain, commands in SURFACE.get("command_params", {}).items()
}
PYTHON_OWNED_PARAMS = set(SURFACE.get("python_owned_params", []))

ROUTER_OPEN = re.compile(r"(?<![\w}>*])([a-z][a-z0-9]*)_cmd\(")
ROUTER_NAME = re.compile(r"(?<![\w}>*<$])([a-z][a-z0-9]*)_cmd\b")
ROUTED_PROSE = re.compile(r"(?<![\w}>*])([a-z][a-z0-9]*)_cmd`?[ \t]+`?([a-z][a-z0-9]*(?:_[a-z0-9]+)*)\b")
SPLIT_BACKTICK = re.compile(r"`([a-z][a-z0-9]*)_cmd`[ \t]+`([a-z][a-z0-9_]*)`")
# `bp_variable` is the real mapping key of blueprint.adopt_native_member, not a legacy prefix.
OLD_DOMAIN_PREFIX = re.compile(r"(?<![\w.])bp[._](?!variable\b)[a-z][a-z0-9_]*")
MCP_PREFIXED = re.compile(r"\bmcp__[\w]+")
JSON_COMMAND = re.compile(r"[\"']command[\"']\s*:\s*[\"']([a-z][\w.]*)[\"']")
QUALIFIED = re.compile(r"(?<![\w./-])([a-z][a-z0-9]*)\.([a-z][a-z0-9_]*[a-z0-9])\b(?![*_])")
IDENTIFIER = re.compile(r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)(?![\w])")
FIRST_ARG = re.compile(
    r"^\s*(?:(?:command\s*=\s*)|[\"']command[\"']\s*:\s*)?[\"']([a-z][\w.]*)[\"']"
)
SHORTHAND_ARG = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*[,)]")
KEYWORD_COMMAND = re.compile(r"\bcommand\s*=\s*[\"']([a-z][\w.]*)[\"']|[\"']command[\"']\s*:\s*[\"']([a-z][\w.]*)[\"']")


def documents() -> list[Path]:
    files: list[Path] = [ROOT / "README.md", ROOT / ".opencode" / "INSTALL.md"]
    for folder in ("skills", "resources", "templates", "hooks"):
        files.extend(sorted((ROOT / folder).rglob("*.md")))
    files.extend(sorted((ROOT / "docs").glob("*.md")))
    return [path for path in files if path.is_file()]


def call_bodies(text: str):
    """Yield (offset, domain, body) for every `<domain>_cmd(...)` call, across lines."""
    for match in ROUTER_OPEN.finditer(text):
        depth, end = 1, match.end()
        limit = min(len(text), match.end() + 2500)
        while end < limit and depth:
            char = text[end]
            depth += char == "("
            depth -= char == ")"
            end += 1
        if depth:  # unbalanced (prose fragment): stop at the next router call or after 600 characters
            nxt = ROUTER_OPEN.search(text, match.end())
            end = min(nxt.start() if nxt else len(text), match.end() + 600)
        yield match.start(), match.group(1), text[match.end():end]


def split_top_level(text: str) -> list[str]:
    """Split on commas that are not nested in brackets or strings."""
    parts, depth, quote, start = [], 0, "", 0
    for index, char in enumerate(text):
        if quote:
            if char == quote and text[index - 1] != "\\":
                quote = ""
        elif char in "\"'":
            quote = char
        elif char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


PARAMS_OPEN = re.compile(r"[\"']?params[\"']?\s*[=:]\s*\{")


def params_literal_keys(body: str) -> list[str]:
    """Top-level keys of a literal `params={...}` / `"params": {...}` dict inside a call body."""
    match = PARAMS_OPEN.search(body)
    if not match:
        return []
    depth, quote, end = 1, "", match.end()
    while end < len(body) and depth:
        char = body[end]
        if quote:
            if char == quote and body[end - 1] != "\\":
                quote = ""
        elif char in "\"'":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        end += 1
    interior = body[match.end():end - 1 if depth == 0 else end]
    keys = []
    for segment in split_top_level(interior):
        key = re.match(r"\s*[\"']([A-Za-z_]\w*)[\"']\s*:", segment) or re.match(r"\s*([A-Za-z_]\w*)\s*(?::|$)", segment)
        if key:
            keys.append(key.group(1))
    return keys


def check_params(domain: str, command: str, body: str, problems: list) -> None:
    declared = COMMAND_PARAMS.get(domain, {}).get(command)
    if not declared:  # facade commands and commands that declare nothing cannot be checked
        return
    for key in params_literal_keys(body):
        if key not in declared and key not in PYTHON_OWNED_PARAMS and not key.startswith("_"):
            problems.append((f"{domain}_cmd {command} param {key}", f"a declared param: {', '.join(sorted(declared))}"))


def check_command(domain: str | None, command: str, problems: list) -> None:
    """Validate a (possibly qualified) command; `domain` is the router domain when known."""
    if "." in command:
        qualified_domain, name = command.split(".", 1)
        if qualified_domain not in DOMAINS:
            problems.append((command, "a `<domain>.<command>` of a live domain"))
        elif name not in DOMAINS[qualified_domain]:
            problems.append((command, f"a {qualified_domain} command"))
        return
    if domain is None:
        if command not in ALL_COMMANDS and command not in NATIVE_ONLY_COMMANDS:
            problems.append((f"command {command}", "a live command (or the native batch envelope)"))
    elif domain in DOMAINS and command not in DOMAINS[domain]:
        problems.append((f"{domain}_cmd {command}", f"a {domain} command"))


def lint_text(text: str) -> list[tuple[int, str, str]]:
    """Return (line, token, expected) problems for a whole document."""
    found: dict[tuple[int, str, str], None] = {}

    def add(offset: int, problems: list[tuple[str, str]]) -> None:
        line = text.count("\n", 0, offset) + 1
        for token, expected in problems:
            found[(line, token, expected)] = None

    for match in ROUTER_NAME.finditer(text):
        name = f"{match.group(1)}_cmd"
        if name not in EXPOSED and match.group(1) != "domain":  # `domain_cmd` is the documentation placeholder
            add(match.start(), [(name, "an exposed router tool (domain missing from the live surface)")])

    for offset, domain, body in call_bodies(text):
        problems: list[tuple[str, str]] = []
        first = FIRST_ARG.match(body)
        shorthand = SHORTHAND_ARG.match(body)
        command = None
        if first:
            command = first.group(1)
        elif shorthand and shorthand.group(1) not in {"command", "params"}:
            command = shorthand.group(1)
        else:
            keyword = KEYWORD_COMMAND.search(body)
            if keyword:
                command = keyword.group(1) or keyword.group(2)
        if command:
            check_command(domain, command, problems)
            if "." not in command and not problems:
                check_params(domain, command, body, problems)
        add(offset, problems)

    for match in ROUTED_PROSE.finditer(text):
        domain, token = match.groups()
        if domain not in DOMAINS or token in DOMAINS[domain]:
            continue
        if token in EXPOSED and "_cmd`" in match.group(0):  # two adjacent tool names, not a command
            continue
        elsewhere = [d for d, commands in DOMAINS.items() if token in commands]
        if token in LEGACY or token in EXPOSED or elsewhere or "_" in token:
            hint = f"a {domain} command (exists in: {', '.join(elsewhere)})" if elsewhere else f"a {domain} command"
            add(match.start(), [(f"{domain}_cmd {token}", hint)])

    for match in SPLIT_BACKTICK.finditer(text):
        domain, token = match.groups()
        if domain in DOMAINS and token not in DOMAINS[domain] and token not in EXPOSED:
            add(match.start(), [(f"{domain}_cmd {token}", f"a {domain} command")])

    for match in OLD_DOMAIN_PREFIX.finditer(text):
        add(match.start(), [(match.group(0), "legacy `bp.`/`bp_` prefix; use blueprint_cmd or blueprint.<command>")])

    for match in MCP_PREFIXED.finditer(text):
        tail = match.group(0)
        name = [piece for piece in tail.split("__") if piece][-1]
        suffixes = [name] + [name.split("_", skip)[-1] for skip in range(1, name.count("_") + 1)]
        if any(
            suffix in LEGACY
            or suffix in EXTRA_STALE
            or (
                suffix.split("_", 1)[0] in WRAPPER_DOMAINS
                and "_" in suffix
                and suffix not in EXPOSED
                and suffix not in ALL_COMMANDS
                and suffix.split("_", 1)[1] in ALL_COMMANDS
            )
            for suffix in suffixes
        ):
            add(match.start(), [(tail, "legacy wrapper tool name behind an mcp__ prefix")])

    for match in JSON_COMMAND.finditer(text):
        problems = []
        check_command(None, match.group(1), problems)
        add(match.start(), problems)

    for match in QUALIFIED.finditer(text):
        domain, command = match.groups()
        if domain in DOMAINS and command not in FILE_SUFFIXES and command not in DOMAINS[domain]:
            add(match.start(), [(f"{domain}.{command}", f"a {domain} command")])

    for match in IDENTIFIER.finditer(text):
        token = match.group(1)
        if token in EXTRA_STALE:
            add(match.start(), [(token, "not a tool on the live surface (scenario_compose / qa_cmd)")])
        if token in LEGACY or (
            token.split("_", 1)[0] in WRAPPER_DOMAINS
            and "_" in token
            and token not in EXPOSED
            and token not in ALL_COMMANDS
            and token.split("_", 1)[1] in ALL_COMMANDS
        ):
            add(match.start(), [(token, "legacy wrapper removed from the live surface; use the routed command")])
        else:
            parts = token.rsplit("_", 1)
            noun = parts[1].rstrip("s") if len(parts) == 2 else ""
            domain = COMMAND_NOUN_DOMAINS.get(noun)
            if (
                domain in DOMAINS
                and parts[0] in DOMAINS[domain]
                and token not in EXPOSED
                and token not in ALL_COMMANDS
            ):
                add(match.start(), [(token, f"the {domain} command `{parts[0]}` (wrapper-style name removed)")])

    return sorted(found)


def lint_line(text: str) -> list[tuple[str, str]]:
    return [(token, expected) for _, token, expected in lint_text(text)]


class CortexToolNameLint(unittest.TestCase):
    def test_documents_name_only_live_tools(self) -> None:
        failures: list[str] = []
        for path in documents():
            rel = path.relative_to(ROOT).as_posix()
            for line, token, expected in lint_text(path.read_text(encoding="utf-8")):
                failures.append(f"{rel}:{line} {token} -> {expected}")
        self.assertEqual([], failures, f"{len(failures)} stale tool references:\n" + "\n".join(failures))

    def test_snapshot_covers_the_registered_domains(self) -> None:
        for domain in ("core", "data", "graph", "blueprint", "umg", "material", "editor", "level", "qa", "reflect",
                       "statetree", "anim"):
            self.assertIn(domain, SURFACE["domains"])
            self.assertIn(f"{domain}_cmd", EXPOSED, f"{domain}_cmd missing from exposed_tools")
        for domain in SURFACE["domains"]:
            self.assertIn(f"{domain}_cmd", EXPOSED, f"domain {domain} has no exposed router tool")

    def test_lint_detects_known_stale_forms(self) -> None:
        self.assertTrue(lint_line('core_cmd(command="batch", params={})'))
        self.assertTrue(lint_line("never nest it inside `core_cmd(batch)`"))
        self.assertEqual([], lint_line("`umg_cmd(list_animation_bindings)` then `core_cmd(batch_query)`"))
        self.assertTrue(lint_line("Use `analyze_blueprint_for_migration` first."))
        self.assertTrue(lint_line("Use `reparent_blueprint` to change the parent."))
        self.assertTrue(lint_line("reparent_blueprint(asset_path=x)"))
        self.assertEqual([], lint_line("`blueprint_cmd(command=\"reparent\")` and remove_graph and save_level"))
        self.assertTrue(lint_line("call graph_list_nodes(asset_path)"))
        self.assertTrue(lint_line("`graph.list_nodes` lists nodes"))
        self.assertTrue(lint_line("blueprint_cmd graph_get_subgraph"))
        self.assertTrue(lint_line("reflect_cmd query_usages"))
        self.assertEqual([], lint_line('graph_cmd(command="search_nodes", params={})'))
        self.assertEqual([], lint_line("`blueprint.graph_metrics` then `core_cmd get_status`"))

    def test_lint_detects_new_false_negative_shapes(self) -> None:
        # unknown router domain
        self.assertTrue(lint_line('foo_cmd(command="x", params={})'))
        self.assertEqual([], lint_line('anim_cmd(command="list_assets", params={})'))
        # multi-line call with keyword command
        self.assertTrue(lint_line('blueprint_cmd(\n    params={"a": 1},\n    command="not_real",\n)'))
        # single quotes and JSON shapes
        self.assertTrue(lint_line("graph_cmd(command='nope')"))
        self.assertTrue(lint_line('{"command": "graph_get_subgraph", "params": {}}'))
        self.assertTrue(lint_line('{"command": "graph.nope", "params": {}}'))
        self.assertEqual([], lint_line('{"command": "batch", "params": {"commands": [{"command": "graph.add_node"}]}}'))
        # unbackticked prose and qualified names in code
        self.assertTrue(lint_line("call blueprint_cmd made_up_command now"))
        self.assertTrue(lint_line("x = graph.nope_command(asset_path)"))
        self.assertEqual([], lint_line("see docs in graph.json and graph.add_node"))

    def test_lint_checks_params_and_remaining_blind_spots(self) -> None:
        # literal params keys are checked against the declared params
        self.assertTrue(lint_line('umg_cmd(command="add_widget", params={"asset_path": "a", "parent": "P", "class": "B"})'))
        self.assertEqual([], lint_line(
            'umg_cmd(command="add_widget", params={"asset_path": "a", "parent_name": "P", "widget_class": "B", "name": "N"})'))
        self.assertEqual([], lint_line('graph_cmd(command="get_subgraph", params={"asset_path": "a", "compact": False})'))
        self.assertEqual([], lint_line('graph_cmd(command="search_nodes", params={"asset_path": "a", "limit": 50})'))
        self.assertTrue(lint_line("material_cmd(command='reset_parameter', params={asset_path, name})"))
        # split-backtick form, legacy bp prefix, run_scenario, mcp__ prefix
        self.assertTrue(lint_line("use `graph_cmd` `get_node` to read it"))
        self.assertEqual([], lint_line("tools: `blueprint_cmd` `graph_cmd` `blueprint_compose`"))
        self.assertTrue(lint_line("via `bp.get_info`"))
        self.assertTrue(lint_line("emitted by `run_scenario`"))
        self.assertTrue(lint_line("call mcp__cortex__graph_list_nodes"))

    def test_snapshot_matches_plugin_surface(self) -> None:
        plugin = os.environ.get("CORTEX_PLUGIN_DIR")
        plugin_dir = Path(plugin) if plugin else ROOT.parent / "Plugins" / "UnrealCortex"
        if not (plugin_dir / "MCP").is_dir():
            self.skipTest(f"no UnrealCortex plugin at {plugin_dir}; set CORTEX_PLUGIN_DIR to check drift")
        uv = shutil.which("uv")
        git = shutil.which("git")
        if uv is None or git is None:
            self.skipTest("uv or git not on PATH; cannot generate the plugin surface")
        ref = os.environ.get("CORTEX_PLUGIN_REF", "origin/main")
        probe = subprocess.run([git, "-C", str(plugin_dir), "rev-parse", "--verify", f"{ref}^{{commit}}"],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            self.skipTest(f"{plugin_dir} is not a git checkout with {ref}; set CORTEX_PLUGIN_REF")
        try:
            result = subprocess.run(
                [uv, "run", "--frozen", "--project", str(plugin_dir / "MCP"), "python",
                 str(ROOT / "scripts" / "sync-cortex-mcp-surface.py"), "--plugin", str(plugin_dir),
                 "--ref", ref, "--check"],
                capture_output=True, text=True, cwd=ROOT, timeout=300,
            )
        except subprocess.TimeoutExpired:
            self.skipTest("surface generation timed out (uv environment creation?)")
        if result.returncode != 0 and "DRIFT" not in result.stderr:
            self.skipTest(f"could not generate the plugin surface (uv/offline?): {result.stderr[-400:]}")
        self.assertEqual(0, result.returncode, result.stderr[-2000:])
        print(f"\nDrift note ({ref}): {result.stdout.strip()}")

    def test_drift_is_one_directional(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location("sync_surface", ROOT / "scripts" / "sync-cortex-mcp-surface.py")
        sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sync)
        fresh = json.loads(json.dumps(SURFACE))
        self.assertEqual([], sync.removed_names(SURFACE, fresh))
        extra = json.loads(json.dumps(SURFACE))
        extra["domains"]["reflect"].append("brand_new_command")
        self.assertEqual([], sync.removed_names(SURFACE, extra))
        self.assertEqual(["reflect.brand_new_command"], sync.added_names(SURFACE, extra))
        shrunk = json.loads(json.dumps(SURFACE))
        shrunk["domains"]["graph"].remove("add_node")
        self.assertEqual(["graph.add_node"], sync.removed_names(SURFACE, shrunk))


if __name__ == "__main__":
    unittest.main()
