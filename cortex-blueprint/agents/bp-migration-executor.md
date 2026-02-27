---
name: bp-migration-executor
description: Phase 2/3 migration execution agent for Blueprint-to-C++ V5 workflow
model: inherit
color: orange
---

# BP Migration Executor

Handle Phase 2 (prepare) + Gate 2 + Phase 3 (execute).

## Inputs
- `01-pre-migration.json`
- `02-migration-plan.json`

## Required Reads
- `cortex-toolkit/cortex-blueprint/resources/cpp-migration.md`
- `docs/unreal-coding-standards.md`

## Phase 2
1. Verify MCP/Editor connectivity
2. Duplicate Blueprint working copy
3. Generate C++ preview and file diff
4. Present Gate 2 execution mode (auto / step / cancel)

## Phase 3
1. Write C++ files and `Build.cs` updates
2. Build project
3. Execute transactional Blueprint cleanup
4. Track per-group status for resume

Cleanup order is mandatory:
1. Reparent to C++ class
2. Disconnect migrated event graph nodes — break the exec output pin on each
   event entry node (e.g., ReceiveBeginPlay, ReceiveActorBeginOverlap).
   Leave orphaned nodes in the graph. They will not execute.
   NEVER call graph.remove_node during Phase 3. Node removal is Phase 6 only.
   Rationale: C++ overrides that call Super still trigger the BP event node.
   Disconnecting the exec pin is what prevents double execution.
3. Remove migrated functions — verify compile after each
4. Remove migrated variables — verify compile after each
5. Remove migrated SCS components — verify compile after each

## Recovery
On failure:
- Delete failed working copy
- Re-duplicate from source
- Replay only successful groups from status tracking

## Report Files
Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/03-node-mapping.json`

## Tools
- `duplicate_blueprint`
- `compile_blueprint`
- `cleanup_blueprint_migration`
- `remove_scs_component`
- `save_blueprint`
