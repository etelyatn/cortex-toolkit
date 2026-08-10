---
name: cortex-qa-interactive
description: Use when running a live, interactive QA session with iterative action and observation
---

# Cortex QA Interactive

## Goal

Drive live exploratory testing in PIE with tight observe-act-assert loops.

## Steps

<!-- Turn budget: INTERACTIVE tier (75 turns) — user-driven session safety net -->
1. Dispatch the qa-engineer agent with a 75-turn budget.
2. Instruct the agent to operate in `guided` mode and:
   - execute one user-requested step at a time,
   - report findings after every step,
   - suggest the next highest-value probe.
3. Continue until the user ends the session or a critical issue is found.

## Constraints

- Keep this skill as orchestration only; agent holds domain logic.

## Handling Session End

If the agent reaches the turn limit (75 turns), report to the user:

> Interactive session ended due to turn limit. Here's what was covered: [summary of findings and areas tested]. You can re-invoke the cortex-qa-interactive skill to continue testing.

Do not treat this as a failure — interactive sessions are naturally open-ended.
