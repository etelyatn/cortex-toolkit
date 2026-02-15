---
name: cortex-bp-migrate
description: Migrate Blueprint logic to C++, or audit a Blueprint for migration candidates. Supports --audit (analysis only) and --dry-run (generate but don't write).
---

# Blueprint to C++ Migration

Analyzes a Blueprint against existing C++ code, determines the right action (migrate, merge, improve, delete, or keep), and generates C++ code using the C++ Migration Specialist agent.

## Steps

### 1. Parse User Input

Extract from the user's message:
- **Blueprint reference:** Asset path (e.g., `/Game/Blueprints/BP_HealthPickup`) or name
- **Mode flag:** Check for `--audit` or `--dry-run` in the input
  - `--audit`: Analysis only, no code generation
  - `--dry-run`: Generate code but don't offer to write files
  - No flag: Full workflow (default)
- **User preferences:** Any specific notes (e.g., "only migrate the Tick logic", "keep event dispatchers in BP")

### 2. Launch C++ Migration Specialist Agent

Use the Task tool with `subagent_type: "cortex-blueprint:cpp-migration-specialist"` to delegate the migration.

Example prompt for the agent:

```
Analyze the Blueprint at {path} and determine the appropriate migration action.

Mode: {full | audit | dry-run}
User context: {any preferences or notes from the user}

Follow your 6-phase workflow: analyze the Blueprint via MCP tools, scan existing C++ source, decide the outcome (migrate/merge/improve/delete/keep), generate C++ code if appropriate, present for review, and ask before writing files.
```

### 3. Agent Workflow (runs autonomously)

The C++ Migration Specialist agent will:
1. Read project context and coding standards
2. Analyze the Blueprint via MCP tools (get_blueprint_info, graph_list_graphs, graph_list_nodes)
3. Scan project Source/ for existing C++ counterparts (Grep/Glob)
4. Classify into one of 5 outcomes: Migrate, Merge, Improve, Delete, Keep
5. Generate C++ code or patches (unless audit mode or Delete/Keep outcome)
6. Present the analysis and code for user review
7. Ask the user whether to write/modify files (unless dry-run mode)

### 4. Review Agent Results

The agent presents:
- **Audit summary** — outcome classification (Migrate/Merge/Improve/Delete/Keep) with evidence
- **Migration analysis** — table of what moves to C++ and what stays in BP
- **Existing C++ comparison** — what already exists, what overlaps (if applicable)
- **C++ header** — complete .h file or diff for existing files
- **C++ source** — complete .cpp file or diff for existing files
- **Blueprint changes** — prescriptive, ordered reparenting/cleanup steps
- **Next steps** — compile, test, verify

The agent will ask before writing any files. You can request adjustments before accepting.

## Supported Blueprint Types

- **Actor Blueprints** — migrated to C++ base class (AActor or existing C++ parent subclass)
- **Widget Blueprints** — migrated to C++ UUserWidget subclass with BindWidget

## Migration Outcomes

| Outcome | What Happens |
|---------|-------------|
| **Migrate** | New C++ class generated, BP reparented |
| **Merge** | Existing C++ class extended with BP's additions |
| **Improve** | Existing C++ class updated with better logic from BP |
| **Delete** | BP identified as duplicate/garbage, deletion recommended |
| **Keep** | BP logic is appropriate as Blueprint, no migration needed |

## Flags

- `/cortex-bp-migrate BP_HealthPickup` — full migration workflow
- `/cortex-bp-migrate BP_HealthPickup --audit` — analysis only, report findings
- `/cortex-bp-migrate BP_HealthPickup --dry-run` — generate code, don't write files

## Why Use the Agent?

- **Smart classification** — doesn't blindly migrate; detects duplicates, garbage, and overlap with existing C++
- **Clean conversation** — no flood of MCP tool calls in your chat
- **Structured methodology** — 6-phase analysis before code generation
- **Coding standards enforced** — follows `docs/unreal-coding-standards.md`
- **Safe by default** — presents code for review, asks before writing files
