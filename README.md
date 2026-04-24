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
