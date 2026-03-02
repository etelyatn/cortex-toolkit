---
name: cortex-reflect
description: "Analyze project class architecture — inheritance trees, Blueprint overrides, cross-references. Use when you need to understand how C++ and Blueprint classes relate."
---

# CortexReflect — Project Knowledge Graph

Analyze your project's class architecture with a single command.

## Usage

`cortex-reflect AMyCharacter` — Full context for a class
`cortex-reflect hierarchy AMyCharacter` — Inheritance tree
`cortex-reflect usages Health AMyCharacter` — Cross-references

## What it does

1. Checks cache freshness (rebuilds if stale)
2. Queries the class hierarchy, detail, and cross-references
3. Presents a comprehensive summary

## Implementation

<!-- Turn budget: COMPLEX tier (max_turns=35) — iterative class hierarchy exploration -->
Use the Task tool with `subagent_type: "cortex-toolkit:project-analyzer"` and `max_turns: 35` to execute this skill with the appropriate CortexReflect MCP tools.

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the class analysis to the user.
- **blocked** / **partial** — surface what was analyzed and what remains. If the cache was stale or a rebuild was needed, note it.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever analysis was produced.
