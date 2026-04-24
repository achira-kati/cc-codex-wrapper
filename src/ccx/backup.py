import shutil
from datetime import datetime, timezone
from pathlib import Path


def new_backup_dir(root: Path) -> Path:
    """Create a fresh timestamped directory under `root` and return its path."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    d = root / timestamp
    d.mkdir(parents=True, exist_ok=False)
    return d


def backup_file(source: Path, backup_dir: Path, tree_root: Path) -> Path:
    """Move `source` into `backup_dir`, preserving its path relative to `tree_root`.

    Returns the new path. `source` must exist; `backup_dir` must be writable.
    """
    rel = source.resolve().relative_to(tree_root.resolve())
    dest = backup_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))
    return dest
