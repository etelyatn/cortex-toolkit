---
name: cortex-level-edit
description: Use when making any change to level content - placing actors, moving
  or reorganizing existing actors, adjusting lighting, building multi-actor layouts,
  deleting actors, or reorganizing scene structure
---

# Level Edit

Delegates any level change to the Level Designer agent using the batch-first methodology.

## Steps

### 1. Launch Level Designer Agent

<!-- Turn budget: CREATE tier (max_turns=25) — design + execute + verify pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:level-designer"` and `max_turns: 25` to delegate the work.

**Structure the prompt using the 3-phase directive:**

```
Make the following level changes using the 3-phase methodology:

**Request:** [user's request verbatim]

MANDATORY WORKFLOW:
0. VERIFY: call `get_info` to confirm MCP connectivity. If it fails, invoke `cortex-status`.
1. Read `.cortex/domains/level.md` for level conventions
2. PLAN: call `get_info`, then `list_actors` or `find_actors` to understand current state.
   Design the complete `operations[]` array before touching anything.
3. BATCH: call `level_compose` once with the full spec.
   - Use `stop_on_error: true` if any op references `$ops[...]` from another op in the batch
   - Use `stop_on_error: false` for independent bulk modifications
4. VERIFY: check `completed_steps == total_steps`.
   If false, diff `spawned_actors` against plan, call `find_actors` if needed,
   then construct a MINIMAL fix batch for the gap only.
   Maximum one retry batch. If retry fails, stop and report.

TOOL SELECTION RULE:
- level_compose: 2+ spawns OR 3+ existing actor modifications OR any spawn+configure chain
- Individual tools: 1-2 existing actors with a single change (quick corrections only)

PROHIBITED: Do NOT skip the Plan phase for multi-actor work. Do NOT call get_actor
for each spawned actor to verify - check completed_steps first.
```

### 2. Agent Workflow

The Level Designer agent will:
1. Read `.cortex/domains/level.md`
2. **Plan** - inspect level state, design full `operations[]` spec
3. **Batch** - call `level_compose` once
4. **Verify** - check result, apply minimal fix if needed
5. Report summary

### 3. Review Agent Results

The agent returns from `level_compose`:
- `success`: true/false
- `actor_count` + `spawned_actors`: actors created or duplicated
- `completed_steps` / `total_steps`: batch progress
- `failed_steps[]`: per-failure with `op_id`, `command`, `error_code`, `error`

## Troubleshooting

**Agent uses individual tools for multi-actor work:**
The structured prompt's TOOL SELECTION RULE should prevent this. If it still happens,
re-emphasize the rule in the prompt.

**Batch partially fails:**
Check `failed_steps[].op_id` to identify which named operations failed and why.
Common causes: actor label not found (`ActorNotFound`), class not available (`ClassNotFound`).

**"Grouping not supported in World Partition":**
`group_actors` is not available in WP levels. Use folder organization instead.

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the batch results to the user.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. The user may need to inspect the level for partially applied changes.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and warn that level changes may be incomplete.
