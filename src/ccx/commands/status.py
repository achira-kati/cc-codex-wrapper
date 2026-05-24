from pathlib import Path

from ccx.commands.sync import (
    TargetFilter,
    _filter_writes_for_target,
    _orphans_for_target,
    _plan,
)
from ccx.formats import merge_content
from ccx.loader import load_canonical
from ccx.manifest import Manifest
from ccx.scope import Scopes


def run(
    scopes: Scopes,
    home: Path,
    project_root: Path | None,
    *,
    target: TargetFilter = "all",
    managed_only: bool = False,
) -> tuple[int, str]:
    """Return (exit_code, human_readable_summary).

    exit_code is 0 if in sync, nonzero if drift detected.
    managed_only ignores desired targets that are not already in the manifest,
    which lets clean operate after a target-specific sync.
    """
    user = load_canonical(scopes.user)
    project = load_canonical(scopes.project) if scopes.project else None
    writes = _filter_writes_for_target(
        _plan(user=user, project=project, home=home, project_root=project_root),
        target=target,
        home=home,
        project_root=project_root,
    )

    manifest = Manifest.load(scopes.user / ".state" / "manifest.json")
    if managed_only:
        writes = [w for w in writes if str(w.path) in manifest.entries]

    drifted: list[Path] = []
    for w in writes:
        if w.kind == "symlink":
            if not w.path.is_symlink() or w.symlink_to is None:
                drifted.append(w.path)
                continue
            if w.path.resolve() != w.symlink_to.resolve():
                drifted.append(w.path)
            continue
        if not w.path.exists():
            drifted.append(w.path)
            continue
        recorded = manifest.entries.get(str(w.path))
        if recorded is None:
            drifted.append(w.path)
            continue
        if w.mode == "merge":
            if recorded != "merge":
                drifted.append(w.path)
                continue
            existing = _read_existing_or_empty(w.path)
            if not existing or merge_content(existing, w.content, w.path) != existing:
                drifted.append(w.path)
            continue
        if recorded in ("merge", "symlink"):
            drifted.append(w.path)
            continue
        if Manifest.hash_file(w.path) != recorded:
            drifted.append(w.path)
            continue
        # Also drift if canonical has changed since last write.
        if w.path.read_text() != w.content:
            drifted.append(w.path)

    orphans = _orphans_for_target(
        manifest,
        {w.path for w in writes},
        target=target,
        home=home,
        project_root=project_root,
    )

    if not drifted and not orphans:
        return 0, "clean — all targets in sync with canonical\n"

    lines = ["drift detected:"]
    for p in drifted:
        lines.append(f"  stale: {p}")
    for p in sorted(orphans, key=str):
        lines.append(f"  orphan: {p}")
    return 1, "\n".join(lines) + "\n"


def _read_existing_or_empty(path: Path) -> str:
    if not path.exists() or path.is_symlink():
        return ""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError):
        return ""
