from pathlib import Path

STARTER_AGENTS_MD = "# Project conventions\n\nAdd instructions here that both Claude Code and Codex should see.\n"
STARTER_MCP_YAML = "servers: {}\n"
STARTER_HOOKS_YAML = "hooks: {}\n"
STARTER_GITIGNORE = ".state/\nbackups/\n"


def run(scope_dir: Path) -> int:
    """Create ~/.ccx/ with starter files. Never overwrites existing content."""
    scope_dir.mkdir(parents=True, exist_ok=True)

    _write_if_missing(scope_dir / "AGENTS.md", STARTER_AGENTS_MD)
    _write_if_missing(scope_dir / "mcp.yaml", STARTER_MCP_YAML)
    _write_if_missing(scope_dir / "hooks.yaml", STARTER_HOOKS_YAML)
    _write_if_missing(scope_dir / ".gitignore", STARTER_GITIGNORE)

    for subdir in ("skills", "claude", "codex"):
        (scope_dir / subdir).mkdir(exist_ok=True)

    print(f"Initialized canonical scope at {scope_dir}")
    return 0


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content)
