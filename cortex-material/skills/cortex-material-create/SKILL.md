---
name: cortex-material-create
description: Use when creating new materials, material instances, parameter collections, or building material graphs from a spec or description
---

# Material Create

Creates materials, instances, and parameter collections from specifications using the Material Designer agent.

## Steps

### 1. Launch Material Designer Agent

Use the Task tool with `subagent_type: "cortex-material:material-developer"` to delegate material creation.

Pass the full specification including:
- Material type (opaque PBR, masked, emissive, transparent)
- Graph structure (expression nodes, connections to material outputs)
- Parameters to expose (scalars, vectors, textures, static switches)
- Material instances to derive (parent, parameter overrides)
- Parameter collections (shared parameters across materials)

Example prompts:
- "Create M_Master_PBR with BaseColor, Normal, Roughness, Metallic texture parameters and a tint color"
- "Create MI_BrickWall from M_Master_PBR with brick textures and roughness 0.85"
- "Create a masked foliage material with subsurface color and wind animation"
- "Create MPC_Environment with TimeOfDay scalar and SunColor vector parameters"
- "Build the expression graph for M_Water with panning normal maps and depth fade"

### 2. Agent Workflow (runs in background)

The Material Designer agent will:
1. Read `.cortex/domains/material.md` for project material conventions
2. Identify parent materials and existing assets
3. Plan the expression graph (nodes, connections, parameters)
4. Create the material or instance asset
5. Add expression nodes and wire connections (for base materials)
6. Set parameter values and overrides (for instances)
7. Configure parameter collections if specified

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns:
- Created asset paths (materials, instances, collections)
- Expression graph summary (node count, connections)
- Parameters exposed and their defaults
- Instance overrides applied
- Any compilation issues

If the agent encounters issues (invalid expression class, missing parent material, connection type mismatch), it will report them for you to address.

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware design** — agent follows project material conventions and naming
- **Graph planning** — designs proper expression graphs automatically
- **Expandable details** — use Ctrl+O to see build steps if needed
