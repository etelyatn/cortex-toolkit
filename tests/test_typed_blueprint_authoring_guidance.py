"""Guidance and fixture checks for the typed Blueprint authoring workflow.

Scope: this module proves toolkit guidance and checked-in JSON *shape* only. It never contacts the
Editor and never speaks to the MCP layer, so it cannot prove Unreal behaviour. In particular it does
**not** carry a catalog of supported families, migration operations, default tags, limits or
selectors: those are published by the live contract (``graph.get_authoring_context`` /
``graph.describe_node`` / ``core.get_operation_schema``, owned by
``Plugins/UnrealCortex/Source/CortexGraph``), and a value this check does not know about is validated
by that contract, not rejected here. Supported-value acceptance for the fixtures below is exercised
live by the consuming plugin scenario under an Editor lease.
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
    # The accepted tag values are published by the live contract (a tagged default is validated by
    # the native pin-defaults owner); this check only requires a non-empty tag and forbids an edge
    # hidden inside a default.
    _require(
        isinstance(kind, str) and kind,
        f"{context}.defaults['{pin_name}'] needs a non-empty 'kind' tag, got {kind!r}",
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
    """Apply the shell rules this check knows, keyed by the shells the contract publishes.

    An operation this check does not know is left to the live contract: it is not rejected here, so a
    newly published operation never invalidates a checked-in fixture (its acceptance is validated
    live). The rules below are structural facts about the known shells, not a supported-value list.
    """
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
    # An unknown operation is accepted structurally and validated live: this check cannot know which
    # operations a newer plugin publishes.


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
        node_class = node.get("node_class")
        _require(
            isinstance(node_class, str) and node_class,
            f"node '{client_id}' needs a node_class; the accepted families are published live",
        )
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

    def test_adapter_intent_matches_the_intent_shape(self):
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

# The shared guide owns the bounded prune workflow; routing surfaces carry a concise, consistent
# statement and link back rather than duplicating the algorithm.
BOUNDED_PRUNE_GUIDE_NEEDLES = (
    ("max_response_chars=40000", "the MCP response budget is explicit"),
    ("complete-or-refuse", "accepted previews are complete or refused"),
    ("approval_complete", "capacity refusals cannot be mistaken for approved inventories"),
    ("response_size_chars", "preview refusal reports the measured response size"),
    ("max_response_chars", "preview refusal reports the response budget"),
    ("removable_count", "preview refusal reports the removable count"),
    ("approved_count", "preview refusal reports the approved count"),
    ("prospective_apply_size_chars", "apply refusal reports prospective size"),
    ("refusal envelope", "the refusal itself is guaranteed to fit"),
    ("pre-mutation", "oversized apply is refused before mutation"),
    ("partition preview", "the first preview measures the full partition"),
    ("exact approved-set preview", "the caller-approved set is previewed exactly"),
    ("second preview token", "apply uses the exact-set preview token"),
    ("max_scanned_nodes", "native scan bounds remain distinct"),
    ("native traversal", "native scan bounds are not response capacity"),
    ("mutation approval", "prune approval is never generically paginated"),
    ("regardless of rollback settings", "graph patches are rejected from every Core batch"),
    ("one-shot", "mutation dispatch is never blindly retried"),
    ("Stop and reconcile", "ambiguous outcomes require readback reconciliation"),
    ("lossless large-island inventory retrieval remains unsupported", "only lossless large-inventory retrieval is deferred"),
)

ROUTED_PRUNE_SUMMARY_NEEDLES = (
    ("bounded complete-or-refuse", "the implemented boundary is described"),
    ("oversized apply is refused before mutation", "apply refusal happens before mutation"),
    ("only lossless large-island inventory retrieval remains unsupported", "only lossless retrieval remains deferred"),
)


class TypedBlueprintRoutingTests(unittest.TestCase):
    def test_all_relevant_skills_link_the_single_guide(self):
        for path in ("skills/cortex-blueprint/SKILL.md", "skills/cortex-umg/SKILL.md", "skills/cortex-bp-migrate/SKILL.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("resources/typed-blueprint-authoring.md", text)

    def test_batch_guide_rejects_graph_patch_in_every_batch(self):
        text = " ".join(_read("resources/batch-pipeline-guide.md").split()).casefold()
        self.assertIn("stop_on_error is not rollback", text)
        self.assertIn("graph.apply_patch", text)
        self.assertIn("every `core_cmd(batch_query)`", text)
        self.assertIn("regardless of rollback settings", text)

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

    def test_guide_publishes_the_bounded_prune_contract_and_stop_rule(self):
        guide = " ".join(_read("resources/typed-blueprint-authoring.md").split())
        for needle, why in BOUNDED_PRUNE_GUIDE_NEEDLES:
            with self.subTest(needle=needle):
                self.assertIn(needle.casefold(), guide.casefold(), why)

    def test_every_prune_routing_resource_describes_bounded_prune_and_deferred_retrieval(self):
        paths = (
            "examples/typed-blueprint-authoring/README.md",
            "resources/bp-migration-executor.md",
            "resources/mcp-tool-reference.md",
            "skills/cortex-bp-migrate/SKILL.md",
        )
        for path in paths:
            text = " ".join(_read(path).split())
            with self.subTest(path=path):
                self.assertIn(
                    "https://github.com/etelyatn/CortexSandbox/issues/102",
                    text,
                    "the bounded-response issue remains linked wherever prune is routed",
                )
                for needle, why in ROUTED_PRUNE_SUMMARY_NEEDLES:
                    with self.subTest(needle=needle):
                        self.assertIn(needle.casefold(), text.casefold(), why)

    def test_routed_prune_guidance_does_not_call_bounded_responses_unsupported(self):
        paths = (
            "resources/typed-blueprint-authoring.md",
            "examples/typed-blueprint-authoring/README.md",
        )
        obsolete_claims = (
            "large-island prune is unsupported at this candidate",
            "unsupported large-island case above",
        )
        for path in paths:
            text = " ".join(_read(path).split()).casefold()
            with self.subTest(path=path):
                for claim in obsolete_claims:
                    self.assertNotIn(claim, text)
        guide = " ".join(_read("resources/typed-blueprint-authoring.md").split()).casefold()
        self.assertIn("pre-mutation refusal applies", guide)
        self.assertIn("unexpected oversized post-apply response", guide)
        readme = " ".join(_read("examples/typed-blueprint-authoring/README.md").split()).casefold()
        self.assertIn("bounded complete-or-refuse mcp prune route is implemented", readme)
        self.assertIn("oversized apply is refused before mutation", readme)

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



    def test_composite_example_uses_discovered_target_and_complete_endpoints(self):
        patterns = _read("resources/blueprint-patterns.md")
        section = patterns.split("**Authoring inside a composite**", 1)[1].split("### Review Blueprint", 1)[0]
        example = section.split("```python", 1)[1].split("```", 1)[0]

        self.assertIn(
            'asset_path = "/Game/Blueprints/BP_CompositeActor.BP_CompositeActor"',
            example,
            "asset_path uses the canonical Blueprint object path",
        )
        self.assertIn('authoring_context = graph_cmd(command="get_authoring_context"', example)
        self.assertIn('"graph_name": root_choice["graph_name"]', example)
        self.assertIn("root_choice = next(", example)
        self.assertIn(
            'if choice["graph_kind"] == "ubergraph" and not choice.get("subgraph_path")',
            example,
        )
        self.assertIn("composite_choice = next(", example)
        self.assertIn(
            'choice for choice in authoring_context["graph_choices"] if choice.get("subgraph_path")',
            example,
            "the target choice must come from the live context",
        )
        for field in ("graph_guid", "graph_kind", "subgraph_path"):
            self.assertIn(f'"{field}": composite_choice["{field}"]', example)
        self.assertIn('"target": {"graph_ref": graph_ref}', example)
        self.assertIn('composite_graph = graph_cmd(command="get_subgraph"', example)
        calls = []
        graph_choices = [
            {
                "graph_guid": "root-guid",
                "graph_kind": "ubergraph",
                "graph_name": "EventGraph",
                "subgraph_path": "",
            },
            {
                "graph_guid": "composite-guid",
                "graph_kind": "composite",
                "graph_name": "MyComposite",
                "subgraph_path": "MyComposite",
            },
        ]
        composite_graph = {
            "nodes": [
                {
                    "node_guid": "tunnel-exit-guid",
                    "is_tunnel_boundary": True,
                    "pins": [{"name": "execute", "direction": "input", "type": "exec"}],
                },
                {
                    "node_guid": "tunnel-entry-guid",
                    "is_tunnel_boundary": True,
                    "pins": [{"name": "execute", "direction": "output", "type": "exec"}],
                },
            ],
        }

        def graph_cmd(command, params):
            calls.append((command, params))
            if command == "get_authoring_context":
                return {"fingerprint": "fixture-fingerprint", "graph_choices": graph_choices}
            if command == "get_subgraph":
                return composite_graph
            return {}

        exec(
            compile(example, "blueprint-patterns-composite-example", "exec"),
            {"blueprint_compose": lambda **params: None, "graph_cmd": graph_cmd},
        )
        applied = next(params for command, params in calls if command == "apply_patch")
        self.assertEqual(
            applied["connections"][0]["from"],
            {"node_guid": "tunnel-entry-guid", "pin": "execute"},
            "the example must use the entry tunnel GUID and paired pin read from the subgraph",
        )
        self.assertEqual(
            applied["connections"][0]["to"],
            {"client_id": "print_msg", "pin": "execute"},
        )
        subgraph_request = next(params for command, params in calls if command == "get_subgraph")
        self.assertIs(subgraph_request.get("compact"), False, "include hidden boundary pins in readback")

    def test_guide_is_reachable_from_the_readme(self):
        self.assertIn("typed-blueprint-authoring", _read("README.md"))



def _fixture(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def _negative(name: str) -> dict:
    return json.loads((EXAMPLES / "negative" / name).read_text(encoding="utf-8"))


class TypedBlueprintFixtureTests(unittest.TestCase):
    def test_p1_migration_fixtures_match_their_shell_shapes(self):
        for name, op in (
            ("replace-entry-intent.json", "replace_entry"),
            ("copy-subgraph-intent.json", "copy_subgraph"),
            ("move-subgraph-intent.json", "move_subgraph"),
            ("prune-island-intent.json", "prune_island"),
        ):
            with self.subTest(fixture=name):
                fragment = _fixture(name)
                validate_intent_fragment(fragment)
                self.assertEqual(fragment["migration"]["op"], op)
                self.assertIs(fragment["dry_run"], True)
                self.assertIs(fragment["save"], False)
                if op in ("copy_subgraph", "move_subgraph", "prune_island"):
                    self.assertNotIn("target", fragment)
                else:
                    self.assertIn("implementation", fragment["target"])

    def test_the_check_accepts_values_only_the_live_contract_knows(self):
        """A published value this check does not know must not invalidate a checked-in fixture."""
        future = {
            "nodes": [
                {"client_id": "later", "node_class": "SomeFutureFamily",
                 "defaults": {"Value": {"kind": "some_future_tag"}}},
            ],
            "connections": [],
        }
        validate_intent_fragment(future)
        validate_intent_fragment(
            {
                "migration": {"op": "some_future_operation", "source": {"graph_ref": {"graph_guid": "<live: graph>"}}},
                "nodes": [],
                "connections": [],
                "pin_updates": [],
            }
        )
        readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")
        self.assertIn("accepted live", readme, "the fixtures must say where supported values are accepted")

    def test_transfer_boundary_refusals_use_the_engine_type_mismatch_code(self):
        descriptor = _negative("expanded-boundary-pin.json")
        self.assertEqual(
            descriptor["expected"]["code"],
            "TYPE_MISMATCH",
            "the transfer planner returns TYPE_MISMATCH for a boundary pin, not PIN_TYPE_MISMATCH",
        )
        guide = _read("resources/typed-blueprint-authoring.md")
        self.assertIn("| `TYPE_MISMATCH` |", guide, "the guide must document the real code")
        boundary_row = re.search(r"^\| `TYPE_MISMATCH` \|.*$", guide, re.M)
        self.assertIn("boundary", boundary_row.group(0))

    def test_scan_budget_exhaustion_is_documented_per_shell(self):
        guide = _read("resources/typed-blueprint-authoring.md")
        limit_row = re.search(r"^\| `LIMIT_EXCEEDED` \|.*$", guide, re.M)
        self.assertIsNotNone(limit_row)
        # A non-prune shell reports its graph-wide scan exhaustion as the budget refusal...
        self.assertIn("scan", limit_row.group(0))
        self.assertIn("scanned_nodes", limit_row.group(0))
        # ... while the prune shell reports the same exhaustion under INVALID_OPERATION.
        invalid_row = re.search(r"^\| `INVALID_OPERATION` \|.*$", guide, re.M)
        self.assertIsNotNone(invalid_row)
        self.assertIn("scan", invalid_row.group(0))
        self.assertIn("complete=false", invalid_row.group(0))
        pin_row = re.search(r"^\| `PIN_TYPE_MISMATCH` \|.*$", guide, re.M)
        self.assertIsNotNone(pin_row)
        self.assertNotIn("expanded", pin_row.group(0))
        self.assertNotIn("boundary", pin_row.group(0))

    def test_policy_verdict_is_scoped_to_the_profile_wrapper(self):
        guide = _read("resources/typed-blueprint-authoring.md")
        self.assertIn("carries no policy verdict", guide, "core.get_operation_schema must not be described as policy-bearing")
        paragraph = re.search(r"^Obtain `core\.get_operation_schema`.*?(?=\n\n)", guide, re.M | re.S)
        self.assertIsNotNone(paragraph)
        self.assertIn("`profile_operation_schema` reports", paragraph.group(0))

    def test_transfer_fixtures_map_every_crossing_edge_with_a_pin_pair(self):
        for name in ("copy-subgraph-intent.json", "move-subgraph-intent.json"):
            with self.subTest(fixture=name):
                fragment = _fixture(name)
                boundary = fragment["migration"]["boundary"]
                self.assertTrue(boundary, "a transfer with crossing edges must publish its boundary mappings")
                for entry in boundary:
                    for side in ("from", "to"):
                        endpoint = entry[side]
                        self.assertEqual(set(endpoint), {"node_guid", "pin"})
                        self.assertTrue(LIVE_TOKEN.search(endpoint["node_guid"]), "identity comes from a read")
                        self.assertTrue(LIVE_TOKEN.search(endpoint["pin"]), "the pin name comes from describe_node")

    def test_prune_apply_echoes_the_approved_preview_partition(self):
        preview = _fixture("prune-island-intent.json")
        apply = _fixture("prune-island-apply.json")
        validate_intent_fragment(apply)
        self.assertEqual(apply["migration"]["op"], "prune_island")
        self.assertEqual(apply["migration"]["source"], preview["migration"]["source"])
        self.assertNotIn("approved_node_guids", preview["migration"], "the preview publishes the partition")
        approved = apply["migration"]["approved_node_guids"]
        self.assertTrue(approved, "an approved set is never empty")
        self.assertTrue(all(LIVE_TOKEN.search(value) for value in approved), "the set comes from the preview")
        self.assertIs(apply["dry_run"], False)
        self.assertIn("expected_validation_hash", apply)

    def test_apply_overlay_matches_the_preview_intent(self):
        preview = _fixture("adapter-intent.json")
        overlay = _fixture("adapter-apply.json")
        self.assertEqual(set(overlay), {"dry_run", "expected_validation_hash"}, "the apply step changes only these two")
        self.assertIs(overlay["dry_run"], False)
        request = {**preview, **overlay}
        validate_intent_fragment(request)
        self.assertIs(request["dry_run"], False)
        self.assertTrue(LIVE_TOKEN.search(request["expected_validation_hash"]))
        self.assertEqual(request["nodes"], preview["nodes"], "the applied intent is the previewed intent")

    def test_negative_fixtures_are_traceable_and_live_only_ones_are_named(self):
        guide = _read("resources/typed-blueprint-authoring.md")
        readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")
        cases = _negative_cases()
        self.assertTrue(cases, "the refused requests must be checked in")
        self.assertGreaterEqual(len(cases), 6)
        for path in cases:
            descriptor = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(case=path.name):
                self.assertEqual(
                    set(descriptor), {"case", "surface", "call", "request", "expected", "live_only"}
                )
                self.assertIn(descriptor["surface"], {"facade", "native"})
                self.assertTrue(descriptor["expected"]["code"])
                self.assertIn(
                    descriptor["expected"]["code"],
                    guide,
                    "a refused code must be documented in the guide",
                )
                if descriptor["live_only"]:
                    self.assertEqual(
                        descriptor["expected"]["enforced_by"],
                        "live",
                        "a live-only case has no static enforcer to name",
                    )
                    self.assertIn(descriptor["case"], readme, "live-only cases must be declared in the README")
                else:
                    self.assertNotEqual(descriptor["expected"]["enforced_by"], "live")
                if descriptor["surface"] == "native":
                    validate_intent_fragment(descriptor["request"])

    def test_every_live_token_is_declared_in_the_readme(self):
        readme = (EXAMPLES / "README.md").read_text(encoding="utf-8")
        tokens = []
        for path in sorted(EXAMPLES.glob("*.json")) + _negative_cases():
            tokens.extend(validate_no_fabricated_live_value(path))
        self.assertTrue(tokens, "the fixtures must declare what the run supplies")
        for token in sorted(set(tokens)):
            with self.subTest(token=token):
                self.assertIn(token, readme, "every live token must be declared in the fixtures README")


if __name__ == "__main__":
    unittest.main()
