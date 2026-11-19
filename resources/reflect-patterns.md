# Reflect Patterns

Common patterns and best practices for using CortexReflect tools effectively.

## Starting a Session

Always check cache freshness first:

```python
reflect_cache_status()
# If stale or not cached:
scan_project(root="AActor")  # ~2-5 seconds
```

## Detail Levels

Use the right detail level to minimize tokens:

| Level | Fields returned | Use when |
|-------|----------------|----------|
| `summary` | name, type, parent, module, source_path, blueprint_children_count | Browsing hierarchy, listing classes |
| `properties` | + properties, interfaces, components | Working with variables or struct layout |
| `full` | + functions | Function signatures, override analysis |

```python
# Quick overview — minimal tokens
reflect_cmd(command="class_detail", params={"class_name": "AMyCharacter", "detail": "summary"})

# Properties / interfaces / components (native full read, functions projected out)
reflect_cmd(command="class_detail", params={"class_name": "AMyCharacter", "detail": "properties"})

# Full analysis
reflect_cmd(command="class_detail", params={"class_name": "AMyCharacter", "detail": "full", "include_inherited": True})
```

`reflect_cmd(command="class_detail", params={...})` accepts `summary|properties|full` and forwards
the read to the native `reflect.class_detail` command, whose **default is `full`** and which itself
accepts only `summary`/`full`. The routed `properties` level maps to a native full read with function
signatures projected out in Python (the router keeps the former wrapper view); it is the cheapest way
to read properties, interfaces and components, including inherited members
(`include_inherited: true` is forwarded). An unknown `detail` value reaches the native validator and
refuses `INVALID_FIELD` instead of degrading to the expensive full read. Use `detail="summary"` for a
lightweight identity/parent read, and `query_class_context(...)` when you want parent + self +
children in one call (its self view accepts `summary|properties|full` but hardcodes
`include_inherited=false`).

## Common Patterns

### Understand a class hierarchy

```python
reflect_cmd(command="class_hierarchy", params={"root": "ACharacter", "depth": 3, "include_blueprint": True})
```

Returns the nested class tree — traverse `children`. Every node carries `name` and `type`;
Blueprint classes add `asset_path`, C++ classes add `module`/`source_path` when the native lower
provides them, and `children` appears when the walk recursed. `include_flat_classes=true` adds an extra `classes` array of class
**names** only (no parent/depth records), useful as a quick name list. Counts and a `truncated` flag
are always present. `truncated` is the authoritative completeness signal: the `max_results` budget is
shared by the whole recursive walk, so a short list does not prove the hierarchy is complete, and
there is no pagination — re-request with a larger `max_results`/`depth`.

### Full class context in one call

```python
query_class_context("AMyCharacter", detail="properties")
# Returns: parent summary + self at properties level + children summaries
```

Saves 3 separate calls. Use this as the default for "tell me about class X".

### Before refactoring — check blast radius

For a full risk assessment before breaking changes, use `impact_analysis`:

```python
impact_analysis(
    target_class="AMyCharacter",
    symbol="Health",
    change_type="removed_function"  # removed_function | deleted_class | changed_property
)
# Returns: affected Blueprints grouped by severity (high/medium/low),
# with exact node IDs, reference types, and unscanned count
```

For a quick "is anything using this?" check (no graph scan, instant):

```python
reflect_cmd(command="get_referencers", params={"asset_path": "/Game/Blueprints/BP_MyCharacter"})
# Returns: all assets that reference this one via the Asset Registry, plus INI/config rows
# ({type: "config", file, line, section, key}, listed first); pass include_config=False to drop them
```

For forward dependencies ("what does this asset pull in?"):

```python
reflect_cmd(command="get_dependencies", params={"asset_path": "/Game/Blueprints/BP_MyCharacter"})
# Returns: parent classes, referenced meshes, materials, other Blueprints
```

Use `reflect_cmd(command="find_usages", params={...})` directly only when you need graph-level detail for a specific symbol without the full risk scoring overhead.

### Project-wide dependency map (migration waves, config, by-name access, duplicates)

For many Blueprints at once use the file-backed `reflect_cmd` commands; each writes its full result to `out_path` (under the project `Saved`, `Content` or `Config`) and answers with a compact summary:

