# Testing Guide

Dual-track testing patterns for UnrealCortex projects.

## Philosophy

- **TDD required:** Red-Green-Refactor — test must fail before implementation
- **Zero warnings:** All tests must be fully green, no warnings
- **Two tracks:** Unreal C++ automation tests + Python MCP server tests

## Track 1: Unreal C++ Tests

### Running

```bash
# Run domain tests
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 'Cortex.Data+' }"

# Quick status (no re-run)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 -ReportOnly }"
```

### Namespaces

- `Cortex.Core+` — CortexCore foundation
- `Cortex.Data+` — CortexData domain
- `Cortex.Graph+` — CortexGraph domain
- `Cortex.Blueprint+` — CortexBlueprint domain
- `Cortex.UI+` — CortexUI domain

Note: Use `+` wildcard, never `*`.

### Patterns

- Tests live in `Source/{Module}/Private/Tests/`
- One test class per operation or feature
- Use `IMPLEMENT_SIMPLE_AUTOMATION_TEST_PRIVATE` macro
- Cleanup: `MarkAsGarbage()` for all created UObjects
- Blueprint tests: call `SavePackage()` after creation
- Guard `LoadObject` with `FindPackage` + `DoesPackageExist`
- Use `AddInfo` for skip conditions, not `AddWarning`

## Track 2: Python MCP Tests

### Running

```bash
cd Plugins/UnrealCortex/MCP
uv run pytest tests/ -v           # all tests
uv run pytest tests/test_cache.py  # specific file
```

First run: `uv add --dev pytest pytest-cov`

### E2E Tests

Require running UE editor (`Saved/CortexPort.txt` must exist):
```bash
uv run pytest tests/test_e2e.py -v
```

### Patterns

- Unit tests: mock TCP connection, test tool logic
- E2E tests: real editor connection, test full chain
- Use pytest fixtures for shared setup
- Test response schemas match documented format
