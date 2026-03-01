---
name: cortex-impact
description: Assess the impact of removing, renaming, or changing a C++ member or Blueprint asset. Use before any breaking change to understand blast radius.
---

# Impact Analysis

Understand what breaks before you break it.

## Usage

`/cortex-impact TakeDamage AMyCharacter` - What breaks if I remove `TakeDamage`?
`/cortex-impact /Game/Blueprints/BP_BaseEnemy` - What depends on this Blueprint?

## Steps

### 1. Check Cache Freshness

Call `reflect_cache_status`. If stale (last scan > 30min ago), run `scan_project` first
so class hierarchy + usage scans are current.

### 2. Run Analysis

If symbol + class are provided:
- Call `impact_analysis` with `target_class`, `symbol`, and inferred `change_type`

If only an asset path is provided:
- Call `get_referencers` for a quick package-level dependency list
- For deeper analysis, map asset to class then call `impact_analysis`
  with `change_type="removed_class"`

### 3. Review Results

Present grouped by risk:
1. High risk - compile failures likely
2. Medium risk - runtime behavior likely impacted
3. Low risk - indirect/package-level links

### 4. Handle Partial Coverage

If `not_scanned.count > 0`, ask:

"{N} Blueprints were not scanned (not loaded in editor). Run deep scan for full coverage?"

If user agrees, re-run with `deep_scan=true`.

### 5. Suggest Next Steps

Recommend:
- Which Blueprints to update first (highest risk first)
- Whether the change is safe to proceed
- Safer alternatives when blast radius is too large
