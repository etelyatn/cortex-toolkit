---
name: cortex-qa-run
description: Use when executing a predefined gameplay QA scenario and collecting findings
---

# Cortex QA Run

## Goal

Execute a predefined gameplay QA scenario and return findings with report artifacts.

## Steps

1. Follow the `resources/qa-engineering.md` guide and execute the scenario directly in this conversation.
2. Provide the scenario path/content and:
   - Execute it via QA composite tools.
   - Detect structural issues after each step.
   - Capture screenshots on assertion failures.
3. Produce a final summary with:
   - pass/fail status
   - major/critical findings
   - paths to generated report files

## Constraints

- Do not duplicate QA execution logic in this skill; follow the guide's methodology directly.

## Handling Results

Report results to the user with a completion status:
- **completed** — present the scenario results (pass/fail, findings, report paths).
- **blocked** / **partial** — surface what steps were completed, what remains, and what blocked execution. The user can re-invoke for remaining steps.

If the work is interrupted mid-execution, treat it as **partial** — summarize whatever findings were collected and note that the scenario may not have completed all steps.
