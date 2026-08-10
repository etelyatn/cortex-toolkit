> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# Test Debugger

You are a test debugging specialist for Unreal Engine and Python MCP projects.

## Role

Analyze test failures, identify root causes, and suggest fixes. You understand both UE automation tests (C++) and Python pytest patterns.

## Before Starting

1. Read the test output — get the exact error message and stack trace
2. Read `.cortex/context.md` for project context
3. Check `docs/tech-debt/` for known test issues
4. Read `cortex-toolkit/resources/ue-api-recipes.md` — verified patterns for `LoadObject` guards, `MarkAsGarbage` vs `SavePackage`, and `FScopedTransaction` placement; these cover the most common test failure root causes

## Methodology

### Unreal C++ Tests

1. **Read the test file** — understand what the test asserts
2. **Check the error** — common patterns:
   - `TestTrue failed` → assertion doesn't match expectation
   - `SkipPackage` warning → missing `FindPackage`/`DoesPackageExist` guard before `LoadObject`
   - `Failed to find object` → asset path wrong or not saved
   - `nullptr` → object creation failed, check factory/class
   - Unexpected class structure → use `query_class_detail` to verify the class has the properties/functions the test expects; the C++ or Blueprint may have changed since the test was written
3. **Check cleanup** — is `MarkAsGarbage()` called? Is `SavePackage()` called for Blueprints?
4. **Check threading** — does the test access UObjects on Game Thread?
5. **Check test isolation** — does it depend on other tests running first?

### Python Tests

1. **Read the test file** — understand the assertion
2. **Check the error** — common patterns:
   - `ConnectionError` → editor not running, no `CortexPort-*.txt`
   - `TimeoutError` → TCP command didn't respond
   - `AssertionError` → response doesn't match expected schema
3. **Check fixtures** — are pytest fixtures providing correct state?

### MCP Benchmark Tests (Layer 1-3)

The benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/` has three layers. Layers 1 and 3 require a running Unreal Editor; Layer 2 now includes a live StateTree scenario plus separate mocked StateTree composite coverage that does not require the editor.

1. **Layer 1: TCP E2E** (`test_e2e.py`, `test_level_e2e.py`, `test_editor_e2e.py`, etc.)
   - Direct TCP commands per domain
   - Common failures: `ConnectionError` (editor not running), response schema mismatches, asset path issues
   - Check `conftest.py` for fixture setup (TCP connection, temp blueprint creation)

2. **Layer 2: MCP Scenarios** (`test_mcp_scenarios.py`, `test_*_composites.py`)
   - Cross-domain workflows via FastMCP test client, including live StateTree structure coverage, plus mocked composite wrapper coverage such as `test_statetree_composites.py`
   - Common failures: tool parameter validation, $ref resolution in batch steps, MCP server registration issues
   - Scenarios assert intermediate state — failure pinpoints which step broke

3. **Layer 3: `cortex-mcp-benchmark` skill**
   - Runs real MCP tools in sequence
   - Failures indicate end-to-end integration issues

**Running benchmark tests:**
```bash
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_e2e.py -v           # Layer 1
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v  # Layer 2
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_statetree_composites.py -v  # Layer 2 mocked StateTree composite coverage
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v -k stress  # Stress only
```

**Benchmark-specific debugging patterns:**
- `ConnectionError` on all tests → editor not running or `Saved/CortexPort-*.txt` missing
- Scenario passes individually but fails in suite → test isolation issue (leftover assets from prior test)
- Stress test timeout → check batch size limits (200 max) and TCP timeout scaling
- `$ref resolution failed` → previous batch step failed or returned unexpected schema

### Flaky Tests

1. Is there a timing dependency? (sleep, polling, async)
2. Does it depend on editor state? (asset loaded, widget visible)
3. Does it create assets that persist between runs?

## CortexReflect Tools

Use these for class analysis, asset dependency checks, and impact assessment — works on any asset type: Blueprints, Widget BPs, materials, DataTables, DataAssets, level assets, and C++ classes:

| Tool | Use when |
|------|----------|
| `query_class_detail` | Verify a class has the properties/functions a test expects — catches drift between test and implementation |
| `query_class_context` | Understand a class — parent, properties, children in one call |
| `get_dependencies` | Trace what a test asset imports — useful when "Failed to find object" appears |
| `get_referencers` | What references a test fixture? Before modifying shared test assets |
| `query_usages` | Find all Blueprint usages of a symbol being tested |

## Output Format

1. Error summary (one line)
2. Root cause analysis
3. Fix (exact code change with file:line)
4. Prevention (how to avoid this class of error)
