---
name: cortex-qa
description: Use when generating QA baselines, running scenario-driven gameplay QA, or starting an interactive QA session
---

# Cortex QA

## Intent Routing

- "generate baseline", "initialize QA", "set up QA profile" -> Baseline Mode
- "run this scenario", "execute gameplay test", "scenario file" -> Scenario Mode
- "interactive QA", "exploratory session", "step through PIE testing" -> Interactive Mode

Only ask a follow-up when the request is genuinely ambiguous between scenario execution and interactive exploration.

## Baseline Mode

Prepare QA context for a project and generate an initial game profile.

1. Launch the `cortex-toolkit:qa-engineer` agent.
2. Ask it to:
   - verify MCP connectivity and PIE readiness
   - inspect key gameplay actors and systems
   - produce a first-pass QA profile using `resources/game-profile-template.md`
3. Save the generated profile in the project QA workspace requested by the user.

Keep this flow non-destructive. Prefer discovery and documentation over test mutation.

## Scenario Mode

Execute a predefined gameplay QA scenario and return findings with report artifacts.

1. Use the Task tool with `subagent_type: "cortex-toolkit:qa-engineer"` and `max_turns: 35`.
2. Provide the scenario path or scenario content and request:
   - scenario execution via QA composite tools
   - structural issue detection after each step
   - screenshot capture on assertion failures
3. Require a final summary with:
   - pass/fail status
   - major and critical findings
   - paths to generated report files

If the agent returns `completed`, present the scenario results.
If it returns `blocked` or `partial`, report what completed, what remains, and what blocked execution.
If there is no status line, treat the run as partial and summarize what findings were collected.

## Interactive Mode

Drive live exploratory testing in PIE with tight observe-act-assert loops.

1. Use the Task tool with `subagent_type: "cortex-toolkit:qa-engineer"` and `max_turns: 75`.
2. Instruct the agent to operate in guided mode:
   - execute one user-requested step at a time
   - report findings after every step
   - suggest the next highest-value probe
3. Continue until the user ends the session or a critical issue is found.

If the session reaches the turn limit, report what was covered and tell the user to continue by invoking `cortex-qa` again. Do not treat the turn limit as a failure.
