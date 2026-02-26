---
name: cortex-bp-migrate-guided
description: Interactive Blueprint-to-C++ migration with level selection, structured preview, dependency analysis, and rollback support. Use when the user wants to review migration options before committing.
---

# Guided Blueprint to C++ Migration

Interactive three-phase migration flow that presents options at each decision gate. Analyzes the Blueprint, checks dependencies and existing C++ code, lets you choose migration scope, previews changes, and offers rollback after execution.

## Steps

### 1. Parse User Input

Extract:
- Blueprint path or name (required)
- `--level minimal|medium|maximal` (optional — skip Gate 1 level selection)

### 2. Launch Migration Guide Agent

Delegate to `cortex-blueprint:bp-migration-guide`.

Pass:
- Blueprint path
- Pre-selected level (if `--level` flag provided)

### 3. Agent Workflow (interactive — pauses at each gate)

**Phase 1: Analysis**
1. Analyze Blueprint structure via `analyze_blueprint_for_migration`
2. Scan downstream dependencies via CortexReflect tools
3. If parent is project C++ class: read existing C++ implementation

**Gate 1: Scope Selection**
- If engine base class parent: present Minimal / Medium / Maximal levels
- If project C++ parent: present per-element merge plan
- User selects scope or picks custom elements

**Phase 2: Preview & Execute**
4. Present structured preview with downstream impact
5. User picks execution mode: Auto / Step-by-step / Cancel
6. Generate C++ code, build, run Blueprint cleanup

**Phase 3: Result & Recovery**
7. Present completion status and manual steps
8. User picks: Keep as-is / Rollback Blueprint only / Rollback everything

### 4. Review Results

Review output. Migration remediation doc (if generated) is at:
`docs/migration/blueprint-to-cpp/{BP_Name}-cpp-migration.md`

## Flags

- `/cortex-bp-migrate-guided BP_JumpPad` — full guided flow
- `/cortex-bp-migrate-guided BP_JumpPad --level medium` — skip level selection gate
