import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scopes:
    user: Path
    project: Path | None


def discover(cwd: Path | None = None) -> Scopes:
    """Return user and (optional) project scope directories.

    User scope is always ~/.ccx/. Project scope is the nearest .ccx/ directory
    walking up from `cwd` (defaults to CWD), or None if none found before the
    filesystem root.
    """
    home = Path(os.environ["HOME"])
    user = home / ".ccx"
    cwd = cwd or Path.cwd()
    project: Path | None = None
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".ccx"
        if candidate.is_dir():
            project = candidate
            break
    return Scopes(user=user, project=project)
