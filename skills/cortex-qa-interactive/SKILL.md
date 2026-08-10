---
name: cortex-qa-interactive
description: Use when running a live, interactive QA session with iterative action and observation
---

# Cortex QA Interactive

## Goal

Drive live exploratory testing in PIE with tight observe-act-assert loops.

## Steps

1. Follow the `resources/qa-engineering.md` guide and drive the session directly in `guided` mode:
   - execute one user-requested step at a time,
   - report findings after every step,
   - suggest the next highest-value probe.
2. Continue until the user ends the session or a critical issue is found.

## Constraints

- Keep this skill as orchestration only; the guide holds the domain methodology.

## Handling Session End

When the session ends, report to the user:

> Interactive session ended. Here's what was covered: [summary of findings and areas tested]. You can re-invoke the cortex-qa-interactive skill to continue testing.

Do not treat this as a failure — interactive sessions are naturally open-ended.
