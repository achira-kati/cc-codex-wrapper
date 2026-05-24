import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Scopes:
    user: Path
    project: Path | None


def user_home() -> Path:
    """Return the current user's home directory across Unix and Windows shells."""
    home = os.environ.get("HOME")
    if home:
        return Path(home)

    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        return Path(userprofile)

    home_drive = os.environ.get("HOMEDRIVE")
    home_path = os.environ.get("HOMEPATH")
    if home_drive and home_path:
        return Path(home_drive + home_path)

    return Path.home()


def discover(cwd: Path | None = None) -> Scopes:
    """Return user and (optional) project scope directories.

    User scope is always ~/.ccx/. Project scope is the nearest .ccx/ directory
    walking up from `cwd` (defaults to CWD), or None if none found before the
    filesystem root.
    """
    home = user_home()
    user = home / ".ccx"
    cwd = cwd or Path.cwd()
    project: Path | None = None
    for parent in [cwd] + list(cwd.parents):
        if _same_path(parent, home):
            break
        candidate = parent / ".ccx"
        if candidate.is_dir():
            project = candidate
            break
    return Scopes(user=user, project=project)


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left == right
