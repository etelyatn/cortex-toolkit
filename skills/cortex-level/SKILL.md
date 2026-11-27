---
name: cortex-level
description: Use when placing, organizing, or reviewing actors in a level
---

# Level

Places, organizes, modifies, and reviews level content following the `resources/level-design.md` guide.

## Mode Detection

| Request | Mode |
|---------|------|
| "Place", "Add", "Spawn", "Build", "Move", "Delete", "Organize", "Adjust lighting", multi-actor layout, scene construction | Create/Modify |
| "Review", "Audit", "Check", "Analyse", "What actors", "List", spatial/organization questions | Review/Analyze |
| Ambiguous | Default to **Review** |

---

## PIE Runtime Targets

The default world for every `level_cmd` actor command is the editor world. When the user asks
to inspect, move, spawn, or screenshot something **while PIE is running**, target the play world:

- Start a session with `editor_cmd(command="start_pie", params={"mode": "selected_viewport"})`
  and wait for `get_pie_state` to report `playing`.
- Pass `world: "pie"` to `spawn_actor`, `delete_actor`, `rename_actor`, `get_actor`,
  `set_transform`, `set_actor_property`, `get_actor_property`, the component commands,
  `attach_actor`/`detach_actor`/`set_tags`/`set_folder`, `list_actors`, `find_actors`,
  `get_bounds`, and `get_info`. Without PIE, `world: "pie"` returns `PIE_NOT_ACTIVE`;
  an unknown value returns `INVALID_VALUE`.
- For a runtime camera, call `level_cmd(command="set_pie_view", params={"location": [x,y,z],
  "rotation": [pitch,yaw,roll], "fov": 75})`. It spawns or reuses a transient camera and sets the
  player view target; `editor_cmd(command="capture_screenshot")` then captures the PIE game view
  (`source: auto` reads the PIE window while PIE runs, so UMG is included: `includes_ui: true`).
- `level_compose` has no `world` parameter (editor-world only). For multiple PIE actor
  operations, call `core_cmd(command="batch_query", params={"commands": [...]})` with
  `world: "pie"` on each level step, or call `level_cmd` individually. Batched `level_cmd`
  forms accept a top-level `world`; a malformed value is `INVALID_VALUE` before any item runs.
- PIE actors and the view camera are transient: they disappear when the session stops.
  `duplicate_actor` refuses `world: "pie"` in single and batched forms; use `spawn_actor`
  for runtime actors.

---

## Create / Modify Mode

### 1. Execute the Workflow

Read the `resources/level-design.md` guide, then execute its workflow directly in this conversation.

**Execute the 3-phase methodology:**

```
Make the following level changes using the 3-phase methodology:

**Request:** [user's request verbatim]
**Prefetched state:** [embed the main-thread `prefetched_state` block here before proceeding]

MANDATORY WORKFLOW:
0. VERIFY: call `get_info` to confirm MCP connectivity. If it fails, invoke `cortex-editor`.
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

### 2. Workflow

Follow this workflow:
1. Read `.cortex/domains/level.md`
2. **Plan** — inspect level state, design full `operations[]` spec
3. **Batch** — call `level_compose` once
4. **Verify** — check result, apply minimal fix if needed
5. Report summary

### 3. Verify Results

`level_compose` returns:
- `success`: true/false
- `actor_count` + `spawned_actors`: actors created or duplicated
- `completed_steps` / `total_steps`: batch progress
- `failed_steps[]`: per-failure with `op_id`, `command`, `error_code`, `error`

A failed compose is the canonical MCP failure object: `_error` is the first failed step's `error_code`
(`INVALID_OPERATION` when the step reported none), `_message` is the step summary, the per-step codes
stay in `failed_steps[]`, and the result is marked `isError`.

---

## Review / Analyze Mode

### 1. Execute the Workflow

Read the `resources/level-design.md` guide, then execute its workflow directly in this conversation.

Pass context about what to review:

```
Review the current level and provide a report:

**Prefetched state:** [embed the main-thread `prefetched_state` block here before proceeding]

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

### 2. Workflow

Follow this workflow:
1. Query level info and actor lists
2. Analyze organization patterns
3. Check spatial distribution
4. Report findings and recommendations

### 3. Verify Results

The review produces:
- Level overview (name, actor count, world type, is_world_partition)
- Actor breakdown by class and folder
- Spatial bounds information
- Organization issues found
- Recommendations for improvement

---

## Handling Results

Report results to the user with a completion status:
- **completed** — present results to the user.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For Create/Modify mode, warn the user that level changes may be incomplete.

If the work is interrupted mid-execution, treat it as **partial** — summarize what was produced and note the work may be incomplete.
