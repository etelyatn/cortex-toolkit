---
name: cortex-qa-interactive
description: Use when running a live, interactive QA session with iterative action and observation
---

# Cortex QA Interactive

## Goal

Drive live exploratory testing in PIE with tight observe-act-assert loops.

## Steps

1. Launch Task agent: `cortex-toolkit:qa-engineer`.
2. Instruct the agent to operate in `guided` mode and:
   - execute one user-requested step at a time,
   - report findings after every step,
   - suggest the next highest-value probe.
3. Continue until the user ends the session or a critical issue is found.

## Constraints

- Keep this skill as orchestration only; agent holds domain logic.
