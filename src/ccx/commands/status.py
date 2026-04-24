from pathlib import Path

from ccx.commands.sync import _plan
from ccx.loader import load_canonical
from ccx.manifest import Manifest
from ccx.scope import Scopes


def run(scopes: Scopes, home: Path, project_root: Path | None) -> tuple[int, str]:
    """Return (exit_code, human_readable_summary).

    exit_code is 0 if in sync, nonzero if drift detected.
    """
    user = load_canonical(scopes.user)
    project = load_canonical(scopes.project) if scopes.project else None
    writes = _plan(user=user, project=project, home=home, project_root=project_root)

    manifest = Manifest.load(scopes.user / ".state" / "manifest.json")

    drifted: list[Path] = []
    for w in writes:
        if w.kind == "symlink":
            continue
        if not w.path.exists():
            drifted.append(w.path)
            continue
        recorded = manifest.entries.get(str(w.path))
        if recorded is None:
            drifted.append(w.path)
            continue
        if Manifest.hash_file(w.path) != recorded:
            drifted.append(w.path)
            continue
        # Also drift if canonical has changed since last write.
        if w.path.read_text() != w.content:
            drifted.append(w.path)

    orphans = manifest.orphans({w.path for w in writes})

    if not drifted and not orphans:
        return 0, "clean — all targets in sync with canonical\n"

    lines = ["drift detected:"]
    for p in drifted:
        lines.append(f"  stale: {p}")
    for p in sorted(orphans, key=str):
        lines.append(f"  orphan: {p}")
    return 1, "\n".join(lines) + "\n"
