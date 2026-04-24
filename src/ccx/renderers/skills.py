from pathlib import Path

from ccx.loader import Canonical
from ccx.renderers.memory import PlannedWrite


def render_skills(
    *,
    user: Canonical | None,
    project: Canonical | None,
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    writes: list[PlannedWrite] = []

    if user is not None and user.skills_dir is not None:
        writes.append(PlannedWrite(
            path=home / ".claude" / "skills", kind="symlink", symlink_to=user.skills_dir
        ))
        writes.append(PlannedWrite(
            path=home / ".agents" / "skills", kind="symlink", symlink_to=user.skills_dir
        ))

    if project is not None and project_root is not None and project.skills_dir is not None:
        writes.append(PlannedWrite(
            path=project_root / ".claude" / "skills", kind="symlink", symlink_to=project.skills_dir
        ))
        writes.append(PlannedWrite(
            path=project_root / ".agents" / "skills", kind="symlink", symlink_to=project.skills_dir
        ))

    return writes
