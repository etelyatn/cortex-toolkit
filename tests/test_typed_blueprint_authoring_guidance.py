"""Guidance and fixture checks for the typed Blueprint authoring workflow.

Scope: this module proves toolkit guidance and checked-in JSON shape only. It never contacts the
Editor and never speaks to the MCP layer, so it cannot prove Unreal behaviour; the live bindings it
names are exercised by the consuming plugin scenario under an Editor lease.

The published contract has exactly one owner: the connected Editor
(``graph.get_authoring_context`` / ``graph.describe_node`` / ``core.get_operation_schema``) and its
native implementation in ``Plugins/UnrealCortex/Source/CortexGraph``. ``PUBLISHED_FAMILIES`` and
``PUBLISHED_MIGRATION_OPS`` exist only so a checked-in fixture cannot silently invent a node family
or a migration operation. They are check guard rails, not a registry the toolkit uses to build
calls: no alias table, limit table or selector catalog is reproduced here, and the guidance defers
to the live schema for all of them.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GUIDE = ROOT / "resources/typed-blueprint-authoring.md"
EXAMPLES = ROOT / "examples/typed-blueprint-authoring"
README = EXAMPLES / "README.md"

# Slice of the graph authoring contract the checked-in fixtures rely on.
PUBLISHED_FAMILIES = (
    "CallFunction",
    "VariableGet",
    "VariableSet",
    "Self",
    "DynamicCast",
    "ConstructObject",
    "Event",
)
PUBLISHED_MIGRATION_OPS = ("replace_entry", "copy_subgraph", "move_subgraph", "prune_island")
TAGGED_DEFAULT_KINDS = (
    "class",
    "soft_class",
    "object",
    "soft_object",
    "text",
    "bool",
    "int",
    "real",
    "float",
    "string",
    "name",
    "enum",
    "null",
)

FRAGMENT_FIELDS = {
    "asset_path",
    "target",
    "patch_id",
    "expected_fingerprint",
    "nodes",
    "connections",
    "pin_updates",
    "dry_run",
    "compile",
    "save",
    "allow_noop",
    "expected_validation_hash",
    "migration",
}
NODE_FIELDS = {"client_id", "node_class", "params", "defaults", "position"}
ENDPOINT_FIELDS = {"client_id", "node_guid", "entry", "pin"}
FLAG_FIELDS = ("dry_run", "compile", "save", "allow_noop")
MIGRATION_FIELDS = {
    "op",
    "source",
    "destination",
    "boundary",
    "pin_map",
    "remove_shadowing_member",
    "approved_node_guids",
}

# A default is a tagged value, never an object reference expressed as an edge.
EDGE_AS_DEFAULT_KEYS = {"node", "node_guid", "client_id", "entry", "from", "to", "ref", "$self"}

LIVE_TOKEN = re.compile(r"<live: ([^<>]+)>")
ANY_ANGLE_TOKEN = re.compile(r"<[^<>]*>")
GUID_LITERAL = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
HASH_LITERAL = re.compile(r"\b[0-9a-fA-F]{32,}\b")
CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class ShapeError(AssertionError):
    """A checked-in fixture does not satisfy the published request shape."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ShapeError(message)


def _strings(value, path: str = "$"):
    """Yield ``(json_path, string)`` for every string in a decoded fixture."""
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from _strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _strings(child, f"{path}[{index}]")


def _validate_tagged_default(pin_name: str, default, context: str) -> None:
    _require(isinstance(default, dict), f"{context}.defaults['{pin_name}'] must be a tagged object")
    for key in default:
        _require(
            key not in EDGE_AS_DEFAULT_KEYS,
            f"{context}.defaults['{pin_name}'] must not express an edge as a default ('{key}')",
        )
    kind = default.get("kind")
    _require(
        isinstance(kind, str) and kind in TAGGED_DEFAULT_KINDS,
        f"{context}.defaults['{pin_name}'] needs a published 'kind' tag, got {kind!r}",
    )
    for json_path, text in _strings(default, f"{context}.defaults['{pin_name}']"):
        _require("$self" not in text, f"{json_path} must not use a magic self reference")


