// Cortex Toolkit plugin for OpenCode.ai.
// Registers the toolkit skills directory and injects session context.
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TOOLKIT_ROOT = path.resolve(__dirname, '../..');
const SKILLS_DIR = path.join(TOOLKIT_ROOT, 'skills');
const CONTEXT_MARKER = '# Cortex Project Context';

// Per-project-dir cache: { [projectDir]: { mtimeMs, text } }
const contextCache = new Map();

function assembleContext(projectDir) {
  const parts = ['# Cortex Project Context', ''];
  const contextFile = path.join(projectDir, '.cortex', 'context.md');
  if (fs.existsSync(contextFile)) {
    parts.push(fs.readFileSync(contextFile, 'utf8'));
    parts.push('');
  }
  const domainDir = path.join(projectDir, '.cortex', 'domains');
  if (fs.existsSync(domainDir)) {
    const domains = fs.readdirSync(domainDir)
      .filter((f) => f.endsWith('.md'))
      .map((f) => f.slice(0, -3))
      .sort();
    if (domains.length) {
      parts.push('## Available Domain Contexts', '', 'Read these files when working in a specific domain:');
      for (const d of domains) parts.push(`- \`.cortex/domains/${d}.md\``);
      parts.push('');
    }
  }
  const configFile = path.join(projectDir, '.cortex', 'config.yaml');
  if (fs.existsSync(configFile)) {
    parts.push(
      '## Project Configuration',
      '',
      'See `.cortex/config.yaml` for shared engine defaults, active domains, and doc references.',
      'Optional per-machine overrides live in ignored `.cortex/config.local.yaml`.'
    );
  }
  return parts.join('\n');
}

const TRUTHY = new Set(['true', 'True', 'TRUE', 'yes', 'Yes', 'YES', 'on', 'On', 'ON', '1']);

// Opt-in gate mirroring hooks/hook-config.sh: session context is disabled
// unless hooks.session_context is truthy in .cortex/config.yaml, with a
// per-machine override in .cortex/config.local.yaml. A key line present in
// config.local.yaml — even with an empty or comment-only value — shadows
// config.yaml and evaluates to disabled.
function hookEnabled(projectDir, key) {
  const assignment = new RegExp(`^[ \\t]*${key}[ \\t]*:[ \\t]*([^#\\s]+)`, 'm');
  const emptyAssignment = new RegExp(`^[ \\t]*${key}[ \\t]*:[ \\t]*(#.*)?$`, 'm');
  for (const file of ['config.local.yaml', 'config.yaml']) {
    const configPath = path.join(projectDir, '.cortex', file);
    if (!fs.existsSync(configPath)) continue;
    const text = fs.readFileSync(configPath, 'utf8');
    const match = text.match(assignment);
    if (match) return TRUTHY.has(match[1]);
    if (emptyAssignment.test(text)) return false;
  }
  return false;
}

function toolMapping() {
  return [
    '## OpenCode Tool Mapping',
    '- Load a skill -> use the native `skill` tool',
    '- Ask the user -> use the `question` tool',
    '- Read / edit / delete a file -> `read` / `edit` / `write`',
    '- Run a shell command -> `bash`',
    '- Search file contents / find by name -> `grep` / `glob`',
    '- Fetch a URL -> `webfetch`',
    '',
    'Cortex MCP tools (prefixed `cortex_mcp_`) require the Unreal Editor running with CortexCore.',
    'If a `cortex_mcp_*` call fails with a connection error, load the `cortex-setup` skill to',
    'diagnose and the `cortex-editor` skill to start it.'
  ].join('\n');
}

export const CortexPlugin = async ({ directory }) => {
  const projectDir = directory;

  function getBootstrap() {
    const ctxFile = path.join(projectDir, '.cortex', 'context.md');
    let mtimeMs = 0;
    if (fs.existsSync(ctxFile)) mtimeMs = fs.statSync(ctxFile).mtimeMs;
    const cached = contextCache.get(projectDir);
    if (cached && cached.mtimeMs === mtimeMs) return cached.text;
    const text = assembleContext(projectDir) + '\n\n' + toolMapping() + '\n';
    contextCache.set(projectDir, { mtimeMs, text });
    return text;
  }

  function getProjectContextOnly() {
    return assembleContext(projectDir);
  }

  return {
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(SKILLS_DIR)) {
        config.skills.paths.push(SKILLS_DIR);
      }
    },

    'experimental.chat.messages.transform': async (_input, output) => {
      if (!hookEnabled(projectDir, 'session_context')) return;
      if (!output.messages || !output.messages.length) return;
      const firstUser = output.messages.find((m) => m.info.role === 'user');
      if (!firstUser || !firstUser.parts.length) return;
      if (firstUser.parts.some((p) => p.type === 'text' && p.text.includes(CONTEXT_MARKER))) return;
      const ref = firstUser.parts[0];
      firstUser.parts.unshift({ ...ref, type: 'text', text: getBootstrap() });
    },

    'experimental.session.compacting': async (_input, output) => {
      if (!hookEnabled(projectDir, 'session_context')) return;
      output.context = output.context || [];
      output.context.push(getProjectContextOnly());
    }
  };
};
