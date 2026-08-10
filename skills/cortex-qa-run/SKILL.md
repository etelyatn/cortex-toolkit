---
name: cortex-qa-run
description: Use when executing a predefined gameplay QA scenario and collecting findings
---

# Cortex QA Run

## Goal

Execute a scenario file through the QA agent and return findings with report artifacts.

## Steps

<!-- Turn budget: COMPLEX tier (35 turns) — iterative OODA loop pattern -->
1. Dispatch the qa-engineer agent with a 35-turn budget.
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

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the scenario results (pass/fail, findings, report paths).
- **blocked** / **partial** — surface what steps were completed, what remains, and what blocked execution. The user can re-invoke for remaining steps.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever findings were collected and note that the scenario may not have completed all steps.
