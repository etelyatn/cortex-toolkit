---
name: cortex-statetree
description: Use when creating, updating, reviewing, validating, compiling, or inspecting Unreal StateTree assets through UnrealCortex
---

# cortex-statetree

Creates, updates, reviews, validates, and compiles StateTree assets using the StateTree Developer agent.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change a StateTree asset
  Examples: "create a StateTree", "add a Patrol state", "wire a transition", "compile this StateTree"
  → Launch `cortex-toolkit:statetree-developer` agent with `max_turns: 25`

- **Review/Analyze**: User wants to inspect structure, validate, or understand an existing StateTree
  Examples: "review ST_Guard", "dump this StateTree", "check transitions", "validate StateTree structure"
  → Launch `cortex-toolkit:statetree-developer` agent with `max_turns: 15`

- **Ambiguous** → Default to Review (read-only, safe)

## Agent Routing

| Mode | Agent | max_turns |
|------|-------|-----------|
| Create/Modify | cortex-toolkit:statetree-developer | 25 |
| Review/Analyze | cortex-toolkit:statetree-developer | 15 |

## Steps

### 1. Launch StateTree Developer Agent

Use the Task tool with `subagent_type: "cortex-toolkit:statetree-developer"` and the appropriate `max_turns` for the detected mode.

**For Create/Modify**, structure the prompt as a mandatory pipeline directive:

```text
Create or update the following StateTree using the MANDATORY pipeline:

**StateTree:** [asset path, e.g. /Game/AI/StateTrees/ST_Guard]
**Mode:** [create or update]
**Schema class:** [required for create, e.g. /Script/GameplayStateTreeModule.StateTreeComponentSchema or a verified project-specific UStateTreeSchema subclass]
**Prefetched state:** [embed the main-thread prefetched_state block here before launching]
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
- Do not claim node/task/condition/binding authoring support. The shipped slice is structure-level only.
```

**For Review/Analyze**, pass the review scope and keep it read-only:

```text
Review the following StateTree(s):

**Scope:** [specific StateTree asset paths, or path prefix such as /Game/AI/StateTrees]
**Concerns:** [structure, transitions, tags, validation, compile readiness]
**Prefetched state:** [embed the main-thread prefetched_state block here before launching]

READ-ONLY MODE:
Permitted tools: statetree_cmd(list_assets), statetree_cmd(dump_tree), statetree_cmd(get_state), statetree_cmd(check_structure), get_dependencies, get_referencers.
Do not call validate_asset, compile, add_state, remove_state, rename_state, move_state, set_state_properties, add_transition, remove_transition, set_transition_properties, create_asset, duplicate_asset, or delete_asset.

WORKFLOW:
1. Read `.cortex/domains/statetree.md` if present, then read `cortex-toolkit/resources/statetree-patterns.md`
2. Use prefetched state first
3. Inspect target assets with `dump_tree`
4. Run `check_structure`
5. Report findings grouped by Errors, Warnings, Info
```

### 2. Handling Agent Results

If the agent's response includes a **Status** line:

- **completed** — present created or modified asset paths, validation state, compile result, and latest fingerprint.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it.

If the agent's response has no Status line, treat it as **partial** and summarize the usable results without claiming completion.
