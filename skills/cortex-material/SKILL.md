---
name: cortex-material
description: Use when creating or reviewing materials, instances, parameter collections, or material graphs
---

# cortex-material

Creates and reviews materials, instances, and parameter collections using the Material Developer agent.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change something
  Examples: "create a material", "add a parameter to", "update the texture slot", "create an instance of"
  → Launch `material-developer` agent with `max_turns: 25`

- **Review/Analyze**: User wants to understand or audit existing assets
  Examples: "review materials in /Game/Materials", "check naming conventions", "audit material complexity", "list all instances"
  → Launch `material-developer` agent with `max_turns: 15`

- **Ambiguous** → Default to Review (read-only, safe)

## Agent Routing

| Mode | Agent | max_turns |
|------|-------|-----------|
| Create/Modify | material-developer | 25 |
| Review/Analyze | material-developer | 15 |

## Steps

### 1. Launch Material Developer Agent

Use the Task tool with `subagent_type: "cortex-toolkit:material-developer"` and the appropriate `max_turns` for the detected mode.

**For Create/Modify**, structure the prompt as a mandatory pipeline directive:

```
Create the following material using the MANDATORY pipeline:

**Material:** [name, e.g. M_PulsatingRed]
**Path:** [e.g. /Game/Materials/]
**Description:** [visual description of what the material should look like]
**Parameters to expose:** [list of ScalarParameter/VectorParameter names and defaults]
**Material instances:** [list of instances to derive, if any]

MANDATORY WORKFLOW:
1. Read `.cortex/domains/material.md` for pin conventions
2. Design your nodes[] and connections[] arrays as a JSON spec
3. Call `material_compose(name, path, nodes, connections)` as a SINGLE call
4. Create material instances if requested

PROHIBITED: Do NOT call `material_cmd` for `create_material`, `add_node`, `connect`, `set_node_property`, or `auto_layout` individually. These are ONLY for modifying existing materials. For new materials, you MUST use `material_compose` exclusively.
```

**For Review/Analyze**, pass the review scope and focus:
- Specific materials to review, or a path for full review
- Specific concerns (graph complexity, parameter usage, instance hierarchy, naming)

### 2. Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user. For creates, include created asset paths. For reviews, include findings grouped by severity.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it.

If the agent's response has no Status line (e.g., turn limit reached), treat as **partial** — summarize whatever was produced and warn the review or creation may be incomplete.
