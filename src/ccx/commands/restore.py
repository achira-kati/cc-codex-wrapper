import shutil
import sys
from pathlib import Path


def run(scope_dir: Path, *, list_only: bool, home: Path) -> int:
    backups_root = scope_dir / "backups"
    if not backups_root.is_dir():
        print("no backups to restore", file=sys.stderr)
        return 1

    snapshots = sorted([d for d in backups_root.iterdir() if d.is_dir()])
    if not snapshots:
        print("no backup snapshots found", file=sys.stderr)
        return 1

    if list_only:
        for s in snapshots:
            print(s.name)
        return 0

    latest = snapshots[-1]
    print(f"restoring from {latest}")
    _restore_tree(latest, home)
    return 0


def _restore_tree(snapshot: Path, target_root: Path) -> None:
    for source in snapshot.rglob("*"):
        if source.is_file():
            rel = source.relative_to(snapshot)
            dest = target_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
