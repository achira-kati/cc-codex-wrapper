# ccx

One config source for Claude Code and Codex.

Write your MCP servers, memory, skills, and shared hooks once in `~/.ccx/`.
`ccx sync` renders them into `~/.claude/` and `~/.codex/` so both tools see
the same state. `ccx claude` and `ccx codex` sync automatically and then
launch the native CLI.

## Install

```bash
uv tool install ccx
```

## Quick start

```bash
ccx init                         # scaffold ~/.ccx/
$EDITOR ~/.ccx/AGENTS.md         # shared memory (both tools)
$EDITOR ~/.ccx/mcp.yaml          # MCP servers
$EDITOR ~/.ccx/hooks.yaml        # shared hook events
ccx sync                         # render to ~/.claude/ and ~/.codex/
ccx claude                       # or: ccx codex
```

## Example: one source, two outputs

Here's what a typical `~/.ccx/` looks like and what `ccx sync` produces from it.

### Shared memory — `~/.ccx/AGENTS.md`

```markdown
# Working agreements

- Run tests before committing.
- Prefer pnpm over npm.
- Ask for approval before adding production dependencies.
```

Becomes:

- **`~/.claude/CLAUDE.md`** — a tiny stub that CC's `@path` import expands at session start:
  ```markdown
  @/Users/you/.ccx/AGENTS.md
  ```
- **`~/.codex/AGENTS.md`** — owned copy of the same content (Codex has no include mechanism, so ccx writes a copy and backs up anything that was there before).

### Skills — `~/.ccx/skills/<name>/SKILL.md`

```
~/.ccx/skills/
└── commit-message/
    └── SKILL.md
```

With `SKILL.md`:
```markdown
---
name: commit-message
description: Write a commit message following the repo's conventions.
---

Look at recent commits, match the prevailing style...
```

Becomes two symlinks pointing at the same canonical dir — no translation:

- `~/.claude/skills` → `~/.ccx/skills`
- `~/.agents/skills` → `~/.ccx/skills`

### MCP servers — `~/.ccx/mcp.yaml`

```yaml
servers:
  context7:
    command: npx
    args: ["-y", "@upstash/context7-mcp"]
  figma:
    url: "https://mcp.figma.com/mcp"
    bearer_token_env_var: FIGMA_OAUTH_TOKEN
```

Becomes:

- **`~/.claude.json`** (CC user-level MCP):
  ```json
  {
    "mcpServers": {
      "context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]},
      "figma": {"url": "https://mcp.figma.com/mcp"}
    }
  }
  ```
- **`~/.codex/config.toml`**:
  ```toml
  [mcp_servers.context7]
  command = "npx"
  args = ["-y", "@upstash/context7-mcp"]

  [mcp_servers.figma]
  url = "https://mcp.figma.com/mcp"
  bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
  ```

### Hooks — `~/.ccx/hooks.yaml` (6 shared events)

```yaml
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - command: "$HOME/.ccx/hooks/pre_bash.py"
          timeout: 30
  SessionStart:
    - hooks:
        - command: "echo 'session starting'"
```

Becomes:

- **`~/.claude/settings.json`** — CC reads the `hooks` key verbatim:
  ```json
  {
    "hooks": {
      "PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "...", "timeout": 30}]}],
      "SessionStart": [{"hooks": [{"command": "echo 'session starting'"}]}]
    }
  }
  ```
- **`~/.codex/hooks.json`** — same structure, with `"type": "command"` injected (Codex requires it):
  ```json
  {
    "hooks": {
      "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "...", "timeout": 30}]}],
      "SessionStart": [{"hooks": [{"type": "command", "command": "echo 'session starting'"}]}]
    }
  }
  ```
- **`~/.codex/config.toml`** also gets `[features] codex_hooks = true` because Codex hooks are opt-in.

### Tool-native passthrough

For things that don't translate (CC permissions, Codex sandbox rules), drop the native file under `~/.ccx/claude/` or `~/.ccx/codex/` and ccx copies or deep-merges it through.

**`~/.ccx/claude/settings.json`** — CC permissions (CC-only; merged into `~/.claude/settings.json` alongside the hooks block ccx generated):
```json
{
  "permissions": {
    "allow": ["Bash(git *)", "Bash(pnpm *)"],
    "deny": ["Bash(rm -rf *)"]
  }
}
```

