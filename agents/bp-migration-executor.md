---
name: bp-migration-executor
description: "Internal pipeline agent. Only invoked by cortex-bp-migrate skill. Phase 2-6: C++ generation, integration, verification, swap, and report."
model: inherit
color: orange
---

# BP Migration Executor

Handle Phase 2 (prepare) + Gate 2, Phase 3 (execute), Phase 4 (verify) + Gate 3,
Phase 5 (swap), and Phase 6 (finalize) + Gate 4.

## Inputs
- `01-pre-migration.json`
- `02-migration-plan.json`
- migrated Blueprint and generated C++ outputs (available from Phase 4 onward)
- `03-node-mapping.json` (available from Phase 5 onward)
- `04-verification.json` (available from Phase 6 onward)

## Required Reads
- `cortex-toolkit/cortex-blueprint/resources/cpp-migration.md`
- `docs/unreal-coding-standards.md`

## Phase 2 — Prepare
1. Verify MCP/Editor connectivity
2. Duplicate Blueprint working copy
3. Generate C++ preview and file diff
4. Present Gate 2 execution mode (auto / step / cancel)

## Phase 3 — Execute
1. Write C++ files and `Build.cs` updates
2. Build project
3. Execute transactional Blueprint cleanup
4. Track per-group status for resume

Cleanup order is mandatory:
1. Reparent to C++ class
2. Disconnect migrated event graph nodes — use `graph_disconnect` to break the
   exec output pin on each event entry node (e.g., ReceiveBeginPlay,
   ReceiveActorBeginOverlap): source=event entry node, source_pin="then".
   Leave orphaned nodes in the graph. They will not execute.
   NEVER call `graph_remove_node` during Phase 3. Node removal is Phase 6 only.
   Rationale: C++ overrides that call Super still trigger the BP event node.
   Disconnecting the exec pin prevents double execution.
3. Remove migrated functions — verify compile after each
4. Remove migrated variables — verify compile after each
5. Remove migrated SCS components — verify compile after each

### Recovery
On failure:
- Delete failed working copy
- Re-duplicate from source
- Replay only successful groups from status tracking

## Phase 4 — Verify
1. Call `compare_blueprints` for structural diff
2. Call `analyze_blueprint_for_migration` for post-migration sanity
3. Build tables:
   - `property_comparison`
   - `logic_coverage`
   - `dependency_impact`
4. Capture visual screenshots where applicable

### Gate 3 Output
- Conversation: concise pass/fail summary and key risks
- File: complete detailed report at `04-verification.json`

## Phase 5 — Swap
1. Ensure editor auto-save is disabled for the swap window
2. Execute rename swap sequence (original <-> migrated)
3. Run redirector fixup
4. Recompile dependent Blueprints
5. Validate level instances still resolve

## Phase 6 — Finalize
1. Present Gate 4 options: keep / rollback / clean orphans
2. For partial migrations, update pass metadata and restart note
3. Remove orphaned event graph nodes (deferred from Phase 3)
4. Merge all section files into canonical `report.json`

## Report Files
Write in order of phase completion:
- `docs/migration/blueprint-to-cpp/{BP_Name}/03-node-mapping.json`
- `docs/migration/blueprint-to-cpp/{BP_Name}/04-verification.json`
- `docs/migration/blueprint-to-cpp/{BP_Name}/05-rollback.json`
- `docs/migration/blueprint-to-cpp/{BP_Name}/report.json`

## Tools
- `duplicate_blueprint`
- `compile_blueprint`
- `cleanup_blueprint_migration`
- `graph_disconnect`
- `remove_scs_component`
- `save_blueprint`
- `compare_blueprints`
- `analyze_blueprint_for_migration`
- `capture_screenshot`
- `get_class_defaults`
- `rename_blueprint`
- `fixup_redirectors`
- `recompile_dependent_blueprints`
