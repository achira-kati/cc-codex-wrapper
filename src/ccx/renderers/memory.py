from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ccx.loader import Canonical


@dataclass(frozen=True)
class PlannedWrite:
    """A target file the renderer intends to produce."""
    path: Path
    kind: Literal["file", "symlink"]
    content: str = ""
    symlink_to: Path | None = None
    mode: Literal["owned", "merge"] = "owned"


def render_memory(
    *,
    user: Canonical | None,
    project: Canonical | None,
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    writes: list[PlannedWrite] = []

    if user is not None:
        # CC: ~/.claude/CLAUDE.md is an include stub.
        agents_path = home / ".ccx" / "AGENTS.md"
        claude_extras = _read_if_exists(
            (user.claude_passthrough / "CLAUDE.md") if user.claude_passthrough else None
        )
        stub = f"@{agents_path.as_posix()}\n"
        if claude_extras:
            stub += "\n" + claude_extras
        writes.append(PlannedWrite(path=home / ".claude" / "CLAUDE.md", kind="file", content=stub))

        # Codex: ~/.codex/AGENTS.md is an owned copy with codex-passthrough extras appended.
        codex_extras = _read_if_exists(
            (user.codex_passthrough / "AGENTS.md") if user.codex_passthrough else None
        )
        codex_content = user.agents_md
        if codex_extras:
            codex_content = codex_content.rstrip() + "\n\n" + codex_extras
        writes.append(
            PlannedWrite(path=home / ".codex" / "AGENTS.md", kind="file", content=codex_content)
        )

    if project is not None and project_root is not None:
        # CC project: ./CLAUDE.md is @AGENTS.md stub.
        project_agents_path = project_root / ".ccx" / "AGENTS.md"
        has_project_agents = project_agents_path.is_file()
        project_claude_extras = _read_if_exists(
            (project.claude_passthrough / "CLAUDE.md") if project.claude_passthrough else None
        )
        if has_project_agents or project_claude_extras:
            stub = "@AGENTS.md\n" if has_project_agents else ""
            if project_claude_extras:
                stub += ("\n" if stub else "") + project_claude_extras
            writes.append(
                PlannedWrite(path=project_root / "CLAUDE.md", kind="file", content=stub)
            )

        # Codex project: ./AGENTS.md symlinks to .ccx/AGENTS.md
        if has_project_agents:
            writes.append(
                PlannedWrite(
                    path=project_root / "AGENTS.md",
                    kind="symlink",
                    symlink_to=project_agents_path,
                )
            )

    return writes


def _read_if_exists(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text()