def _validate_endpoint(endpoint, context: str) -> None:
    _require(isinstance(endpoint, dict), f"{context} must be an object")
    unknown = set(endpoint) - ENDPOINT_FIELDS
    _require(not unknown, f"{context} has unknown field(s) {sorted(unknown)}")
    identities = [key for key in ("client_id", "node_guid", "entry") if key in endpoint]
    _require(len(identities) == 1, f"{context} requires exactly one endpoint identity, got {identities}")
    if "entry" in endpoint:
        _require(endpoint["entry"] is True, f"{context}.entry must be true")
    if "client_id" in endpoint:
        _require(CLIENT_ID.match(endpoint["client_id"]) is not None, f"{context}.client_id is invalid")
    pin = endpoint.get("pin")
    _require(isinstance(pin, str) and pin, f"{context}.pin must be a non-empty string")
    if LIVE_TOKEN.search(pin) is None:
        _require(not any(character.isspace() for character in pin), f"{context}.pin must not contain whitespace")


def _validate_migration_shell(fragment: dict, migration: dict) -> None:
    op = migration["op"]
    source = migration.get("source")
    _require(isinstance(source, dict), "migration.source must be an object")
    has_target = "target" in fragment
    if op == "replace_entry":
        _require(
            isinstance(fragment.get("target"), dict) and "implementation" in fragment["target"],
            "replace_entry needs target.implementation declaring the replaced entry",
        )
        _require("graph_ref" not in fragment["target"], "replace_entry takes an implementation target, never graph_ref")
        _require(isinstance(source.get("graph_ref"), dict), "migration.source.graph_ref must be an object")
        _require(isinstance(source.get("entry_node_guid"), str), "migration.source.entry_node_guid is required")
        pin_map = migration.get("pin_map")
        _require(isinstance(pin_map, list) and pin_map, "replace_entry needs a non-empty migration.pin_map")
        for entry in pin_map:
            _require(set(entry) == {"entry", "from_pin", "to_pin"}, "a pin_map entry carries entry, from_pin, to_pin")
            _require(entry["entry"] in ("input", "output"), f"pin_map.entry {entry['entry']!r} must be input or output")
        return
    if op in ("copy_subgraph", "move_subgraph"):
        _require(not has_target, f"a {op} request addresses its graphs inside migration, so 'target' must be absent")
        selection = source.get("node_guids")
        _require(isinstance(selection, list) and selection, "migration.source.node_guids must select at least one node")
        _require(isinstance(migration.get("destination"), dict), "migration.destination must be an object")
        boundary = migration.get("boundary")
        _require(isinstance(boundary, list), "migration.boundary must be an array (empty when nothing crosses)")
        for entry in boundary:
            _require(set(entry) == {"from", "to"}, "a boundary entry carries from and to")
            for side in ("from", "to"):
                _require(
                    set(entry[side]) == {"node_guid", "pin"},
                    f"migration.boundary.{side} carries exactly node_guid and pin",
                )
        return
    if op == "prune_island":
        _require(not has_target, "a prune_island request addresses its graph inside migration, so 'target' must be absent")
        _require(isinstance(source.get("graph_ref"), dict), "migration.source.graph_ref must be an object")
        _require(isinstance(source.get("entry_node_guid"), str), "migration.source.entry_node_guid is required")
        _require("boundary" not in migration and "pin_map" not in migration, "prune_island carries neither boundary nor pin_map")
        if "approved_node_guids" in migration:
            _require(
                isinstance(migration["approved_node_guids"], list) and migration["approved_node_guids"],
                "an approved set is the caller's echo of the preview's removable list; it is never sent empty",
            )
        return
    raise ShapeError(f"migration.op {op!r} is not a published migration operation")


