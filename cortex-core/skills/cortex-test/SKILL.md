---
name: cortex-test
description: Use when running automation tests, checking test results, or after code changes that need verification. Accepts optional domain parameter like cortex-test Data
---

# Cortex Test

Unified dual-track test runner for Unreal C++ and Python MCP tests.

## Usage

- `cortex-test` — run both tracks
- `cortex-test Data` — Unreal `Cortex.Data+` tests only
- `cortex-test python` — Python MCP tests only
- `cortex-test e2e` — Python E2E tests (ensures editor running first)

## Steps

### 1. Determine Test Track

Parse the argument:
- No argument → run both tracks
- Domain name (Data, Core, Graph, Blueprint, UI) → Unreal tests for that domain
- `python` → Python unit tests
- `e2e` → Python E2E tests

### 2. Unreal C++ Tests

Run via PowerShell test runner:
```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 'Cortex.<Domain>+' }"
```

For all domains, omit the filter or use `Cortex+`.

**Quick status check** (no re-run):
```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 -ReportOnly }"
```

**Zero warnings required** — treat any warnings as failures.

### 3. Python MCP Tests

Check for test dependencies:
```bash
cd Plugins/UnrealCortex/MCP && uv run pytest tests/ -v
```

For E2E tests, first verify the editor is running (check `Saved/CortexPort.txt` exists). If not running, tell the user to start it or use `/cortex-editor`.

### 4. Report Results

Report:
- Which track(s) ran
- Pass/fail counts per track
- Any failures with file:line and error message
- Overall verdict: PASS or FAIL