**`~/.ccx/codex/rules/default.rules`** — Codex Starlark rules (copied as-is to `~/.codex/rules/default.rules`):
```python
prefix_rule(
    pattern = ["git", "push"],
    decision = "prompt",
    justification = "Review before pushing.",
)
```

**`~/.ccx/codex/config.toml`** — Codex sandbox (merged into `~/.codex/config.toml` alongside the `mcp_servers` and `features` sections):
```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"
```

---

## Project-level setup

Project-scope looks identical to user-scope — just under `.ccx/` at the repo root instead of `~/.ccx/`. Commit `.ccx/` so your team shares the same config; everything else is generated and should be ignored.

### Layout to commit

```
my-project/
└── .ccx/
    ├── AGENTS.md            # project memory (team shares this)
    ├── mcp.yaml             # project-specific MCP servers
    ├── hooks.yaml           # project hooks
    ├── skills/
    │   └── run-migrations/
    │       └── SKILL.md
    ├── claude/
    │   └── settings.json    # project permissions, CC-only settings
    └── codex/
        └── rules/
            └── default.rules
```

### What ccx generates in the repo

After `ccx sync` (from anywhere inside the repo — ccx walks up to find `.ccx/`):

```
my-project/
├── CLAUDE.md            # generated: @AGENTS.md stub
├── AGENTS.md            # generated: symlink → .ccx/AGENTS.md
├── .mcp.json            # generated: CC project MCP servers
├── .claude/
│   ├── settings.json    # generated hooks block + your permissions (deep-merged)
│   └── skills/          # symlink → ../.ccx/skills
├── .codex/
│   ├── config.toml      # generated: [mcp_servers.*] + [features] + your sandbox config
│   ├── hooks.json       # generated
│   └── rules/           # copied from .ccx/codex/rules/
├── .agents/
│   └── skills/          # symlink → ../.ccx/skills
└── .ccx/                # your source (committed)
```

### Recommended `.gitignore` additions

Add these to your repo's `.gitignore` so teammates don't commit generated or machine-local files:

```gitignore
# ccx local state (per-dev, not shared)
.ccx/.state/
.ccx/backups/

# ccx-generated — regenerated from .ccx/ on every `ccx sync`
/CLAUDE.md
/AGENTS.md
/.mcp.json
/.claude/
/.codex/
/.agents/
```

The leading `/` anchors each rule to the repo root — important if you also have nested `CLAUDE.md`, `.claude/`, or similar paths that you *do* want to track (e.g. test fixtures).

If you want teammates to see CC/Codex's own `settings.local.json` per-dev files but not commit them, add:

```gitignore
.claude/settings.local.json
.codex/settings.local.json
```

### Merge rules: project + user

When you have both `~/.ccx/` and `./.ccx/`, they combine per concept:

| Concept | Rule |
|---|---|
| **MCP servers** | Project overrides user **by server name** in the project output. User's own outputs are unchanged. |
| **Hooks** | Project entries **append** under the same event in the project output. |
| **Memory** | No cross-scope merge — both tools already load user + project `AGENTS.md`/`CLAUDE.md` hierarchically. |
| **Skills** | User and project target symlinks each point at their own canonical dir. |
| **Passthrough** | Project `.ccx/claude/...` renders to `./.claude/...`; user's to `~/.claude/...`. The tools' settings hierarchy handles final layering. |

### First-time setup for a new project

```bash
cd my-project
mkdir -p .ccx/{skills,claude,codex/rules}

cat > .ccx/AGENTS.md <<'EOF'
# Project conventions
- Tests: `pnpm test`
- Type check: `pnpm typecheck`
- Never push to main directly.
EOF

cat > .ccx/mcp.yaml <<'EOF'
servers:
  project-db-mcp:
    command: ./scripts/mcp-server.sh
    env:
      DATABASE_URL: "$DATABASE_URL"
EOF

cat > .ccx/claude/settings.json <<'EOF'
{"permissions": {"allow": ["Bash(pnpm *)"], "deny": ["Bash(rm -rf *)"]}}
EOF

# See "Recommended .gitignore additions" above.
$EDITOR .gitignore

ccx sync
git add .ccx .gitignore
git commit -m "chore: ccx project config"
```

