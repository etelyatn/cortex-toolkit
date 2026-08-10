---
name: cortex-blueprint
description: Use when creating, modifying, reviewing, or debugging Blueprints — structure, graphs, variables, functions, best practices
---

# cortex-blueprint

Creates, modifies, reviews, and debugs Blueprint assets using the Blueprint Developer and Blueprint Debugger agents.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change something
  Examples: "create a blueprint", "add a variable to", "wire up BeginPlay", "add a component"
  → Dispatch the blueprint-developer agent with a 25-turn budget.

- **Review/Analyze**: User wants to understand or audit existing assets
  Examples: "review BP_Player", "check naming conventions", "audit complexity", "list all blueprints"
  → Dispatch the blueprint-developer agent with a 15-turn budget.

- **Debug**: User wants to trace or diagnose a problem
  Examples: "debug BP_Player", "why isn't this working", "trace execution", "investigate crash"
  → Dispatch the blueprint-debugger agent with a 35-turn budget.

- **Ambiguous** → Default to Review (read-only, safe)

## Agent Routing

| Mode | Agent | Turn budget |
|------|-------|-----------|
| Create/Modify | cortex-toolkit:blueprint-developer | 25 |
| Review/Analyze | cortex-toolkit:blueprint-developer | 15 |
| Debug | cortex-toolkit:blueprint-debugger | 35 |

## Steps

### 1. Launch Agent

Dispatch the agent listed in the routing table above with the turn budget for the detected mode.

**For Create/Modify**, structure the prompt as a mandatory pipeline directive:

```
Create the following Blueprint using the MANDATORY pipeline:

**Blueprint:** [name and type, e.g. BP_PlayerCharacter (Actor)]
**Path:** [e.g. `/Game/Blueprints/` or a project-owned plugin root such as `/InventoryPlugin/Blueprints/`]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before launching]
**Variables:** [name, type, default value, category, exposed status]
**Functions:** [name, inputs, outputs]
**Graph:** [nodes and connections for BeginPlay, function graphs, etc.]

MANDATORY WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for node class names and pin conventions
2. Use `prefetched_state` first. Do not re-fetch the same baseline if it is already present.
3. Investigate existing Blueprints to avoid name collisions only when `prefetched_state` does not already answer the question
4. Issue independent read calls in parallel
5. Pass `expected_fingerprint` on every mutation that touches a prefetched asset
6. Design your variables[], functions[], nodes[], and connections[] as a JSON spec
7a. NEW Blueprint → `blueprint_compose(name, path, ...)` as a SINGLE call
7b. MODIFYING EXISTING (2+ changes) → `blueprint_compose(mode="update", asset_path="...", nodes=[...], connections=[...])` as a SINGLE call

PROHIBITED:
- Never call `graph_add_node` or `graph_connect` individually N times for multi-node operations.
- Always batch 2+ node additions/connections into a single `blueprint_compose(mode="update")` call.
- Individual graph tools are only acceptable for a single isolated change (e.g., set one pin value, connect one existing wire).
```

**For Review/Analyze**, pass the review scope and focus:

```
Review the following Blueprint(s):

**Scope:** [specific Blueprint paths, or "all Blueprints in `/Game/Blueprints/` or a project-owned plugin Blueprint root"]
**Concerns:** [naming, complexity, compilation, variable organization, best practices]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before launching]

READ-ONLY MODE: Do NOT call list_blueprints, `blueprint_cmd(command="compile", params={...})`, impact_analysis, or any write tools.
Permitted tools: blueprint_cmd(get_info), graph_cmd(list_graphs), graph_cmd(get_subgraph), graph_cmd(trace_exec), graph_cmd(find_event_handler), graph_cmd(find_function_calls), reflect_cmd(query_class_context).

WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for project conventions
2. Use `prefetched_state` first; only fetch missing data
3. Use blueprint_cmd(get_info) to inspect relevant Blueprints — do NOT call list_blueprints
4. Check structure (naming, type appropriateness, parent class)
5. Analyze graphs in parallel: call graph_cmd(get_subgraph) or graph_cmd(find_event_handler) across the relevant graphs simultaneously
6. Check variable organization (categories, exposure, naming)
7. Cross-reference against project conventions

Note: graph trace/subgraph reads and blueprint_cmd(get_info) default to compact=true (positions, node_class, hidden pins, empty function inputs/outputs stripped). This is fine for review — pass compact=false only if you need position data or must distinguish inherited from blueprint-defined functions via the `source` field.

Return findings grouped by severity: Errors, Warnings, Info.
```

**For Debug**, pass the investigation details:

```
Investigate the following Blueprint issue:

**Blueprint:** [asset path]
**Goal:** [execution trace / find function / explain behavior / diagnose crash]
**Starting point:** [specific node, event, or behavior to start from]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before launching]

WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for available tools and patterns
2. Use `prefetched_state` first and avoid re-fetching identical baseline reads
3. Run independent graph reads in parallel
4. Use graph_search_nodes and connections to trace execution flow
5. Map the call chain and identify where behavior diverges from expectation
6. If you make a fix, include `expected_fingerprint` on every mutation
7. Report findings with node-level detail

Note: graph read commands default to compact=true — sufficient for execution tracing and branch analysis. Pass compact=false only if the bug involves visual layout (needs positions) or hidden pin wiring.
```

### 2. Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user. For creates, include asset paths and stats (variable, function, node, connection counts, compilation status). For reviews, include findings grouped by severity. For debug, include the traced execution path and diagnosis.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For creates, warn the user that partially created assets may need cleanup.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the work may be incomplete.
