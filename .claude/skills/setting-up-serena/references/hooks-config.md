# Serena Claude Code Hooks

Full hooks block to merge into `.claude/settings.json`.
If the file already has a `"hooks"` key, merge each
hook type rather than replacing the entire object.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "serena-hooks remind --client=claude-code"
          }
        ]
      },
      {
        "matcher": "mcp__serena__*",
        "hooks": [
          {
            "type": "command",
            "command": "serena-hooks auto-approve --client=claude-code"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "serena-hooks activate --client=claude-code"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "serena-hooks cleanup --client=claude-code"
          }
        ]
      }
    ]
  }
}
```

## What each hook does

| Hook | Effect |
|------|--------|
| `remind` | Fires on every tool call; reminds Claude to prefer Serena over grep/glob when a symbolic tool would be better |
| `auto-approve` | Auto-approves all `mcp__serena__*` tool calls, reducing confirmation prompts |
| `activate` | Activates the current working directory as the Serena project at session start |
| `cleanup` | Releases the project lock and cleans up temp state when the session ends |

## Scope

To share hooks with all collaborators on the project, write
to `.claude/settings.json` (project scope). To keep them
personal, write to `~/.claude/settings.json` (user scope).