def validate_intent_fragment(fragment: dict) -> None:
    """Validate one checked-in request fragment against the published envelope shape."""
    _require(isinstance(fragment, dict), "a fixture fragment must be a JSON object")
    unknown = set(fragment) - FRAGMENT_FIELDS
    _require(not unknown, f"fragment has unknown field(s) {sorted(unknown)}")

    for flag in FLAG_FIELDS:
        if flag in fragment:
            _require(
                isinstance(fragment[flag], bool),
                f"'{flag}' must be a strict JSON boolean, never a number or string",
            )

    if "target" in fragment:
        target = fragment["target"]
        _require(isinstance(target, dict), "target must be an object")
        _require(
            set(target) <= {"graph_ref", "implementation"} and len(target) >= 1,
            "target must specify graph_ref or implementation",
        )
        if "implementation" in target:
            implementation = target["implementation"]
            _require(isinstance(implementation, dict), "target.implementation must be an object")
            _require(
                set(implementation) <= {"owner_class", "function_name", "call_kind"},
                "target.implementation has an unknown field",
            )

    nodes = fragment.get("nodes", [])
    _require(isinstance(nodes, list), "nodes must be an array")
    for node in nodes:
        _require(isinstance(node, dict), "node entries must be objects")
        unknown = set(node) - NODE_FIELDS
        _require(not unknown, f"node has unknown field(s) {sorted(unknown)}")
        client_id = node.get("client_id")
        _require(CLIENT_ID.match(client_id or "") is not None, f"node.client_id {client_id!r} is invalid")
        _require(client_id != "entry", "node.client_id 'entry' is reserved for the implementation entry")
        _require(node.get("node_class") in PUBLISHED_FAMILIES, f"node_class {node.get('node_class')!r} is not published")
        if "params" in node:
            _require(isinstance(node["params"], dict), f"node '{client_id}' params must be an object")
        if "defaults" in node:
            defaults = node["defaults"]
            _require(isinstance(defaults, dict), f"node '{client_id}' defaults must be an object")
            for pin_name, default in defaults.items():
                _validate_tagged_default(pin_name, default, f"node '{client_id}'")

    connections = fragment.get("connections", [])
    _require(isinstance(connections, list), "connections must be an array")
    declared = {node.get("client_id") for node in nodes}
    fed = set()
    for connection in connections:
        _require(isinstance(connection, dict), "connection entries must be objects")
        _require(set(connection) == {"from", "to"}, "a connection carries exactly from and to")
        for side in ("from", "to"):
            _validate_endpoint(connection[side], f"connection.{side}")
            identity = connection[side].get("client_id")
            if identity is not None:
                _require(identity in declared, f"connection.{side}.client_id '{identity}' is not a declared node")
        target = connection["to"]
        if "client_id" in target:
            fed.add((target["client_id"], target["pin"]))
    for node in nodes:
        for pin_name in node.get("defaults", {}):
            _require(
                (node["client_id"], pin_name) not in fed,
                f"node '{node['client_id']}' has a default and an edge on the same input '{pin_name}'",
            )

    if "migration" in fragment:
        migration = fragment["migration"]
        _require(isinstance(migration, dict), "migration must be an object")
        unknown = set(migration) - MIGRATION_FIELDS
        _require(not unknown, f"migration has unknown field(s) {sorted(unknown)}")
        _require(isinstance(migration.get("op"), str) and migration["op"], "migration.op is required")
        if "remove_shadowing_member" in migration:
            _require(
                isinstance(migration["remove_shadowing_member"], bool),
                "migration.remove_shadowing_member must be a strict JSON boolean",
            )
        for array_field in ("boundary", "pin_map", "approved_node_guids"):
            if array_field in migration:
                _require(isinstance(migration[array_field], list), f"migration.{array_field} must be an array")
        if migration["op"] in PUBLISHED_MIGRATION_OPS:
            for shell_field in ("nodes", "connections", "pin_updates"):
                _require(
                    fragment.get(shell_field, []) == [],
                    f"a migration request carries no authoring '{shell_field}' array",
                )
            _validate_migration_shell(fragment, migration)


def validate_no_fabricated_live_value(path: Path) -> list:
    """Assert a fixture invents no GUID/hash and return its declared ``<live: …>`` tokens."""
    text = path.read_text(encoding="utf-8")
    _require(GUID_LITERAL.search(text) is None, f"{path.name} carries a GUID literal")
    _require(HASH_LITERAL.search(text) is None, f"{path.name} carries a hash literal")
    tokens: list = []
    for json_path, value in _strings(json.loads(text)):
        for match in ANY_ANGLE_TOKEN.finditer(value):
            live = LIVE_TOKEN.fullmatch(match.group(0))
            _require(
                live is not None,
                f"{path.name}:{json_path} placeholder {match.group(0)!r} is not a declared <live: …> binding",
            )
            tokens.append(live.group(1))
    return tokens


def _negative_cases() -> list:
    negative_dir = EXAMPLES / "negative"
    return sorted(negative_dir.glob("*.json")) if negative_dir.is_dir() else []


