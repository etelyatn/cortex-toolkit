---
name: cortex-bp-migrate-guided
description: Interactive Blueprint-to-C++ migration v2.0 with phase-based agents, scope gates, partial mode, and resume support.
---

# Guided Blueprint to C++ Migration (v2.0)

Use the 4-agent workflow:
1. `bp-migration-analyst`
2. `bp-migration-executor`
3. `bp-migration-verifier`
4. `bp-migration-finalizer`

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
4. Dispatch agents in sequence with gate pauses between phases.
5. Finalizer merges section files into `report.json`.

## Resume Map
- `01-pre-migration.json` only: resume at planning.
- `02-migration-plan.json` exists: resume at execution prep.
- `03-node-mapping.json` exists: resume at verification.
- `04-verification.json` exists: resume at swap/finalization.
- `report.json` exists: migration complete.

## References
- `docs/plans/2026-02-26-bp-migration-v2-design.md`
- `docs/plans/2026-02-26-bp-migration-v2-impl.md`
- `cortex-toolkit/cortex-blueprint/resources/cpp-migration.md`
