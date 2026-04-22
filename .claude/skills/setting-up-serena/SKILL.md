---
name: setting-up-serena
description: Installs and configures the Serena MCP server for Claude Code and Codex, including client MCP registration, the TypeScript LSP plugin, Claude Code hooks, and project onboarding. Use when the user asks to set up Serena, install Serena, configure Serena MCP, or enable symbolic code navigation. Trigger keywords: set up serena, install serena, configure serena, serena mcp, serena setup, symbolic tools, typescript lsp.
---

# Setting Up Serena

Serena is an MCP server that gives coding agents semantic,
symbol-level code intelligence. It replaces grep-based
search with precise go-to-definition, find-references, and
atomic rename across the codebase.

## When to Use

- User asks to install or configure Serena
- Serena MCP tools are unavailable in a session
- A new project needs Serena onboarding
- The TypeScript LSP is missing (Serena symbolic tools
  silently fail on `.ts`/`.tsx` without it)

## Instructions

### Step 1 — Install Serena

Requires `uv`. If `uv` is not installed, tell the user to
install it first: https://docs.astral.sh/uv/getting-started/installation/

```bash
uv tool install -p 3.13 serena-agent@latest --prerelease=allow
```

Then register Serena as a user-scoped MCP server in the
clients you use:

Claude Code:

```bash
claude mcp add --scope user serena -- \
  serena start-mcp-server --context claude-code \
  --project-from-cwd
```

Codex:

```bash
codex mcp add serena -- \
  serena start-mcp-server --context=codex \
  --project-from-cwd
```

Verify registration:

```bash
claude mcp list
codex mcp list
```

`serena` must appear in the output for each client you plan
to use.

### Step 2 — Install Claude Code Hooks

Add the following to `.claude/settings.json` (create the
file if it does not exist). Merge with any existing content
— do not overwrite other hooks.

See `references/hooks-config.md` for the full hooks block.

The hooks do four things:

| Hook | Command | Purpose |
|------|---------|---------|
| `PreToolUse` (all) | `serena-hooks remind` | Reminds Claude to prefer Serena tools |
| `PreToolUse` (`mcp__serena__*`) | `serena-hooks auto-approve` | Auto-approves Serena tool calls |
| `SessionStart` | `serena-hooks activate` | Activates the project at session start |
| `Stop` | `serena-hooks cleanup` | Cleans up when the session ends |

Codex does not use Claude's hooks file. Register Serena in
Codex separately via `codex mcp add ...` above.

### Step 3 — Install TypeScript LSP

Serena's symbolic tools for `.ts`/`.tsx` files require the
TypeScript language server binary and the Claude Code plugin.

**Install the binary:**

```bash
npm install -g typescript-language-server typescript
which typescript-language-server   # must return a path
```

**Install the plugin** for Claude Code:

```
/plugin install typescript-lsp@claude-plugins-official
/reload-plugins
```

If the marketplace is not available, add it first:

```
/plugin marketplace add anthropics/claude-plugins-official
/plugin install typescript-lsp@claude-plugins-official
/reload-plugins
```

Verify: run `/plugin` → **Installed** tab → `typescript-lsp`
must be listed and active.

Codex uses Serena's `codex` MCP context and does not need
the Claude plugin install step.

### Step 4 — Configure the Project Language

Serena needs to know the project language to activate the
LSP. Check `.serena/project.yml`:

```bash
cat .serena/project.yml 2>/dev/null || echo "NOT FOUND"
```

If the file does not exist or `typescript` is not listed
under `languages:`, add it:

```yaml
languages:
  - typescript
```

### Step 5 — Run Project Onboarding

Start a **fresh conversation** after completing the steps
above (the MCP server must be active). Then call:

```
mcp__serena__onboarding
```

Serena will read the project structure and write memory
files under `.serena/memories/`. After onboarding
completes, start another fresh conversation — onboarding
fills context and the next session benefits from the
generated memories.

Review the generated memories and adjust any that are
inaccurate.

## Common Edge Cases

- **`serena start-mcp-server` not found**: The `uv tool
  install` step was skipped or failed. Re-run it.
- **MCP tools still missing after install**: Restart the
  client (Claude Code or Codex) to reload the MCP server
  list.
- **TypeScript LSP errors tab shows "Executable not found"**:
  `typescript-language-server` is not on `$PATH`. Re-run
  `npm install -g typescript-language-server typescript`.
- **Hooks not firing**: The `serena-hooks` binary must be on
  `$PATH` — it is installed alongside Serena via `uv tool
  install`. Verify with `which serena-hooks`.
- **Onboarding fills context**: Always start a fresh
  conversation before and after running onboarding.

## Related Skills

- `.claude/skills/managing-design-system/` — requires Serena
  and the TypeScript LSP to function
- `.claude/skills/building-skills/` — for creating new skills
