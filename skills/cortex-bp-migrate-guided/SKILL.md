---
name: cortex-bp-migrate-guided
description: Interactive Blueprint-to-C++ migration V5 with phase-based agents, scope gates, partial mode, and resume support.
---

# Guided Blueprint to C++ Migration (V5)

Use the 2-agent workflow:
1. `cortex-toolkit:bp-migration-planner`
2. `cortex-toolkit:bp-migration-executor`

## Flags
- `/cortex-bp-migrate-guided BP_Name`
- `/cortex-bp-migrate-guided BP_Name --level minimal|medium|maximal`
- `/cortex-bp-migrate-guided BP_Name --partial` (run only selected groups and preserve pass state)

## Workflow
1. Parse BP target and flags.
2. Resolve migration directory: `docs/migration/blueprint-to-cpp/{BP_Name}/`.
3. Resume detection:
   - If section files already exist, infer current phase from highest file present.
   - Continue from the next missing phase unless user requests restart.
4. Dispatch planner, then executor with a gate pause between phases.
5. Executor handles verification, swap, and finalization; merges section files into `report.json`.

## Resume Map
- `01-pre-migration.json` only: resume at planning.
- `02-migration-plan.json` exists: resume at execution prep.
- `03-node-mapping.json` exists: resume at verification (executor picks up here).
- `04-verification.json` exists: resume at swap/finalization (executor picks up here).
- `report.json` exists: migration complete.

## References
- `docs/plans/2026-02-26-bp-migration-v5-design.md`
- `docs/plans/2026-02-26-bp-migration-v5-impl.md`
- `resources/cpp-migration.md`
