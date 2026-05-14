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
- `Cortex.UMG+` — CortexUMG domain
- `Cortex.Level+` — CortexLevel domain (requires rendering, no `-NullRHI`)
- `Cortex.Reflect+` — CortexReflect domain
- `Cortex.Editor+` — CortexEditor shared infrastructure (requires rendering, no `-NullRHI`)
- `Cortex.QA+` — CortexQA domain (requires rendering and test level content)
- `Cortex.StateTree+` — CortexStateTree domain

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

Require running UE editor (`Saved/CortexPort-*.txt` must exist):
```bash
uv run pytest tests/test_e2e.py -v
```

### Patterns

- Unit tests: mock TCP connection, test tool logic
- E2E tests: real editor connection, test full chain
- Use pytest fixtures for shared setup
- Test response schemas match documented format

## Track 3: MCP Benchmark Tests

Three-layer integration testing framework that validates the full AI-to-Unreal pipeline. All layers require a running Unreal Editor.

### Layer 1: TCP E2E Tests (per-domain)

Direct TCP commands testing CRUD lifecycle and error cases for each domain.

```bash
# All domains
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_e2e.py -v

# Domain-specific E2E files
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_level_e2e.py -v
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_editor_e2e.py -v
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_class_defaults.py -v
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_material_composites_e2e.py -v
```

**Covered domains:** Core, Data, Blueprint, Graph, Level, Editor, Material, CDO/Class Defaults

### Layer 2: MCP Scenario Tests (cross-domain)

Multi-step workflow tests via FastMCP test client. Tests the full Python MCP stack: tool registration, parameter validation, response formatting.

```bash
# All scenarios
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v

# Scenarios only (no stress)
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v -k "not stress"

# Stress tests only
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v -k stress

# StateTree composites
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_statetree_composites.py -v
```

**Scenarios:** Blueprint Lifecycle, Widget Builder, Data Pipeline, Graph Wiring, GameplayTag Workflow, Localization Pipeline

**Stress tests:** Bulk blueprint create, large widget trees, many graph nodes, rapid data operations, concurrent batch

### Layer 3: `/mcp-benchmark` Skill

Claude Code skill that calls real MCP tools in sequence and reports pass/fail with timing. Tests the full AI-to-MCP-to-Unreal path.

```
/mcp-benchmark              # leave test assets for visual inspection
/mcp-benchmark --cleanup    # auto-delete test assets after verification
```

**Benchmark checks:** Connection, Data Catalog, Blueprint CRUD, Graph Wiring, Widget Build, Material Create, Batch Pipeline, Data Operations, Tag Validation, Editor Domain, Level Operations, Reflect

### Test File Map

| File | Layer | Domain Coverage |
|------|-------|-----------------|
| `test_e2e.py` | 1 | Core, Data, Blueprint, Graph, UMG |
| `test_level_e2e.py` | 1 | Level (actors, transforms, components, queries, batch) |
| `test_level_batch.py` | 1 | Level batch API |
| `test_editor_e2e.py` | 1 | Editor (PIE, viewport, screenshots, logs) |
| `test_class_defaults.py` | 1 | CDO get/set class defaults |
| `test_material_composites_e2e.py` | 1 | Material property setters, enum aliases |
| `test_graph_layout.py` | 1 | Graph layout engine stress |
| `test_mcp_scenarios.py` | 2 | Cross-domain scenarios + stress tests |
| `test_blueprint_composites.py` | 2 | Blueprint composite tool workflows |
| `test_material_composites.py` | 2 | Material composite tool workflows |
| `test_umg_composites.py` | 2 | UMG composite tool workflows |
| `test_statetree_composites.py` | 2 | StateTree composite create/update, cleanup, and preflight |
| `test_qa_tools.py` | 2 | QA domain tool integration |
| `test_reflect_tools.py` | 2 | Reflect domain tool integration |
| `conftest.py` | -- | Shared fixtures (TCP connection, MCP client, temp assets) |

### Pytest Markers

```python
@pytest.mark.e2e          # requires running editor
@pytest.mark.stress        # long-running performance tests
@pytest.mark.scenario      # multi-step workflow tests
```

### Asset Namespace

All benchmark test assets are created under `Content/Temp/CortexMCPTest/` with unique names (UUID suffixes) to avoid cross-run collisions. Layer 1 and 2 auto-cleanup in pytest teardown.

### When to Run Benchmarks

- After adding new MCP tools or modifying tool parameters
- After changing TCP command handlers in C++
- After modifying the Python MCP server or tool registration
- Before releases to validate full integration
- When debugging cross-domain workflow failures
