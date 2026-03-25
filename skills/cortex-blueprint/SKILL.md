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
  → Launch `cortex-toolkit:blueprint-developer` agent with `max_turns: 25`

- **Review/Analyze**: User wants to understand or audit existing assets
  Examples: "review BP_Player", "check naming conventions", "audit complexity", "list all blueprints"
  → Launch `cortex-toolkit:blueprint-developer` agent with `max_turns: 15`

- **Debug**: User wants to trace or diagnose a problem
  Examples: "debug BP_Player", "why isn't this working", "trace execution", "investigate crash"
  → Launch `cortex-toolkit:blueprint-debugger` agent with `max_turns: 35`

- **Ambiguous** → Default to Review (read-only, safe)

## Agent Routing

| Mode | Agent | max_turns |
|------|-------|-----------|
| Create/Modify | cortex-toolkit:blueprint-developer | 25 |
| Review/Analyze | cortex-toolkit:blueprint-developer | 15 |
| Debug | cortex-toolkit:blueprint-debugger | 35 |

## Steps

### 1. Launch Agent

Use the Task tool with the appropriate `subagent_type` and `max_turns` for the detected mode.

**For Create/Modify**, structure the prompt as a mandatory pipeline directive:

```
Create the following Blueprint using the MANDATORY pipeline:

**Blueprint:** [name and type, e.g. BP_PlayerCharacter (Actor)]
**Path:** [e.g. /Game/Blueprints/]
**Variables:** [name, type, default value, category, exposed status]
**Functions:** [name, inputs, outputs]
**Graph:** [nodes and connections for BeginPlay, function graphs, etc.]

MANDATORY WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for node class names and pin conventions
2. Investigate existing Blueprints to avoid name collisions
3. Design your variables[], functions[], nodes[], and connections[] as a JSON spec
4a. NEW Blueprint → `blueprint_compose(name, path, ...)` as a SINGLE call
4b. MODIFYING EXISTING (2+ changes) → `blueprint_compose(mode="update", asset_path="...", nodes=[...], connections=[...])` as a SINGLE call

PROHIBITED:
- Never call `graph_add_node` or `graph_connect` individually N times for multi-node operations.
- Always batch 2+ node additions/connections into a single `blueprint_compose(mode="update")` call.
- Individual graph tools are only acceptable for a single isolated change (e.g., set one pin value, connect one existing wire).
```

**For Review/Analyze**, pass the review scope and focus:

```
Review the following Blueprint(s):

**Scope:** [specific Blueprint paths, or "all Blueprints in /Game/Blueprints/"]
**Concerns:** [naming, complexity, compilation, variable organization, best practices]

READ-ONLY MODE: Do NOT call list_blueprints, compile_blueprint, impact_analysis, or any write tools.
Permitted tools: blueprint_cmd(get_info), graph_cmd(list_graphs), graph_cmd(list_nodes), graph_cmd(get_node), reflect_cmd(query_class_context).

WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for project conventions
2. Use blueprint_cmd(get_info) to inspect relevant Blueprints — do NOT call list_blueprints
3. Check structure (naming, type appropriateness, parent class)
4. Analyze graphs in parallel: call graph_cmd(list_nodes) for all graphs simultaneously
5. Check variable organization (categories, exposure, naming)
6. Cross-reference against project conventions

Return findings grouped by severity: Errors, Warnings, Info.
```

**For Debug**, pass the investigation details:

```
Investigate the following Blueprint issue:

**Blueprint:** [asset path]
**Goal:** [execution trace / find function / explain behavior / diagnose crash]
**Starting point:** [specific node, event, or behavior to start from]

WORKFLOW:
1. Read `.cortex/domains/blueprints.md` for available tools and patterns
2. Use graph_search_nodes and connected_to to trace execution flow
3. Map the call chain and identify where behavior diverges from expectation
4. Report findings with node-level detail
```

### 2. Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user. For creates, include asset paths and stats (variable, function, node, connection counts, compilation status). For reviews, include findings grouped by severity. For debug, include the traced execution path and diagnosis.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For creates, warn the user that partially created assets may need cleanup.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the work may be incomplete.
