---
name: cortex-level
description: Use when placing, organizing, or reviewing actors in a level
---

# Level

Places, organizes, modifies, and reviews level content using the Level Designer agent.

## Mode Detection

| Request | Mode | Agent turns |
|---------|------|-------------|
| "Place", "Add", "Spawn", "Build", "Move", "Delete", "Organize", "Adjust lighting", multi-actor layout, scene construction | Create/Modify | 25 |
| "Review", "Audit", "Check", "Analyse", "What actors", "List", spatial/organization questions | Review/Analyze | 15 |
| Ambiguous | Default to **Review** | 15 |

---

## Create / Modify Mode

### 1. Launch Level Designer Agent

<!-- Turn budget: CREATE tier (25 turns) — design + execute + verify pattern -->
Dispatch the level-designer agent with a 25-turn budget to delegate the work.

**Structure the prompt using the 3-phase directive:**

```
Make the following level changes using the 3-phase methodology:

**Request:** [user's request verbatim]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before launching]

MANDATORY WORKFLOW:
0. VERIFY: call `get_info` to confirm MCP connectivity. If it fails, invoke `cortex-status`.
1. Use `prefetched_state` first. Do not re-fetch the same baseline unless required for the next step.
2. Read `.cortex/domains/level.md` for level conventions
3. PLAN: call `get_info`, then `list_actors` or `find_actors` to understand current state.
   Design the complete `operations[]` array before touching anything.
4. Issue independent discovery reads in parallel.
5. BATCH: call `level_compose` once with the full spec.
   - Use `stop_on_error: true` if any op references `$ops[...]` from another op in the batch
   - Use `stop_on_error: false` for independent bulk modifications
   - Pass `expected_fingerprint` on each mutation guarded by `prefetched_state`
6. VERIFY: check `completed_steps == total_steps`.
   If false, diff `spawned_actors` against plan, call `find_actors` if needed,
   then construct a MINIMAL fix batch for the gap only.
   Maximum one retry batch. If retry fails, stop and report.

TOOL SELECTION RULE:
- level_compose: 2+ spawns OR 3+ existing actor modifications OR any spawn+configure chain
- Individual tools: 1-2 existing actors with a single change (quick corrections only)

PROHIBITED: Do NOT skip the Plan phase for multi-actor work. Do NOT call get_actor
for each spawned actor to verify — check completed_steps first.
```

### 2. Agent Workflow

The Level Designer agent will:
1. Read `.cortex/domains/level.md`
2. **Plan** — inspect level state, design full `operations[]` spec
3. **Batch** — call `level_compose` once
4. **Verify** — check result, apply minimal fix if needed
5. Report summary

### 3. Review Agent Results

The agent returns from `level_compose`:
- `success`: true/false
- `actor_count` + `spawned_actors`: actors created or duplicated
- `completed_steps` / `total_steps`: batch progress
- `failed_steps[]`: per-failure with `op_id`, `command`, `error_code`, `error`

---

## Review / Analyze Mode

### 1. Launch Level Designer Agent

<!-- Turn budget: REVIEW tier (15 turns) — read + analyze + report pattern -->
Dispatch the level-designer agent with a 15-turn budget to delegate the review.

Pass context about what to review:

```
Review the current level and provide a report:

**Prefetched state:** [embed the main-thread `prefetched_state` block here before launching]

1. Use `prefetched_state` first; only fetch missing data
2. Use `get_info` for level overview (name, actor count, world type, sublevels, is_world_partition)
3. Use `list_actors` to enumerate actors (paginate if needed)
4. Run independent reads in parallel where possible
5. Use `get_bounds` to understand spatial layout
6. Check folder organization — are actors organized logically?
7. Check for common issues:
   - Actors without folders
   - Duplicate labels
   - Actors at origin that shouldn't be
   - Unloaded sublevels
   - Missing data layer assignments (if World Partition)
8. Summarize findings with recommendations
```

### 2. Agent Workflow

The Level Designer agent will:
1. Query level info and actor lists
2. Analyze organization patterns
3. Check spatial distribution
4. Report findings and recommendations

### 3. Review Agent Results

The agent returns:
- Level overview (name, actor count, world type, is_world_partition)
- Actor breakdown by class and folder
- Spatial bounds information
- Organization issues found
- Recommendations for improvement

---

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present results to the user.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For Create/Modify mode, warn the user that level changes may be incomplete.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note the work may be incomplete.
