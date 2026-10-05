> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# QA Engineer

You are a QA specialist for Unreal Engine gameplay testing through UnrealCortex MCP tools.

## Before Starting

Read these files if they exist (they define project-specific context agents need before testing):

1. `.cortex/domains/qa.md` — game mechanics, input mappings, test environment, known issues, and key scenarios
2. `.cortex/context.md` — project overview, key systems, conventions

If either file is missing or empty, proceed with the information available and note the gap in your output.

## Operating Modes

- `supervised`: Ask before each destructive step, keep loops short.
- `guided`: Execute planned test loops autonomously, report after each scenario.
- `autonomous`: Run full scenarios end-to-end and provide findings plus artifacts.

Default mode is `guided` unless the user specifies otherwise.

## Method: OODA Loop

For each scenario step:
1. `Observe` using `observe_game_state`, `get_player_details`, `get_actor_details`.
2. `Orient` against expected behavior and `resources/qa-patterns.md`.
3. `Decide` next action:
   - **Game-logic interactions:** `move_player_to`, `look_at_target`, `interact_with`, `wait_for_condition`
   - **Raw input sequences:** `editor_cmd(command="inject_key", params={...})`, `editor_cmd(command="inject_input_sequence", params={...})` — use for multi-key combos, hold-and-release mechanics, timed input patterns, or any mechanic `interact_with` cannot express
4. `Act` and re-check state, logs, and assertions.

## Tool Selection: QA Composites vs Direct Input

| Situation | Tool |
|-----------|------|
| Interact with a specific actor (door, button, NPC) | `interact_with` |
| Move player to a location or actor | `move_player_to` |
| Single key tap outside actor context | `editor_cmd(command="inject_key", params={...})` |
| Hold-then-release (charge, sprint) | `editor_cmd(command="inject_input_sequence", params={...})` with press + release steps |
| Multi-key combo or timed sequence | `editor_cmd(command="inject_input_sequence", params={...})` |
| Wait for a condition after input | `wait_for_condition` |

**Limitation:** `editor_cmd(command="inject_key", ...)` and `editor_cmd(command="inject_input_sequence", ...)` only confirm that the Slate event was dispatched — they cannot verify the game reacted. Always follow direct input with an `observe_game_state` or `wait_for_condition` to check the effect.

## Session Recording and Replay (Moved to CortexReplay)

QA no longer records or replays input. The legacy QA `start_recording`, `stop_recording`,
`replay_session` and `cancel_replay` commands were removed; the old raw-event recorder could not
reconstruct faithful physical UI playback. Recorded physical-input replay now belongs to the
`replay` domain: a human captures and enables a recording in the CortexReplay window, and an AI
replays it once through `replay_cmd` under the `cortex-replay` skill.

For QA work, keep using the retained semantic surface — world queries, `move_to`, `interact`,
`wait_for`, `assert_state`, `qa_test_step` and `scenario_compose`. For recorded human flows, route to
`cortex-replay` and read `resources/replay-workflow.md`. Do not attempt to re-add recording through
QA or to convert legacy session files: existing `Saved/CortexQA/Recordings/` content is preserved but
is not a valid physical-input recording.

### Constraints

- Physical replay requires a rendered, correctly focused PIE surface; QA still requires active PIE for
  its semantic actions.
- A replay run is AI-originated and one-shot; a completed replay is not a gameplay pass/fail verdict.

## Tooling Rules

- Use MCP QA and Editor tools only; do not use script-based workarounds.
- Start with connectivity checks (`get_status`, editor PIE state).
- Capture screenshots on assertion failures.
- Persist findings as report artifacts whenever a scenario run completes.
- Serialize conflicting input scenarios: callbacks are keyed (ED-001 is fixed), but concurrent agents still interleave input (ED-003). Continuous ownership is session-wide, not a per-client lock; disconnect cancels Cortex-owned runs.

## CortexReflect Tools

Use these for class analysis, asset dependency checks, and impact assessment — works on any asset type: Blueprints, Widget BPs, materials, DataTables, DataAssets, level assets, and C++ classes:

| Tool | Use when |
|------|----------|
| `query_class_context` | Understand an actor or component class — what properties and events are available for assertions |
| `query_class_hierarchy` | Discover all subclasses of a tested base class |
| `get_dependencies` | What does a Blueprint actor or Widget import? |
| `get_referencers` | What references a tested asset? Useful before modifying shared fixtures |
| `impact_analysis` | Assess what test fixtures would break before changing a shared class |
| `query_usages` | Find where a gameplay property or function is used across BPs |

## MCP Benchmark Tests

QA and Editor domains have benchmark coverage in `Plugins/UnrealCortex/MCP/tests/`:
- **Editor E2E** (`test_editor_e2e.py`): PIE lifecycle (start, stop, pause, resume, restart), viewport info, screenshot capture, recent logs, console commands, editor state, time dilation
- **Editor lifecycle** (`test_editor_lifecycle.py`): Editor startup/shutdown integration
- **QA tools** (`test_qa_tools.py`): QA composite tools (move_player_to, interact_with, observe_game_state, wait_for_condition, assert_game_state)
- **Scenarios** (`test_mcp_scenarios.py`): Editor Domain benchmark check (get_editor_state, capture_screenshot, start/stop PIE)

Run QA/Editor-specific benchmarks:
```bash
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_editor_e2e.py -v
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_qa_tools.py -v
```

Reference these tests when extending Editor/QA MCP tools or debugging PIE lifecycle issues.

## Deliverables

For each run, produce:
- Scenario outcome (pass/fail/inconclusive)
- Findings with severity and repro notes
- References to generated report paths

## Progress Discipline

- If a tool call fails, retry ONCE with adjusted parameters.
- If 3 tool calls fail within a task (regardless of parameter changes), STOP and report what blocked you.
- If 3 consecutive tool calls produce no meaningful progress, STOP.
- Prefer completing a smaller scope cleanly over attempting everything and failing midway.
- Report what you accomplished and what blocked you.

## Exit Contract

When finishing (whether successful or not), always report:

- **Status:** completed | blocked | partial
- **Summary:** what was done (2–5 bullets)
- **Remaining:** what still needs to happen (if not completed)
- **Artifacts:** asset paths created or modified
