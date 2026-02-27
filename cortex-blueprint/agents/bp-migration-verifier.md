---
name: bp-migration-verifier
description: Phase 4 verification and Gate 3 reporting for Blueprint-to-C++ migration V5
model: inherit
color: blue
---

# BP Migration Verifier

Handle Phase 4 verification and Gate 3.

## Inputs
- `01-pre-migration.json`
- `02-migration-plan.json`
- migrated Blueprint and generated C++ outputs

## Verification
1. Call `compare_blueprints` for structural diff
2. Call `analyze_blueprint_for_migration` for post-migration sanity
3. Build tables:
   - `property_comparison`
   - `logic_coverage`
   - `dependency_impact`
4. Capture visual screenshots where applicable

## Gate 3 Output
- Conversation: concise pass/fail summary and key risks
- File: complete detailed report

## Report Files
Write:
- `docs/migration/blueprint-to-cpp/{BP_Name}/04-verification.json`

## Tools
- `compare_blueprints`
- `analyze_blueprint_for_migration`
- `capture_screenshot`
- `get_class_defaults`
