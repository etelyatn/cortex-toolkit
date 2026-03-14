---
name: cortex-material-create
description: Use when creating new materials, material instances, parameter collections, or building material graphs from a spec or description
---

# Material Create

Creates materials, instances, and parameter collections from specifications using the Material Designer agent.

## Steps

### 1. Launch Material Designer Agent

<!-- Turn budget: CREATE tier (max_turns=25) — design + execute + verify pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:material-developer"` and `max_turns: 25` to delegate material creation.

**IMPORTANT: Structure the prompt as a mandatory pipeline directive.** Do NOT pass a free-form natural language description. Instead, pass a structured prompt that forces the agent to use the composite tool:

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

### 2. Agent Workflow (runs in background)

The Material Designer agent will:
1. Read `.cortex/domains/material.md` for project material conventions
2. Design the full expression graph spec (nodes + connections as JSON arrays)
3. **Call `material_compose` once** — atomic creation of material + nodes + connections in single batch
4. Create material instances if requested

**Enforcement:**
- The agent prompt contains a PROHIBITED tools list — it will not use individual graph tools for new materials
- The composite tool executes atomically: all-or-nothing with auto-cleanup on failure
- One `material_compose` call replaces what would be 20-60 individual tool calls

### 3. Review Agent Results

The agent returns:
- Created asset paths (materials, instances, collections)
- Expression graph summary (node count, connections)
- Parameters exposed and their defaults
- Instance overrides applied
- Any compilation issues

If the agent encounters issues (invalid expression class, missing parent material, connection type mismatch), it will report them for you to address.

## Why Use the Agent?

- **Single tool call** — one `material_compose` instead of dozens of individual calls
- **Context-aware design** — agent follows project material conventions and naming
- **Graph planning** — designs proper expression graphs automatically
- **Reliability** — atomic operations with validation and auto-cleanup
- **Expandable details** — use Ctrl+O to see build steps if needed

## Troubleshooting

**Agent makes individual tool calls instead of using composite:**
- The structured prompt above should prevent this. If it still happens, check that the agent prompt (`material-developer.md`) has the PROHIBITED section intact.

**"Pin not found" or connection errors:**
- Pin names must match exact conventions (outputs by index `"0"`, inputs by name `"A"`, `"Input"`, etc.)
- Solution: Use `get_material_node_pins` to discover actual pin names, or check `.cortex/domains/material.md`

**Material created but parameters missing:**
- VectorParameter DefaultValue requires FLinearColor support (fixed in recent update)
- Solution: Verify `set_node_property` supports FStructProperty for [R,G,B,A] arrays

**Multiple material variants created:**
- Agent may be retrying failed operations with slightly different names
- Solution: Ensure composite tool is used (atomic all-or-nothing operations prevent retries)

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present created artifacts to the user. Optionally verify key assets exist with a single search_assets call.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. The user may need to clean up partially created assets.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and warn that assets may be incomplete.
