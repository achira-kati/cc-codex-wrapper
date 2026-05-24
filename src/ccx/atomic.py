import os
import subprocess
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
    """Make `target` a link pointing at `source`, replacing any existing link.

    Caller is responsible for backing up a real (non-symlink) target beforehand.
    On Windows without symlink privileges, falls back to a directory junction or
    file hardlink so sync can still run in a normal shell.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        target.unlink()
    try:
        target.symlink_to(source, target_is_directory=source.is_dir())
    except OSError as exc:
        if os.name != "nt" or getattr(exc, "winerror", None) != 1314:
            raise
        _replace_with_windows_link(target, source)


def _replace_with_windows_link(target: Path, source: Path) -> None:
    if source.is_dir():
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(target), str(source)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    target.hardlink_to(source)
