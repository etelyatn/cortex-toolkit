---
name: cortex-help
description: Use when the user asks for help, wants to discover available commands, is unsure what to do next, or says "what can I do?" or "what should I do next?"
---

# Cortex Help

Discoverability and contextual guidance for the Cortex Toolkit.

Use skill names directly in instructions (for example `cortex-help all`).

## Argument Parsing

Check the arguments passed to this skill:
- No arguments → **Advisor Mode** (default)
- `all` → **Catalog Mode**
- Domain keyword → **Domain Mode** (see domain mapping below)
- Unrecognized argument → Fall back to **Advisor Mode** and mention: "No domain called '{arg}'. Run cortex-help all to see all commands."

**Domain mapping (accept aliases):**

| Argument | Domain |
|----------|--------|
| `data` | data |
| `blueprint`, `bp` | blueprint |
| `material`, `mat` | material |
| `ui`, `umg` | ui |
| `level` | level |
| `statetree`, `st` | statetree |
| `qa`, `test` | qa |
| `setup`, `infra` | setup |

---

## Advisor Mode (no arguments)

Gather these signals via file reads only — no MCP calls:

### Signal Gathering

1. **Project initialized?** Check if `.cortex/config.yaml` exists
2. **Editor running?** Check if a `Saved/CortexPort-*.txt` port file exists. If yes, read the port number.
3. **Schema freshness?** Check if `.cortex/schema/` exists. If yes, check modification time of files inside it.
4. **Content inventory?** Check which `Content/` subdirectories exist:
   - `Content/Data/` → count `.uasset` files
   - `Content/Blueprints/` → count `.uasset` files
   - `Content/Materials/` → count `.uasset` files
   - `Content/UI/` → count `.uasset` files
   - `Content/AI/StateTrees/` or `Content/StateTrees/` → count `.uasset` files
   - `Content/Maps/` → note map files
5. **Conversation context?** Review the current conversation for domain keywords or recent task context.

### Signal Priority

Generate 2-3 suggestions in this priority order:

1. **Broken infrastructure** → fix first
   - No `.cortex/config.yaml` → suggest `cortex-init`
   - No `Saved/CortexPort-*.txt` → suggest `cortex-editor`
2. **Missing setup** → suggest setup
   - No `.cortex/schema/` or schema older than 7 days → suggest `cortex-schema-refresh`
   - Empty `.cortex/context.md` (still has template comments) → suggest filling it in
3. **Active work context** → suggest next step
   - User just created something → suggest the matching review skill
   - User working in a domain → suggest related skills
4. **No context** → suggest exploration
   - Has DataTables → suggest `cortex-data`
   - Has Blueprints → suggest `cortex-blueprint`
   - Has StateTrees → suggest `cortex-statetree`
   - Nothing detected → suggest `cortex-start`

### Output Format

Print exactly this structure (15-30 lines):

```
Cortex Toolkit

Editor: {connected (port XXXX) | not running} | Schema: {age or "not generated"}

Suggested Next Steps

1. {Title} — {Rationale with specific numbers}.
   Run `cortex-<name>` to {action description}.

2. {Title} — {Rationale}.
   Run `cortex-<name>` to {action description}.

3. {Title} — {Rationale}.
   Run `cortex-<name>` to {action description}.

---
All commands: cortex-help all | Domain help: cortex-help <domain>
```

**Rules:**
- Never show more than 3 suggestions
- Every suggestion must trace to a detected signal — never fabricate
- Use plain language in suggestions ("data definitions" not "schema"), though "Schema" is acceptable in the status line
- Include specific numbers when available ("12 Blueprints" not "some Blueprints")

---

## Catalog Mode (`all` argument)

Print this complete reference grouped by workflow stage:

```
All Commands

Setup & Infrastructure
  cortex-init              Initialize project configuration
  cortex-editor            Open Unreal Editor
  cortex-build             Build the project
  cortex-status            Check editor connection, module status, and connection recovery
  cortex-restart           Restart the Unreal Editor
  cortex-schema-refresh    Regenerate project schema from live editor

Domains
  cortex-blueprint         Create, modify, review, or debug Blueprints — structure, graphs, variables, functions, best practices
  cortex-data              Create, populate, or review DataTables, DataAssets, CurveTables, or StringTables — including balance and integrity checks
  cortex-material          Create or review materials, instances, parameter collections, or material graphs
  cortex-ui                Create or review UMG widgets, screens, or UI components
  cortex-level             Place, organize, or review actors in a level
  cortex-statetree         Create, update, review, validate, or compile StateTree assets
  cortex-reflect           Assess blast radius before breaking changes, or analyze class architecture and cross-references

Test & QA
  cortex-test              Run Unreal or Python tests
  cortex-qa-init           Set up QA test scenarios
  cortex-qa-run            Execute automated QA scenarios
  cortex-qa-interactive    Interactive game testing session

Learn & Migrate
  cortex-start             Guided onboarding with a real task
  cortex-bp-migrate        Migrate Blueprints to C++ — 4-stage pipeline with hard gates (ANALYZE → PLAN → EXECUTE → COMPLETE)

---
Domain help: cortex-help <domain> (data, bp, mat, ui, level, statetree, qa, setup)
```

No signal gathering needed. Print the catalog and stop.

---

## Domain Mode (domain keyword argument)

### Signal Gathering

For the requested domain, gather:
1. **Content inventory** — count assets in the relevant `Content/` subdirectory
2. **Schema status** — check if domain-specific schema files exist in `.cortex/schema/`
3. **Domain context** — check if `.cortex/domains/{domain}.md` exists

### Domain Definitions

**data:**
- Skills: `cortex-data`, `cortex-reflect`, `cortex-schema-refresh`
- Content path: `Content/Data/`
- Schema files: `.cortex/schema/datatables.md`, `.cortex/schema/structs.md`, `.cortex/schema/tags.md`
- Domain context: `.cortex/domains/data.md`

**blueprint (bp):**
- Skills: `cortex-blueprint`, `cortex-bp-migrate`, `cortex-reflect`
- Content path: `Content/Blueprints/`
- Schema files: `.cortex/schema/blueprints.md`
- Domain context: `.cortex/domains/blueprints.md`

**material (mat):**
- Skills: `cortex-material`
- Content path: `Content/Materials/`
- Domain context: `.cortex/domains/material.md`

**ui (umg):**
- Skills: `cortex-ui`
- Content path: `Content/UI/`
- Domain context: `.cortex/domains/umg.md`

**level:**
- Skills: `cortex-level`
- Content path: `Content/Maps/`
- Domain context: `.cortex/domains/level.md`

**statetree:**
- Skills: `cortex-statetree`, `cortex-reflect`
- Content path: `Content/AI/StateTrees/` or `Content/StateTrees/`
- Domain context: `.cortex/domains/statetree.md`

**qa (test):**
- Skills: `cortex-qa-init`, `cortex-qa-run`, `cortex-qa-interactive`, `cortex-test`
- Domain context: `.cortex/domains/qa.md`

**setup (infra):**
- Skills: `cortex-init`, `cortex-editor`, `cortex-build`, `cortex-status`, `cortex-restart`, `cortex-schema-refresh`
- Note: No content path or schema. "Your Project" section should show infrastructure status instead: config exists/missing, editor connected/not, schema freshness.

### Output Format

```
{Domain Name} Domain

Skills
  cortex-<name>     {description}
  cortex-<name>     {description}

Your Project
  {N} {asset type} in {path}
  Schema: {status}
  Domain context: {exists or missing}

Suggested
  {One contextual suggestion based on detected content}
```

---
