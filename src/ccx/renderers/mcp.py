import json
from pathlib import Path
from typing import Any

import tomli_w

from ccx.renderers.memory import PlannedWrite


def render_mcp(
    *,
    user_servers: dict[str, dict[str, Any]],
    project_servers: dict[str, dict[str, Any]],
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    writes: list[PlannedWrite] = []

    if user_servers:
        cc_content = json.dumps({"mcpServers": _to_cc(user_servers)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=home / ".claude.json", kind="file", content=cc_content))

        codex_content = tomli_w.dumps({"mcp_servers": _to_codex(user_servers)})
        writes.append(PlannedWrite(path=home / ".codex" / "config.toml", kind="file", content=codex_content))

    if project_servers and project_root is not None:
        # Project overrides user by server name.
        merged = {**user_servers, **project_servers}
        cc_content = json.dumps({"mcpServers": _to_cc(merged)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=project_root / ".mcp.json", kind="file", content=cc_content))

        codex_content = tomli_w.dumps({"mcp_servers": _to_codex(merged)})
        writes.append(PlannedWrite(path=project_root / ".codex" / "config.toml", kind="file", content=codex_content))

    return writes


def _to_cc(servers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Keep only fields CC understands; drop Codex-only ones."""
    cc_fields = {"command", "args", "env", "url", "headers"}
    out: dict[str, dict[str, Any]] = {}
    for name, spec in servers.items():
        kept = {k: v for k, v in spec.items() if k in cc_fields}
        out[name] = kept
    return out


def _to_codex(servers: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Codex accepts all canonical fields verbatim."""
    return {name: dict(spec) for name, spec in servers.items()}
