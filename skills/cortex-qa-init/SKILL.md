---
name: cortex-qa-init
description: Use when initializing QA workflows for a project and generating a baseline game QA profile
---

# Cortex QA Init

## Goal

Prepare QA context for a project and generate an initial game profile for scenario-driven testing.

## Steps

1. Follow the `resources/qa-engineering.md` guide for QA methodology.
2. Complete the initialization workflow:
   - Verify MCP connectivity and PIE readiness.
   - Inspect key gameplay actors/systems.
   - Produce a first-pass QA profile using `resources/game-profile-template.md`.
3. Save the generated profile in the project QA workspace requested by the user.

## Notes

- Keep this flow non-destructive.
- Prefer discovery and documentation over test mutation.
