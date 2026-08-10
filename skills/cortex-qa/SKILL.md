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

1. Verify MCP connectivity and PIE readiness with `get_status`; if the editor is not running or the connection fails, direct the user to `cortex-editor`.
2. Inspect key gameplay actors and systems via `qa_cmd(command="observe_state")` and `qa_cmd(command="get_actor_state")`.
3. Produce a first-pass QA profile using `resources/game-profile-template.md` as the structure.
4. Save the generated profile in the project QA workspace requested by the user.

Keep this flow non-destructive. Prefer discovery and documentation over test mutation.

## Scenario Mode

Execute a predefined gameplay QA scenario and return findings with report artifacts.

1. Read the scenario format from `resources/scenario-format.md`. Execute the scenario steps directly with `scenario_compose(scenario_name=..., steps=[...])`, where each step carries the `action`, optional `wait`, optional `assertion`, and `screenshot_name`.
2. Detect structural issues after each step (assertion failures, unexpected actor state, missing actors).
3. Capture a screenshot on assertion failures so the report has visual evidence.
4. Return a final summary with:
   - pass/fail status
   - major and critical findings
   - paths to generated report files

If the scenario is interrupted, report what completed, what remains, and what blocked execution. Treat a scenario with no final status as partial.

## Interactive Mode

Drive live exploratory testing in PIE with tight observe-act-assert loops.

1. Loop `qa_test_step` steps in the current conversation: each step has an `action` (`qa_cmd` command such as `move_to`, `interact`, `look_at`, `teleport_player`, `probe_forward`), optional `wait`, optional `assertion` (via `qa_cmd(command="assert_state")`), and a `screenshot_name`.
2. Operate one user-requested step at a time; report findings after every step.
3. After each step, suggest the next highest-value probe based on observed state.
4. Continue until the user ends the session or a critical issue is found.

If the conversation reaches a turn limit, report what was covered and tell the user to continue by invoking `cortex-qa` again. Do not treat the turn limit as a failure.
