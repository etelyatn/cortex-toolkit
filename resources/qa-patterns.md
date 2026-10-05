# QA Patterns

Bug detection patterns and classification for exploratory and scenario-driven gameplay testing.

## Severity

- `CRITICAL`: crashes, deadlocks, data corruption, progression blockers.
- `MAJOR`: core mechanic failure, frequent errors, unusable flow.
- `MINOR`: visual issues, minor placement/state inconsistencies.

## Common Checks

- Player below kill Z or outside playable bounds.
- Required interaction has no state change after valid input.
- Wait condition timeouts for expected gameplay transitions.
- Repeated error logs during scenario execution.
- Frame rate drops below defined threshold for sustained periods.

## Input-Driven Testing Patterns

**Single interaction:** Use `interact_with` — it handles look-at + key press + timeout in one call.

**Hold mechanics (charge, sprint, aim):**
```
editor_cmd(command="inject_input_sequence", params={
  steps: [
    {at_ms: 0,    kind: "key", key: "LeftShift", action: "press"},
    {at_ms: 2000, kind: "key", key: "LeftShift", action: "release"}
  ]
})
```
Follow with `observe_game_state` to confirm stamina drain, sprint state, etc.

**Combo / timed sequence:**
```
editor_cmd(command="inject_input_sequence", params={
  steps: [
    {at_ms: 0,   kind: "key", key: "R",              action: "tap"},
    {at_ms: 500, kind: "key", key: "LeftMouseButton", action: "tap"}
  ]
})
```

**Input failure signatures:**
- `dispatched: true` but no game state change → input reached Slate but was not bound / no game mode active
- `PIE_NOT_ACTIVE` error → PIE stopped or was never started
- `INVALID_FIELD` error → bad key name or action string (fix the scenario)
- `wait_for_condition` timeout after input → mechanic not responding; file as MAJOR

**Known limitation:** `editor_cmd(command="inject_key", ...)` and `editor_cmd(command="inject_input_sequence", ...)` only confirm Slate dispatch, not game receipt. Always verify effects with `observe_game_state` or `wait_for_condition` after injecting input.

**Typed/sustained Enhanced Input:**
```python
editor_cmd(command="inject_input_continuous", params={
    "action_name": "/Game/Input/IA_Move.IA_Move",
    "value": {"x": 0, "y": 1},
    "mode": "start"
})
# Observe the mechanic through QA state/assertions before declaring success.
editor_cmd(command="inject_input_continuous", params={
    "action_name": "/Game/Input/IA_Move.IA_Move", "mode": "stop"
})
```
Use the actual loaded action path and its value type; axis meanings come from the
project's binding, not Cortex. `inject_input_action` lasts one frame. Continuous
start/update/stop normally return immediately; optional positive start-only duration
defers until expiry/cancellation and must fit the native float delay.
Input values must be actual JSON numbers, not numeric strings; Axis1D must fit float.
Update cannot acquire another subsystem's injection. Stop is idempotent for unowned
actions and does not cancel game-managed injection. `injecting` describes Cortex
ownership, not every native injection. Disconnect/PIE end cancels owned runs.
Native values are queued for a subsequent world tick; already queued input can
drain after stop. A successful response does not prove a binding/mechanic reacted.
Session-wide ownership is not multi-agent isolation.

For visual assertions, inspect screenshot `view`, `pie_active`, `camera_available`
and `camera_provenance`. A PIE world can exist while the active view is editor/SIE;
game-view camera pose is unavailable. Default camera mutation rejects possessed
PIE. Its explicit override affects only a transient editor client, not game camera.


## Session Recording and Replay (Moved to CortexReplay)

QA no longer records or replays input; the legacy QA recording commands were removed in the
CortexReplay cutover. Recorded physical-input replay now belongs to the `replay` domain
(`cortex-replay` skill, `replay_cmd`), where a human captures and enables a recording and an AI
replays it once under fixed press-only guards.

- QA keeps its semantic surface: `move_to`, `interact`, `wait_for`, `assert_state`, `qa_test_step`,
  `scenario_compose`.
- AI replay is one-shot and never retried; recover an unknown start through `list_recordings` /
  `get_run`, then report the terminal `state`.
- `Completed` means the recorded sequence finished dispatching — it is not a gameplay pass/fail
  verdict, and there is no assertion/report artifact per event.
- Follow the `cortex-replay` skill and `resources/replay-workflow.md` for replay runs.

## Benchmark Tests

QA and Editor tool coverage in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_editor_e2e.py` | PIE lifecycle, viewport, screenshots, logs, console commands, time dilation |
| `test_editor_lifecycle.py` | Editor startup/shutdown integration |
| `test_qa_tools.py` | QA composites (move_player_to, interact_with, observe_game_state, wait_for_condition, assert_game_state) |

Run to validate after modifying Editor/QA MCP tools or C++ command handlers.

## Reporting

Each finding should include:
- summary
- severity
- repro steps
- observed evidence (state/log/screenshot)
