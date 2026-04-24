import os
from pathlib import Path


def atomic_write(target: Path, content: str) -> None:
    """Write content to target atomically via temp file + rename.

    Parent directories are created if missing. On success, no .tmp file remains.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".ccx.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, target)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def replace_with_symlink(target: Path, source: Path) -> None:
    """Make `target` a symlink pointing at `source`, replacing any existing link.

    Caller is responsible for backing up a real (non-symlink) target beforehand.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        target.unlink()
    target.symlink_to(source)
