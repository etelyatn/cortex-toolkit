"""Lint skills/resources/templates/README for tool names the live Cortex MCP surface lacks.

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
WRAPPER_DOMAINS = ("graph", "blueprint", "umg", "material", "statetree", "level", "qa", "reflect")

ROUTED_CALL = re.compile(r"\b([a-z]+)_cmd\(\s*(?:command\s*=\s*)?[\"'](\w+)[\"']")
ROUTED_SHORTHAND = re.compile(r"\b([a-z]+)_cmd\(\s*([a-z][a-z0-9_]*)\s*[,)]")
ROUTED_PROSE = re.compile(r"\b([a-z]+)_cmd[ \t]+`?([a-z][a-z0-9]*(?:_[a-z0-9]+)*)\b")
QUALIFIED = re.compile(r"`([a-z]+)\.([a-z][a-z0-9_]*)`")
IDENTIFIER = re.compile(r"(?<![\w.])([A-Za-z_][A-Za-z0-9_]*)(?![\w])")


def documents() -> list[Path]:
    files: list[Path] = [ROOT / "README.md"]
    for folder in ("skills", "resources", "templates"):
        files.extend(sorted((ROOT / folder).rglob("*.md")))
    return [path for path in files if path.is_file()]


def lint_line(text: str) -> list[tuple[str, str]]:
    """Return (token, expected) problems for one line."""
    problems: list[tuple[str, str]] = []
    for domain, command in ROUTED_CALL.findall(text) + [
        (d, c) for d, c in ROUTED_SHORTHAND.findall(text) if c not in {"command", "params"}
    ]:
        if domain in DOMAINS and command not in DOMAINS[domain]:
            problems.append((f"{domain}_cmd {command}", f"a {domain} command"))
    for domain, token in ROUTED_PROSE.findall(text):
        if domain not in DOMAINS or token in DOMAINS[domain]:
            continue
        elsewhere = [d for d, commands in DOMAINS.items() if token in commands]
        if token in LEGACY or token in EXPOSED or elsewhere:
            hint = f"a {domain} command (exists in: {', '.join(elsewhere)})" if elsewhere else f"a {domain} command"
            problems.append((f"{domain}_cmd {token}", hint))
    for domain, command in QUALIFIED.findall(text):
        if domain in DOMAINS and command not in DOMAINS[domain]:
            problems.append((f"{domain}.{command}", f"a {domain} command"))
    for token in IDENTIFIER.findall(text):
        if token in LEGACY or (
            token.split("_", 1)[0] in WRAPPER_DOMAINS
            and "_" in token
            and token not in EXPOSED
            and token not in ALL_COMMANDS
            and token.split("_", 1)[1] in ALL_COMMANDS
        ):
            problems.append((token, "legacy wrapper removed from the live surface; use the routed command"))
    return problems


class CortexToolNameLint(unittest.TestCase):
    def test_documents_name_only_live_tools(self) -> None:
        failures: list[str] = []
        for path in documents():
            rel = path.relative_to(ROOT).as_posix()
            for number, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                seen: set[tuple[str, str]] = set()
                for token, expected in lint_line(text):
                    if (token, expected) not in seen:
                        seen.add((token, expected))
                        failures.append(f"{rel}:{number} {token} -> {expected}")
        self.assertEqual([], failures, f"{len(failures)} stale tool references:\n" + "\n".join(failures))

    def test_lint_detects_known_stale_forms(self) -> None:
        self.assertTrue(lint_line('core_cmd(command="batch", params={})'))
        self.assertTrue(lint_line("never nest it inside `core_cmd(batch)`"))
        self.assertEqual([], lint_line("`umg_cmd(list_animation_bindings)` then `core_cmd(batch_query)`"))
        self.assertTrue(lint_line("Use `analyze_blueprint_for_migration` first."))
        self.assertTrue(lint_line("call graph_list_nodes(asset_path)"))
        self.assertTrue(lint_line("`graph.list_nodes` lists nodes"))
        self.assertTrue(lint_line("blueprint_cmd graph_get_subgraph"))
        self.assertTrue(lint_line("reflect_cmd query_usages"))
        self.assertEqual([], lint_line('graph_cmd(command="search_nodes", params={})'))
        self.assertEqual([], lint_line("`blueprint.graph_metrics` then `core_cmd get_status`"))

    def test_snapshot_matches_plugin_surface(self) -> None:
        plugin = os.environ.get("CORTEX_PLUGIN_DIR")
        plugin_dir = Path(plugin) if plugin else ROOT.parent / "Plugins" / "UnrealCortex"
        if not (plugin_dir / "MCP" / "tests" / "fixtures" / "capabilities_cache_full.json").is_file():
            self.skipTest(f"no UnrealCortex plugin at {plugin_dir}; set CORTEX_PLUGIN_DIR to check drift")
        uv = shutil.which("uv")
        if uv is None:
            self.skipTest("uv not on PATH; cannot generate the plugin surface")
        result = subprocess.run(
            [uv, "run", "--project", str(plugin_dir / "MCP"), "python",
             str(ROOT / "scripts" / "sync-cortex-mcp-surface.py"), "--plugin", str(plugin_dir), "--check"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(0, result.returncode, result.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
