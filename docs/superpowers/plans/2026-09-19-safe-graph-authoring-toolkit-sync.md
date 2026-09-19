# Safe Graph Authoring Toolkit Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Document safe graph-node and UMG designer-variable authoring in Cortex Toolkit's existing discovery and workflow guidance.

**Architecture:** Keep guidance colocated with existing tool discovery and domain workflows. The tool reference defines command availability and rollback boundaries; the Blueprint and UMG skills define their respective safe mutation sequences.

**Tech Stack:** Markdown, PowerShell, ripgrep.

## Global Constraints

- Modify only existing toolkit guidance plus this plan and its approved design specification.
- Do not add a standalone recovery guide or change UnrealCortex runtime behavior.
- New Widget Blueprints continue to use `widget_compose`.
- Rollback guidance must state that rollback is limited to supported graph node/link operations.

---

### Task 1: Publish Safe Authoring Guidance

**Files:**
- Modify: `resources/mcp-tool-reference.md:83-90,270-304,324-334`
- Modify: `skills/cortex-blueprint/SKILL.md:43-73`
- Modify: `skills/cortex-umg/SKILL.md:20-45`
- Test: targeted ripgrep assertions against the three Markdown files

**Interfaces:**
- Consumes: `core_cmd(command="batch_query", params={"commands": [...], "rollback_on_error": true, "verify_rollback": true})`
- Consumes: `graph_cmd(command="describe_node", params={"asset_path": "..."})`
- Consumes: `umg_cmd(command="set_widget_variable", params={"asset_path": "...", "widget_name": "...", "is_variable": true, "expected_fingerprint": {...}})`
- Produces: toolkit instructions that direct agents to inspect before authoring and accurately limit rollback claims.

- [ ] **Step 1: Run the documentation assertions before editing**

Run:

```powershell
$files = @('resources/mcp-tool-reference.md', 'skills/cortex-blueprint/SKILL.md', 'skills/cortex-umg/SKILL.md'); @('graph.describe_node', 'umg.set_widget_variable', 'rollback_on_error', 'expected_fingerprint') | ForEach-Object { if (-not (rg --fixed-strings --quiet $_ $files)) { "MISSING: $_" } }
```

Expected: `MISSING` output for the new safe-authoring terms.

- [ ] **Step 2: Add the tool-reference contract**

Add the following guidance in the Core, Graph, and UMG sections:

```markdown
`batch_query` accepts `rollback_on_error` and `verify_rollback`. Rollback is capability-gated and applies only to supported graph node/link operations; it does not undo pin-value, UMG, material, or other domain mutations.

Use `describe_node` before raw `add_node` authoring to inspect the accepted class, parameters, and pins. Correct an invalid request before attempting the mutation.

`set_widget_variable` changes the designer-variable flag on an existing Widget Blueprint. Inspect the current widget tree first and pass its current `expected_fingerprint`.
```

- [ ] **Step 3: Add Blueprint and UMG workflow requirements**

Add the following requirements without changing the existing composite-first rules:

```markdown
Before a raw `graph.add_node` mutation, call `graph_cmd(command="describe_node", ...)` for the target Blueprint. Use the returned contract to select accepted parameters and pin names; correct validation failures before retrying.

For an existing Widget Blueprint, inspect the current tree/fingerprint before calling `umg_cmd(command="set_widget_variable", ...)`, and pass `expected_fingerprint`. Use this only for an isolated designer-variable change; new screens still use `widget_compose`.
```

- [ ] **Step 4: Run documentation assertions after editing**

Run:

```powershell
$files = @('resources/mcp-tool-reference.md', 'skills/cortex-blueprint/SKILL.md', 'skills/cortex-umg/SKILL.md'); @('graph.describe_node', 'umg.set_widget_variable', 'rollback_on_error', 'expected_fingerprint') | ForEach-Object { if (-not (rg --fixed-strings --quiet $_ $files)) { throw "Missing required guidance: $_" } }; rg --fixed-strings --quiet 'does not undo pin-value, UMG, material, or other domain mutations' resources/mcp-tool-reference.md; if ($LASTEXITCODE -ne 0) { throw 'Missing rollback boundary.' }
```

Expected: command exits successfully with no output.

- [ ] **Step 5: Commit the documentation sync**

```powershell
git add resources/mcp-tool-reference.md skills/cortex-blueprint/SKILL.md skills/cortex-umg/SKILL.md docs/superpowers/plans/2026-09-19-safe-graph-authoring-toolkit-sync.md
git commit -m "docs: sync safe graph authoring guidance"
```
```
