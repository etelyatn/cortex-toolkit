# Balance Analysis Guide

Framework for analyzing game balance using MCP data tools.

## Analysis Process

1. **Define scope** — which system? (economy, combat, progression)
2. **Gather data** — extract all relevant tables via `batch_query`
3. **Map relationships** — identify how tables reference each other
4. **Check curves** — are progressions smooth? Use CurveTable data
5. **Find outliers** — values outside expected ranges
6. **Cross-validate** — income vs expense, player power vs enemy power

## Common Balance Checks

### Economy
- Total income per level bracket vs total expenses
- Rarest item price vs maximum earnable currency at that level
- Time-to-earn for key items at each tier

### Combat
- Player DPS vs enemy HP at each level
- Time-to-kill vs time-to-die ratio
- Healing throughput vs incoming damage

### Progression
- XP per level curve (should be smooth, typically polynomial or exponential)
- Power spikes at milestone levels
- Dead zones where nothing meaningful unlocks

## Useful MCP Tool Combinations

- `core_cmd(command="batch")` — pull multiple tables in one call for cross-analysis
- `data_cmd(command="get_curve_table")` — extract numeric curves for regression analysis
- `data_cmd(command="query_datatable")` — filter specific level ranges or categories
- `data_cmd(command="resolve_tags")` — understand tag hierarchies for categorized data

## Reporting Format

| Item | Table | Field | Current | Expected Range | Verdict |
|------|-------|-------|---------|----------------|---------|
| Sword of Fire | DT_Weapons | Damage | 150 | 80-120 | Over |

Include recommendations with specific values and reasoning.
