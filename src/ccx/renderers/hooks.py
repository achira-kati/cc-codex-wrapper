import json
from pathlib import Path
from typing import Any

import tomli_w

from ccx.merge import deep_merge
from ccx.renderers.memory import PlannedWrite


def render_hooks(
    *,
    user_hooks: dict[str, list[dict[str, Any]]],
    project_hooks: dict[str, list[dict[str, Any]]],
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    writes: list[PlannedWrite] = []

    if user_hooks:
        cc_content = json.dumps({"hooks": _cc_shape(user_hooks)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=home / ".claude" / "settings.json", kind="file", content=cc_content))

        codex_content = json.dumps({"hooks": _codex_shape(user_hooks)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=home / ".codex" / "hooks.json", kind="file", content=codex_content))

        codex_cfg = tomli_w.dumps({"features": {"codex_hooks": True}})
        writes.append(PlannedWrite(path=home / ".codex" / "config.toml", kind="file", content=codex_cfg))

    if project_hooks and project_root is not None:
        merged = deep_merge(user_hooks, project_hooks)
        cc_content = json.dumps({"hooks": _cc_shape(merged)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=project_root / ".claude" / "settings.json", kind="file", content=cc_content))

        codex_content = json.dumps({"hooks": _codex_shape(merged)}, indent=2, sort_keys=True)
        writes.append(PlannedWrite(path=project_root / ".codex" / "hooks.json", kind="file", content=codex_content))

    return writes


def _cc_shape(hooks: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Claude Code requires 'type': 'command' on each command hook."""
    return _command_hook_shape(hooks)


def _codex_shape(hooks: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Codex requires 'type': 'command' on each handler."""
    return _command_hook_shape(hooks)


def _command_hook_shape(hooks: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for event, matchers in hooks.items():
        new_matchers: list[dict[str, Any]] = []
        for matcher in matchers:
            new_matcher = dict(matcher)
            new_handlers = []
            for handler in matcher.get("hooks", []):
                new_handler = dict(handler)
                new_handler.setdefault("type", "command")
                new_handlers.append(new_handler)
            new_matcher["hooks"] = new_handlers
            new_matchers.append(new_matcher)
        out[event] = new_matchers
    return out
