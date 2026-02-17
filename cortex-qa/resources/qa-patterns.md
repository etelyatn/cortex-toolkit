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

## Reporting

Each finding should include:
- summary
- severity
- repro steps
- observed evidence (state/log/screenshot)
