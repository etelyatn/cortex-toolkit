---
name: cortex-material
description: Use when creating or reviewing materials, instances, parameter collections, or material graphs
---

# cortex-material

Creates and reviews materials, instances, and parameter collections following the `resources/material-development.md` guide.

## Mode Detection

Determine mode from user intent:

- **Create/Modify**: User wants to build or change something
  Examples: "create a material", "add a parameter to", "update the texture slot", "create an instance of"
  → Follow the `resources/material-development.md` guide.

- **Review/Analyze**: User wants to understand or audit existing assets
  Examples: "review materials in /Game/Materials", "check naming conventions", "audit material complexity", "list all instances"
  → Follow the `resources/material-development.md` guide.

- **Ambiguous** → Default to Review (read-only, safe)

## Routing

| Mode | Guide |
|------|-------|
| Create/Modify | `material-development` |
| Review/Analyze | `material-development` |

## Steps

### 1. Execute the Workflow

Read the guide listed in the routing table for the detected mode, then execute its workflow directly in this conversation using the MCP tools it references.

**For Create/Modify**, execute the mandatory pipeline directive:

```
Create the following material using the MANDATORY pipeline:

**Material:** [name, e.g. M_PulsatingRed]
**Path:** [e.g. /Game/Materials/]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before proceeding]
**Description:** [visual description of what the material should look like]
**Parameters to expose:** [list of ScalarParameter/VectorParameter names and defaults]
**Material instances:** [list of instances to derive, if any]

MANDATORY WORKFLOW:
1. Read `.cortex/domains/material.md` for pin conventions
2. Use `prefetched_state` first and avoid re-fetching the same baseline
3. Run independent read calls in parallel
4. Design your nodes[] and connections[] arrays as a JSON spec
5. Call `material_compose(name, path, nodes, connections)` as a SINGLE call
6. Include `expected_fingerprint` on every mutation that touches a prefetched asset
7. Create material instances if requested

PROHIBITED:
- For NEW materials: never call `create_material`, `add_node`, `connect`, `set_node_property`, or `auto_layout` individually — use `material_compose` exclusively.
- For EXISTING materials with 2+ changes: never make N sequential individual tool calls — use `core_cmd(batch)` with `stop_on_error: true` and `$ref` wiring (see `resources/batch-pipeline-guide.md`).
- Individual tools are only acceptable for a single isolated change on an existing asset.

**For Review/Analyze**, include the same `prefetched_state` block before reading, consume it before fresh reads, and keep independent reads parallel. Any follow-up mutation must carry `expected_fingerprint`.
```

**For Review/Analyze**, pass the review scope and focus:
- Specific materials to review, or a path for full review
- Specific concerns (graph complexity, parameter usage, instance hierarchy, naming)

### 2. Reporting Results

Report results to the user with a completion status:
- **completed** — present results. For creates, include created asset paths. For reviews, include findings grouped by severity.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it.

If the work is interrupted mid-execution, treat it as **partial** — summarize what was produced and warn the review or creation may be incomplete.
