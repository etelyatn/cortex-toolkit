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

The agent runs interactively through three phases (Analysis → Preview & Execute → Result & Recovery), pausing at each gate for user input. It will not proceed without explicit confirmation at each decision point.

### 4. Review Results

Review output. Migration remediation doc (if generated) is at:
`docs/migration/blueprint-to-cpp/{BP_Name}-cpp-migration.md`

## Flags

- `/cortex-bp-migrate-guided BP_JumpPad` — full guided flow
- `/cortex-bp-migrate-guided BP_JumpPad --level medium` — skip level selection gate
