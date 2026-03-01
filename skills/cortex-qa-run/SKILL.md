---
name: cortex-qa-run
description: Use when executing a predefined gameplay QA scenario and collecting findings
---

# Cortex QA Run

## Goal

Execute a scenario file through the QA agent and return findings with report artifacts.

## Steps

1. Launch Task agent: `cortex-toolkit:qa-engineer`.
2. Provide the scenario path/content and request:
   - Scenario execution via QA composite tools.
   - Structural issue detection after each step.
   - Screenshot capture on assertion failures.
3. Require a final summary with:
   - pass/fail status
   - major/critical findings
   - paths to generated report files

## Constraints

- Do not duplicate QA execution logic in this skill; delegate to the agent.
