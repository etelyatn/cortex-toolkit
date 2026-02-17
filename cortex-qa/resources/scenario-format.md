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

## Notes

- Use flat params for `qa.wait_for` and `qa.assert_state`.
- Include explicit timeouts for deferred commands.
- Prefer short, atomic steps for easier triage.
