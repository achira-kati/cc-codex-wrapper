from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class LoaderError(Exception):
    """Raised on canonical schema validation failure."""


@dataclass
class Canonical:
    root: Path
    agents_md: str = ""
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)
    hooks: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    skills_dir: Path | None = None
    claude_passthrough: Path | None = None
    codex_passthrough: Path | None = None


def load_canonical(scope_dir: Path) -> Canonical:
    """Load a canonical scope (~/.ccx/ or .ccx/). Missing files are treated as empty."""
    c = Canonical(root=scope_dir)

    agents_md = scope_dir / "AGENTS.md"
    if agents_md.is_file():
        c.agents_md = agents_md.read_text()

    mcp_path = scope_dir / "mcp.yaml"
    if mcp_path.is_file():
        c.mcp_servers = _load_and_validate_mcp(mcp_path)

    hooks_path = scope_dir / "hooks.yaml"
    if hooks_path.is_file():
        c.hooks = _load_and_validate_hooks(hooks_path)

    skills = scope_dir / "skills"
    if skills.is_dir():
        c.skills_dir = skills

    claude = scope_dir / "claude"
    if claude.is_dir():
        c.claude_passthrough = claude

    codex = scope_dir / "codex"
    if codex.is_dir():
        c.codex_passthrough = codex

    return c


def _load_and_validate_mcp(path: Path) -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(path.read_text()) or {}
    servers = data.get("servers", {})
    if not isinstance(servers, dict):
        raise LoaderError(f"{path}: 'servers' must be a mapping")
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            raise LoaderError(f"{path}: servers.{name} must be a mapping")
        if "command" not in spec and "url" not in spec:
            raise LoaderError(
                f"{path}: servers.{name}: must have either 'command' or 'url'"
            )
    return servers


def _load_and_validate_hooks(path: Path) -> dict[str, list[dict[str, Any]]]:
    data = yaml.safe_load(path.read_text()) or {}
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        raise LoaderError(f"{path}: 'hooks' must be a mapping")
    allowed_events = {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "UserPromptSubmit",
        "Stop",
        "PermissionRequest",
    }
    for event, matchers in hooks.items():
        if event not in allowed_events:
            raise LoaderError(
                f"{path}: hooks.{event}: not a shared event. "
                f"Use ~/.ccx/claude/settings.json or ~/.ccx/codex/hooks.json for tool-only events."
            )
        if not isinstance(matchers, list):
            raise LoaderError(f"{path}: hooks.{event} must be a list")
    return hooks