class TypedBlueprintGuidanceTests(unittest.TestCase):
    def test_guide_separates_preview_apply_and_persistence(self):
        guide = (ROOT / "resources/typed-blueprint-authoring.md").read_text(encoding="utf-8")
        for heading in ("## Live contract", "## Preview", "## Apply", "## Persistence", "## Recovery"):
            with self.subTest(heading=heading):
                self.assertIn(heading, guide)
        self.assertIn("expected_validation_hash", guide)
        self.assertIn("graph.apply_patch", guide)
        self.assertIn("No blind retry", guide)

    def test_example_uses_edges_not_object_literal_node_references(self):
        intent = json.loads((ROOT / "examples/typed-blueprint-authoring/adapter-intent.json").read_text(encoding="utf-8"))
        self.assertIs(intent["dry_run"], True)
        self.assertIs(intent["save"], False)
        ids = [node["client_id"] for node in intent["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(node["node_class"] == "Self" for node in intent["nodes"]))
        self.assertTrue(any(node["node_class"] == "ConstructObject" for node in intent["nodes"]))
        for node in intent["nodes"]:
            for value in node.get("defaults", {}).values():
                self.assertIn("kind", value)
                self.assertNotIn("client_id", value)
                self.assertNotIn("node", value)
        self.assertNotIn("expected_fingerprint", intent)
        self.assertNotIn("expected_validation_hash", intent)
        # Self→Outer is an edge, never a default: the create node's outer input is addressed by its
        # engine PinName ("self"); "Outer" is only its Blueprint-facing friendly name.
        model = next(node for node in intent["nodes"] if node["node_class"] == "ConstructObject")
        wired_outer = [
            edge
            for edge in intent["connections"]
            if edge["to"]["client_id"] == model["client_id"] and edge["from"] == {"client_id": "self", "pin": "self"}
        ]
        self.assertEqual(len(wired_outer), 1, "the outer input must be wired from a Self node, never defaulted")
        self.assertNotIn("self", model.get("defaults", {}))

    def test_object_literal_defaults_are_rejected_by_the_shape_check(self):
        rejected = (
            {"Outer": {"node": "$self"}},
            {"Outer": {"client_id": "self"}},
            {"Outer": {"kind": "object", "path": "$self"}},
            {"Outer": {}},
        )
        for defaults in rejected:
            with self.subTest(defaults=defaults):
                node = {"client_id": "model", "node_class": "ConstructObject", "defaults": defaults}
                with self.assertRaises(ShapeError):
                    validate_intent_fragment({"nodes": [node], "connections": []})

    def test_adapter_intent_matches_the_published_intent_shape(self):
        intent = json.loads((EXAMPLES / "adapter-intent.json").read_text(encoding="utf-8"))
        validate_intent_fragment(intent)
        self.assertNotIn("target", intent)
        self.assertNotIn("patch_id", intent)
        self.assertNotIn("migration", intent)

    def test_checked_in_fixtures_carry_no_fabricated_live_value(self):
        fixtures = sorted(EXAMPLES.glob("*.json")) + _negative_cases()
        self.assertTrue(fixtures, "no fixtures found")
        for path in fixtures:
            with self.subTest(fixture=path.name):
                validate_no_fabricated_live_value(path)


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


# Guidance files that must never prescribe the removed legacy update batch again.
ROUTED_FILES = (
    "skills/cortex-blueprint/SKILL.md",
    "skills/cortex-umg/SKILL.md",
    "skills/cortex-bp-migrate/SKILL.md",
    "resources/blueprint-development.md",
    "resources/blueprint-patterns.md",
    "resources/ui-development.md",
    "resources/batch-pipeline-guide.md",
    "resources/mcp-tool-reference.md",
    "resources/bp-migration-executor.md",
    "resources/typed-blueprint-authoring.md",
    "README.md",
)

# A prescriptive legacy update call: `blueprint_compose(mode="update", …, nodes/connections=…)`.
LEGACY_UPDATE_CALLS = (
    re.compile(r"""blueprint_compose\([^()]*mode\s*=\s*["']update["'][^()]*nodes\s*=""", re.S),
    re.compile(r"""blueprint_compose\([^()]*mode\s*=\s*["']update["'][^()]*connections\s*=""", re.S),
    re.compile(r"""mode\s*=\s*["']update["'][^()]*pin_text_values""", re.S),
    re.compile(r"""blueprint_compose\([^()]*mode\s*=\s*["']update["'][^()]*graph_name\s*=""", re.S),
)

# The frozen contract facts the guide (and the routing files that lean on it) must state.
GUIDE_CONTRACT_NEEDLES = (
    ("mode='update' requires a 'patch'", "update mode without a patch is refused, not migrated by fallback"),
    ("MIGRATION_REQUIRED", "the refusal code for an update without a patch"),
    ("MIXED_UPDATE_CONTRACT", "the refusal code for legacy fields beside patch"),
    ("never coerced", "strict booleans are never coerced"),
    ("must be **absent**", "target is absent for the transfer and prune shells"),
    ("replayed_with_absent_source", "an accepted replay with an absent source is published"),
    ("prune_island", "the prune shell is published"),
    ("approved_node_guids", "the caller echoes the approved removable set"),
    ("omission marker", "the inventory is bounded"),
    ("No blind retry", "recovery never retries blindly"),
    ("blocked", "missing live support blocks instead of falling back"),
)


class TypedBlueprintRoutingTests(unittest.TestCase):
    def test_all_relevant_skills_link_the_single_guide(self):
        for path in ("skills/cortex-blueprint/SKILL.md", "skills/cortex-umg/SKILL.md", "skills/cortex-bp-migrate/SKILL.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("resources/typed-blueprint-authoring.md", text)

    def test_batch_guide_does_not_confuse_stop_with_rollback(self):
        text = (ROOT / "resources/batch-pipeline-guide.md").read_text(encoding="utf-8")
        self.assertIn("stop_on_error is not rollback", text)
        self.assertIn("graph.apply_patch", text)
        self.assertIn("not nestable", text)

    def test_no_affected_file_prescribes_the_removed_legacy_update_route(self):
        for path in ROUTED_FILES:
            text = _read(path)
            for pattern in LEGACY_UPDATE_CALLS:
                with self.subTest(path=path, pattern=pattern.pattern[:48]):
                    self.assertIsNone(pattern.search(text), f"{path} still prescribes the removed legacy update call")

    def test_update_route_guidance_names_the_guarded_patch(self):
        for path in (
            "skills/cortex-blueprint/SKILL.md",
            "resources/blueprint-development.md",
            "resources/batch-pipeline-guide.md",
            "resources/mcp-tool-reference.md",
        ):
            text = _read(path)
            with self.subTest(path=path):
                self.assertIn("graph.apply_patch", text)
                self.assertIn("patch=", text)

    def test_guide_states_the_frozen_contract_facts(self):
        guide = _read("resources/typed-blueprint-authoring.md")
        for needle, why in GUIDE_CONTRACT_NEEDLES:
            with self.subTest(needle=needle):
                self.assertIn(needle, guide, why)

    def test_widget_graph_authoring_is_routed_out_of_the_stop_on_error_batch(self):
        text = _read("skills/cortex-umg/SKILL.md")
        self.assertIn("typed-blueprint-authoring", text)
        self.assertIn("widget_compose", text, "new screens keep their own composite route")
        self.assertIn("set_widget_variable", text)
        self.assertIn("Widget Blueprint graph", text, "the widget-graph exception must be stated")
        exception = text.split("Widget Blueprint graph", 1)[1]
        self.assertIn(
            "typed-blueprint-authoring",
            exception[:1200],
            "the graph exception must name the guarded workflow instead of the stop-on-error batch",
        )

    def test_migration_guidance_blocks_bounded_operations_instead_of_substituting_cleanup(self):
        skill = _read("skills/cortex-bp-migrate/SKILL.md")
        executor = _read("resources/bp-migration-executor.md")
        for path, text in (("skills/cortex-bp-migrate/SKILL.md", skill), ("resources/bp-migration-executor.md", executor)):
            with self.subTest(path=path):
                self.assertIn("typed-blueprint-authoring", text)
                self.assertIn("replace_entry", text)
                self.assertIn("prune_island", text)
                self.assertIn("blocked", text.lower())
        self.assertIn("disconnect-plus-orphan", executor, "the raw cleanup substitute must be explicitly refused")

    def test_guide_is_reachable_from_the_readme(self):
        self.assertIn("typed-blueprint-authoring", _read("README.md"))


if __name__ == "__main__":
    unittest.main()
