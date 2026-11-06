---
name: cortex-statetree
description: Use when creating, updating, reviewing, validating, compiling, inspecting, or migrating Blueprint nodes of Unreal StateTree assets through UnrealCortex
---

# cortex-statetree

Creates, updates, reviews, validates, and compiles StateTree assets following the `resources/statetree-development.md` guide.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change a StateTree asset
  Examples: "create a StateTree", "add a Patrol state", "wire a transition", "compile after structural edits"
  → Follow the `resources/statetree-development.md` guide.

- **Review/Analyze**: User wants to inspect structure or understand an existing StateTree without mutating it
  Examples: "review ST_Guard", "dump this StateTree", "check transitions", "check StateTree structure"
  → Follow the `resources/statetree-development.md` guide.

- **Validate/Compile**: User wants to run mutating validation fixups or compile an existing StateTree
  Examples: "validate this StateTree", "run validation fixups", "compile ST_Guard"
  → Follow the `resources/statetree-development.md` guide.

- **Node migration**: User wants to replace Blueprint StateTree tasks/conditions with native ones while keeping their bindings
  Examples: "replace STT_Wait with the native task", "migrate the Blueprint conditions in ST_Tutorial to C++", "show the bindings of this task"
  → Follow the "Node Migration Pipeline" in `resources/statetree-development.md` (UE 5.8+; the native type must already exist in C++).

- **Ambiguous** → Default to Review (read-only, safe)

## Routing

| Mode | Guide |
|------|-------|
| Create/Modify | `statetree-development` |
| Review/Analyze | `statetree-development` |
| Validate/Compile | `statetree-development` |
| Node migration | `statetree-development` ("Node Migration Pipeline"), `cpp-migration` ("StateTree Task and AnimBP Binding Migration") |

## Steps

### 1. Execute the Workflow

Read the guide listed in the routing table for the detected mode, then execute its workflow directly in this conversation using the MCP tools it references.

**For Create/Modify**, execute the mandatory pipeline directive:

```text
Create or update the following StateTree using the MANDATORY pipeline:

**StateTree:** [asset path, e.g. /Game/AI/StateTrees/ST_Guard]
**Mode:** [create or update]
**Schema class:** [required for create, e.g. /Script/GameplayStateTreeModule.StateTreeComponentSchema or a verified project-specific UStateTreeSchema subclass]
**Prefetched state:** [embed the main-thread prefetched_state block here before proceeding]
**States:** [state names, hierarchy, type, tags, enabled state, selection behavior]
**Transitions:** [source, target, trigger, event tag, priority]
**Validation:** [check only, validate, compile, save]

MANDATORY WORKFLOW:
1. Read `.cortex/domains/statetree.md` if present, then read `cortex-toolkit/resources/statetree-patterns.md`
2. Use `prefetched_state` first. Do not re-fetch the same baseline if it is already present.
3. For new assets with 2+ states or transitions, design a JSON spec and call `statetree_compose(...)` once.
4. For existing assets with 2+ changes, prefer `statetree_compose(mode="update", asset_path="...", expected_fingerprint=...)`.
5. For one isolated existing-asset change, use `statetree_cmd(command="...", params={...})`.
6. Pass `expected_fingerprint` on every mutation that touches a prefetched StateTree.
7. Run `check_structure` after structural edits and `compile` only when explicitly requested.

PROHIBITED:
- Do not edit `.uasset` files directly.
- Do not write Unreal Python scripts as a workaround for StateTree mutation.
- Do not create GameplayTags implicitly. Invalid tags must be reported.
- Do not claim node/task/condition/binding authoring support beyond `replace_node` (a Blueprint-to-native swap that keeps node IDs and bindings but never ports logic). Everything else is structure-level only.
```

**For Review/Analyze**, pass the review scope and keep it read-only:

```text
Review the following StateTree(s):

**Scope:** [specific StateTree asset paths, or path prefix such as /Game/AI/StateTrees]
**Concerns:** [structure, transitions, tags, check_structure findings, compile readiness]
**Prefetched state:** [embed the main-thread prefetched_state block here before proceeding]

READ-ONLY MODE:
Permitted tools: statetree_cmd(list_assets), statetree_cmd(dump_tree), statetree_cmd(get_state), statetree_cmd(check_structure), statetree_cmd(get_node_bindings), statetree_cmd(get_runtime_state), get_dependencies, get_referencers.
Do not call validate_asset, compile, add_state, remove_state, rename_state, move_state, set_state_properties, add_transition, remove_transition, set_transition_properties, replace_node, create_asset, duplicate_asset, or delete_asset.

WORKFLOW:
1. Read `.cortex/domains/statetree.md` if present, then read `cortex-toolkit/resources/statetree-patterns.md`
2. Use prefetched state first
3. Inspect target assets with `dump_tree`
4. Run `check_structure`
5. Report findings grouped by Errors, Warnings, Info
```

**For Validate/Compile**, pass the mutation scope explicitly:

```text
Run validation fixups or compile for the following StateTree:

**StateTree:** [asset path, e.g. /Game/AI/StateTrees/ST_Guard]
**Operation:** [validate_asset, compile, or both]
**Prefetched state:** [embed the main-thread prefetched_state block here before proceeding]
**Expected fingerprint:** [required fingerprint from prefetched_state or a fresh dump_tree/check_structure result]
**Save:** [true or false]

MUTATING MODE:
1. Read `.cortex/domains/statetree.md` if present, then read `cortex-toolkit/resources/statetree-patterns.md`
2. Use `prefetched_state` first. Do not re-fetch the same baseline if it is already present.
3. Pass `expected_fingerprint` on every mutating call.
4. Run only the requested `validate_asset` and/or `compile` operations.
5. Report structured diagnostics and the latest returned fingerprint.
```

**For Node migration**, pass the unit explicitly:

```text
Replace Blueprint StateTree node(s) by native ones:

**StateTree:** [asset path]
**Blueprint class or node_id:** [class path (every node of the class) or one editor node ID]
**Native type:** [new_node_struct path, or new_node_class path (wrapper kept); must already be built]
**property_map:** [OldName -> NewName, or none]
**Expected fingerprint:** [fingerprint a StateTree command just returned (it carries editor_content_hash)]
**Save:** [false until PIE verification]

MUTATING MODE:
1. Read `resources/statetree-development.md` ("Node Migration Pipeline") and `.cortex/domains/statetree.md` if present.
2. `get_node_bindings` for the nodes; record node_ids, bindings, `whole_tree_binding_count`.
3. `replace_node` with `dry_run:true`; read `property_plan`, `bindings.remapped`, `bindings.unresolved`, `required_acknowledgment`. Stop on any unresolved binding.
4. Acknowledge data loss (`acknowledged_losses`) only with the user's approval; then apply with `compile:true`.
5. Run `compile`, re-read `get_node_bindings` (counts equal), verify in PIE with `get_runtime_state` and the `LogStateTree` log, then save.
6. On `rollback_status` other than `restored` (asset quarantined) stop and report; do not retry.

PROHIBITED: changing node types by hand, claiming the Blueprint logic was ported, using `replace_node` on UE < 5.8 (`NOT_AVAILABLE`).
```

### 2. Reporting Results

Report results to the user with a completion status:

- **completed** — present created or modified asset paths, validation state, compile result, and latest fingerprint.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it.

If the work is interrupted mid-execution, treat it as **partial** and summarize the usable results without claiming completion.