```python
# Typed dependency graph with a wave order (hard kinds inherits/implements/struct_use/enum_use/
# widget_tree_child/listview_entry order the waves; soft kinds only when named in ordering_kinds)
reflect_cmd(command="export_dependency_graph", params={
    "path_prefixes": ["/Game/MyGame"], "out_path": "Saved/Migration/deps.json"})

# Config (INI) references whose package or directory no longer exists; takes no parameters
reflect_cmd(command="find_broken_config_paths", params={})

# By-name access that references cannot see (string-literal FindFunction/SetTimerByFunctionName/...);
# literal-only, so an empty result is not proof of absence
reflect_cmd(command="find_name_lookups", params={
    "path_prefixes": ["/Game/MyGame"], "out_path": "Saved/Migration/name_lookups.json"})

# Duplicated graphs: exact groups are strict, similar groups are loose (native-ancestor descriptors)
reflect_cmd(command="find_duplicate_graphs", params={
    "path_prefixes": ["/Game/MyGame"], "min_nodes": 5, "similarity": 0.9,
    "out_path": "Saved/Migration/duplicates.json"})
```

Read the file for detail; the response only carries counts and the first entries. See `resources/mcp-tool-reference.md` ("Dependency map commands") for every field.

### Interface implementers/callers and user-type usage (migration inventories)

Read-only, file-backed, matched by **resolved owner** (never by member name); both load every candidate Blueprint, so pass `out_path` for a project-wide run:

```python
# Who implements a BPI (or a native interface) and who calls it: message / typed_call / interface_cast sites
reflect_cmd(command="find_interface_implementers", params={
    "interface": "/Game/Interfaces/BPI_StressApplier",     # or /Script/MyGame.StressApplierInterface
    "path_prefixes": ["/Game/MyGame"], "out_path": "Saved/Migration/bpi_stress.json"})
# implementers[]: asset_path, direct (false = inherited, `via` names the ancestor),
#   functions[]: implementation = function_graph | event | none (+ graph_guid, entry_node_guid, node_count / has_body)
# callers[]: kind, asset_path, graph_guid, subgraph_path, node_guid, node_class, function; unresolved_callers[] need manual review
# "include_callers": False lists implementers only; "function": "ApplyStress" restricts one function (cast sites stay)

# Where a user struct/enum is used, by category (variable, pin, make_struct, datatable_row_struct, data_asset, ...)
reflect_cmd(command="find_type_usages", params={
    "user_type": "/Game/Data/UDS_StressRow", "path_prefixes": ["/Game/MyGame"],
    "out_path": "Saved/Migration/uds_stress.json"})
# load_failures and skipped_assets are never "free of the type"; run again with the native type afterwards
```

Next steps: `resources/cpp-migration.md` ("Interface and user-type replacement") for the wave procedure and `resources/mcp-tool-reference.md` for every field.

### Find what Blueprint children override

```python
reflect_cmd(command="find_overrides", params={"class_name": "AMyCharacter", "depth": 2})
# Returns: per-child list of overridden functions, events, custom additions
```

### Search for classes by name pattern

```python
# reflect_cmd(command="class_hierarchy", params={"root": ...}) with a specific root is preferred
# For pattern search, use search_assets for Blueprint assets
```

## Performance Tips

- Use `max_results` to cap large hierarchies (default 100)
- Use `path_filter` in `reflect_cmd(command="find_usages", params={...})` to scope scans: `path_filter="/Game/Characters/"`
- Use `max_blueprints=20` for quick scans, `50` (default) for thorough coverage
- Routed Reflect reads are not TTL-cached: every `reflect_cmd` hierarchy/detail/usages call goes to
  the editor, so request only the level you need (`detail="summary"`, a bounded `max_results`/`depth`)
- `find_usages` defaults to `limit=20` with `max_blueprints=50`; raise them deliberately for a thorough scan

## Class Name Formats

CortexReflect accepts three formats:

```python
# Short C++ name (prefix optional)
reflect_cmd(command="class_detail", params={"class_name": "ACharacter"})
reflect_cmd(command="class_detail", params={"class_name": "Character"})   # same result

# Full C++ name with prefix
reflect_cmd(command="class_detail", params={"class_name": "AMyCharacter"})

# Blueprint asset path
reflect_cmd(command="class_detail", params={"class_name": "/Game/Blueprints/BP_MyCharacter"})
```

## Cache Management

```python
# Check freshness
reflect_cache_status()
# → {"cached": true, "age_seconds": 120, "class_count": 47, "stale": false}

# Full rescan (after adding new C++ classes)
rebuild_graph_cache()

# Targeted rescan with custom root
scan_project(root="UObject")  # Everything
scan_project(root="AActor")   # Actors only (faster, default)
```

## Benchmark Tests

Reflect domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_reflect_tools.py` | All reflect tools: cache_status, scan_project, class_hierarchy, class_detail, query_class_context, find_overrides, find_usages, get_dependencies, get_referencers, impact_analysis, rebuild_graph_cache |

Run to validate after modifying Reflect MCP tools or C++ command handlers.
