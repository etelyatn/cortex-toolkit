# Scenario Format

Reference format for inline or file-based QA scenarios.

## Minimal JSON Shape

```json
{
  "name": "door-smoke-test",
  "steps": [
    {"command": "qa.look_at", "params": {"target": "Door_A"}},
    {"command": "qa.move_to", "params": {"target": "Door_A", "timeout": 10.0}},
    {"command": "qa.interact", "params": {"key": "E"}},
    {"command": "qa.wait_for", "params": {"type": "actor_property", "actor": "Door_A", "property": "bOpen", "value": true, "timeout": 3.0}},
    {"command": "qa.assert_state", "params": {"type": "actor_property", "actor": "Door_A", "property": "bOpen", "expected": true}}
  ]
}
```

## With Direct Input Injection

Use `editor.inject_key` or `editor.inject_input_sequence` when `qa.interact` is insufficient (multi-key combos, hold mechanics, timed sequences):

```json
{
  "name": "sprint-jump-test",
  "steps": [
    {"command": "qa.move_to", "params": {"target": "SprintTestStart", "timeout": 10.0}},
    {"command": "editor.inject_input_sequence", "params": {
      "steps": [
        {"at_ms": 0,    "kind": "key", "key": "LeftShift", "action": "press"},
        {"at_ms": 500,  "kind": "key", "key": "W",         "action": "press"},
        {"at_ms": 1000, "kind": "key", "key": "SpaceBar",  "action": "tap"},
        {"at_ms": 1500, "kind": "key", "key": "W",         "action": "release"},
        {"at_ms": 1600, "kind": "key", "key": "LeftShift", "action": "release"}
      ]
    }},
    {"command": "qa.wait_for", "params": {"type": "actor_property", "actor": "Player", "property": "bIsJumping", "value": true, "timeout": 3.0}},
    {"command": "qa.assert_state", "params": {"type": "actor_property", "actor": "Player", "property": "bIsJumping", "expected": true}}
  ]
}
```

## Notes

- Use flat params for `qa.wait_for` and `qa.assert_state`.
- Include explicit timeouts for deferred commands.
- Prefer short, atomic steps for easier triage.
- After any `editor.inject_*` step, always follow with `qa.wait_for` or `observe_game_state` to verify the game reacted — direct input tools only confirm Slate dispatch.
- Do not run two `editor.inject_input_sequence` commands concurrently (single callback slot limitation).