Teammates clone, run `ccx sync` once, and their `claude` / `codex` see the same project state.

---

## What's in scope

| Concept | Where to put it |
|---|---|
| Memory (shared) | `~/.ccx/AGENTS.md` |
| Memory (CC-only additions) | `~/.ccx/claude/CLAUDE.md` (appended after `@include`) |
| Memory (Codex-only additions) | `~/.ccx/codex/AGENTS.md` (appended in owned copy) |
| Skills | `~/.ccx/skills/<name>/SKILL.md` (same format for both tools) |
| MCP servers | `~/.ccx/mcp.yaml` |
| Hooks (6 shared events) | `~/.ccx/hooks.yaml` |
| CC permissions | `~/.ccx/claude/settings.json` |
| CC-only hook events (`PreCompact`, `SubagentStart`, etc.) | `~/.ccx/claude/settings.json` |
| Codex `prefix_rule()` | `~/.ccx/codex/rules/*.rules` |
| Codex `sandbox_mode`, `approval_policy` | `~/.ccx/codex/config.toml` |

## What's NOT in scope

**Auto memory is deliberately not synced.** Each tool writes its own auto
memory in a format chosen by that tool:

- Claude Code writes to `~/.claude/projects/<project>/memory/` (per-repo,
  structured `MEMORY.md` index + topic files).
- Codex writes to `~/.codex/memories/` (per-user, opaque generated state the
  docs explicitly say not to hand-edit).

The formats are incompatible, the scopes don't align (per-repo vs per-user),
and each agent has implicit expectations about the structure *it* produced.
ccx leaves both alone; each tool continues to manage its own auto memory.

**Also not translated:**
- **Permissions / sandbox** — CC's `allow`/`deny`/`ask` patterns and Codex's
  `sandbox_mode` + `prefix_rule()` don't map. Write each in its native format
  under `~/.ccx/claude/` or `~/.ccx/codex/`.
- **Subagents, slash commands, plugins** — formats differ enough that a
  shared schema would be lossy.

### Known limitation: `~/.claude.json` is owned wholesale (v1)

ccx currently writes `~/.claude.json` (CC's user-level MCP config file) in full,
including only the `mcpServers` key. But CC uses `~/.claude.json` for other
state too — projects history, UI preferences, tips dismissal, etc. Running
`ccx sync` backs up the pre-existing file but replaces it with only ccx's
managed content, effectively resetting those other states.

**Workaround until v1.1:** if you rely on CC storing state in `~/.claude.json`,
avoid using ccx for MCP servers at user scope for now, or add your servers
to `~/.claude/settings.json` directly via `~/.ccx/claude/settings.json`
passthrough (note: check whether your CC version reads MCP from settings.json
before relying on this).

**Planned fix (v1.1):** change the MCP renderer to deep-merge `mcpServers`
into existing `~/.claude.json` rather than owning the file wholesale.

## How it works

`ccx sync` is pure and idempotent. It:

1. Loads canonical from `~/.ccx/` and (if in a project) `.ccx/`.
2. Computes the desired contents of every target file.
3. Backs up any pre-existing target not already managed by ccx to
   `~/.ccx/backups/<timestamp>/`.
4. Writes atomically (via temp + rename).
5. Updates `~/.ccx/.state/manifest.json` so the next run can detect drift and
   clean up orphaned targets.

Memory and skills use includes / symlinks where possible; MCP, hooks, and
passthrough files are owned with backup.

## Commands

| Command | Purpose |
|---|---|
| `ccx init` | Scaffold `~/.ccx/` with starter files |
| `ccx sync` | Render canonical → targets |
| `ccx sync --dry-run` | Print plan without writing |
| `ccx sync --check` | Exit non-zero if drift exists (for pre-commit / CI) |
| `ccx sync --force` | Overwrite manual edits to managed files |
| `ccx status` | Show what's stale or orphaned |
| `ccx restore [--list]` | Restore from a backup snapshot |
| `ccx claude [args...]` | Sync then exec `claude` |
| `ccx codex [args...]` | Sync then exec `codex` |

Set `CCX_SKIP_SYNC=1` to skip the implicit sync on `ccx claude` / `ccx codex`.

## License

MIT.
