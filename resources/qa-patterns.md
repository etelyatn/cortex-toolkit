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
run_input_sequence: [
  {at_ms: 0,    kind: "key", key: "LeftShift", action: "press"},
  {at_ms: 2000, kind: "key", key: "LeftShift", action: "release"}
]
```
Follow with `observe_game_state` to confirm stamina drain, sprint state, etc.

**Combo / timed sequence:**
```
run_input_sequence: [
  {at_ms: 0,   kind: "key", key: "R",         action: "tap"},
  {at_ms: 500, kind: "key", key: "LeftMouseButton", action: "tap"}
]
```

**Input failure signatures:**
- `dispatched: true` but no game state change → input reached Slate but was not bound / no game mode active
- `PIE_NOT_ACTIVE` error → PIE stopped or was never started
- `INVALID_FIELD` error → bad key name or action string (fix the scenario)
- `wait_for_condition` timeout after input → mechanic not responding; file as MAJOR

**Known limitation:** Direct input tools (`press_key`, `run_input_sequence`) only confirm Slate dispatch, not game receipt. Always verify effects with `observe_game_state` or `wait_for_condition` after injecting input.

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
