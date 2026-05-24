import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ccx.atomic import atomic_write, replace_with_symlink
from ccx.backup import backup_file, new_backup_dir
from ccx.formats import merge_content
from ccx.loader import Canonical, LoaderError, load_canonical
from ccx.manifest import Manifest
from ccx.renderers.hooks import render_hooks
from ccx.renderers.mcp import render_mcp
from ccx.renderers.memory import PlannedWrite, render_memory
from ccx.renderers.passthrough import render_passthrough
from ccx.renderers.skills import render_skills
from ccx.scope import Scopes

TargetFilter = Literal["all", "claude", "codex"]
TargetName = Literal["claude", "codex"]


@dataclass
class SyncOptions:
    dry_run: bool = False
    force: bool = False
    quiet: bool = False
    target: TargetFilter = "all"


def run(scopes: Scopes, home: Path, project_root: Path | None, opts: SyncOptions) -> int:
    try:
        user = load_canonical(scopes.user)
        project = load_canonical(scopes.project) if scopes.project else None
    except LoaderError as e:
        print(f"canonical validation failed: {e}", file=sys.stderr)
        return 2

    all_writes = _plan(user=user, project=project, home=home, project_root=project_root)
    writes = _filter_writes_for_target(
        all_writes, target=opts.target, home=home, project_root=project_root
    )
    manifest_path = scopes.user / ".state" / "manifest.json"
    manifest = Manifest.load(manifest_path)

    desired_paths = {w.path for w in writes}
    orphans = _orphans_for_target(
        manifest, desired_paths, target=opts.target, home=home, project_root=project_root
    )

    # Drift detection for non-force runs.
    if not opts.force:
        for w in writes:
            if w.mode == "merge":
                continue  # merge-mode: external edits are expected
            if w.path.exists() and str(w.path) in manifest.entries and not w.path.is_symlink():
                recorded = manifest.entries[str(w.path)]
                if recorded in ("symlink", "merge"):
                    continue
                if Manifest.hash_file(w.path) != recorded:
                    print(
                        f"manual edit detected at {w.path}. "
                        f"Re-run with --force to overwrite, or move the change into canonical.",
                        file=sys.stderr,
                    )
                    return 3

    if opts.dry_run:
        _print_plan(writes, orphans)
        return 0

    # Backup phase: any existing target that isn't ccx-managed gets moved aside.
    backup_dir = None
    for w in writes:
        if w.mode == "merge":
            continue
        if w.path.exists() and not w.path.is_symlink():
            if str(w.path) not in manifest.entries:
                if backup_dir is None:
                    backup_dir = new_backup_dir(scopes.user / "backups")
                tree_root = home if _is_under(w.path, home) else (project_root or home)
                backup_file(w.path, backup_dir, tree_root)
                if not opts.quiet:
                    print(f"backed up {w.path} -> {backup_dir}")

    # Write phase.
    new_manifest = Manifest(
        entries=_preserve_unselected_entries(
            manifest, target=opts.target, home=home, project_root=project_root
        )
    )
    for w in writes:
        if w.kind == "symlink":
            assert w.symlink_to is not None
            replace_with_symlink(w.path, w.symlink_to)
            # Symlinks aren't hash-tracked; record with a sentinel.
            new_manifest.record(w.path, "symlink")
        elif w.mode == "merge":
            existing = _read_existing_or_empty(w.path)
            merged = merge_content(existing, w.content, w.path) if existing else w.content
            atomic_write(w.path, merged)
            new_manifest.record(w.path, "merge")
        else:
            atomic_write(w.path, w.content)
            new_manifest.record(w.path, Manifest.hash_file(w.path))

    # Orphan cleanup: preserve any orphan whose user has edited since ccx wrote it.
    for orphan in orphans:
        if not (orphan.exists() or orphan.is_symlink()):
            continue
        recorded = manifest.entries.get(str(orphan))
        if recorded == "merge":
            # Was merge-mode; we don't own it. Skip entirely.
            continue
        if orphan.is_symlink() or recorded == "symlink":
            orphan.unlink()
            if not opts.quiet:
                print(f"removed orphan symlink {orphan}")
            continue
        current = Manifest.hash_file(orphan)
        if recorded is not None and current != recorded:
            if not opts.force:
                print(
                    f"warning: orphan {orphan} was edited since ccx wrote it; "
                    f"not removing. Re-run with --force to delete anyway.",
                    file=sys.stderr,
                )
                continue
        orphan.unlink()
        if not opts.quiet:
            print(f"removed orphan {orphan}")

    new_manifest.save(manifest_path)
    return 0


def _plan(
    *,
    user: Canonical,
    project: Canonical | None,
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    writes: list[PlannedWrite] = []
    writes += render_memory(user=user, project=project, home=home, project_root=project_root)
    writes += render_skills(user=user, project=project, home=home, project_root=project_root)
    writes += render_mcp(
        user_servers=user.mcp_servers,
        project_servers=project.mcp_servers if project else {},
        home=home,
        project_root=project_root,
    )
    writes += render_hooks(
        user_hooks=user.hooks,
        project_hooks=project.hooks if project else {},
        home=home,
        project_root=project_root,
    )
    # Passthrough runs LAST so it can merge with earlier-planned writes.
    writes = render_passthrough(
        scope_dir=user.root, target_root=home, generated_writes=writes, subdir="claude",
    )
    writes = render_passthrough(
        scope_dir=user.root, target_root=home, generated_writes=writes, subdir="codex",
    )
    if project is not None and project_root is not None:
        writes = render_passthrough(
            scope_dir=project.root, target_root=project_root, generated_writes=writes, subdir="claude",
        )
        writes = render_passthrough(
            scope_dir=project.root, target_root=project_root, generated_writes=writes, subdir="codex",
        )
    return _coalesce_by_path(writes)


def _coalesce_by_path(writes: list[PlannedWrite]) -> list[PlannedWrite]:
    """Merge writes that target the same path. Preserves order of first appearance.

    Symlinks are kept as-is (can't merge symlinks). File writes with the same path
    are deep-merged via format-aware merge.
    """
    result: list[PlannedWrite] = []
    by_path: dict[Path, int] = {}  # path -> index in result

    for w in writes:
        if w.path in by_path:
            idx = by_path[w.path]
            existing = result[idx]
            if existing.kind == "symlink" or w.kind == "symlink":
                # Can't meaningfully merge a symlink with anything; last write wins.
                result[idx] = w
            else:
                merged_content = merge_content(existing.content, w.content, w.path)
                # Preserve merge mode if either write is merge-mode.
                coalesced_mode = "merge" if (existing.mode == "merge" or w.mode == "merge") else "owned"
                result[idx] = PlannedWrite(
                    path=w.path, kind="file", content=merged_content, mode=coalesced_mode
                )
        else:
            by_path[w.path] = len(result)
            result.append(w)

    return result


def _filter_writes_for_target(
    writes: list[PlannedWrite],
    *,
    target: TargetFilter,
    home: Path,
    project_root: Path | None,
) -> list[PlannedWrite]:
    if target == "all":
        return writes
    selected = {target}
    return [
        w
        for w in writes
        if _path_targets(w.path, home=home, project_root=project_root) & selected
    ]


def _orphans_for_target(
    manifest: Manifest,
    desired_paths: set[Path],
    *,
    target: TargetFilter,
    home: Path,
    project_root: Path | None,
) -> set[Path]:
    desired_str = {str(p) for p in desired_paths}
    return {
        Path(path)
        for path in manifest.entries
        if path not in desired_str
        and _path_matches_target(
            Path(path), target=target, home=home, project_root=project_root
        )
    }


def _preserve_unselected_entries(
    manifest: Manifest,
    *,
    target: TargetFilter,
    home: Path,
    project_root: Path | None,
) -> dict[str, str]:
    return {
        path: recorded
        for path, recorded in manifest.entries.items()
        if not _path_matches_target(
            Path(path), target=target, home=home, project_root=project_root
        )
    }


def _path_matches_target(
    path: Path,
    *,
    target: TargetFilter,
    home: Path,
    project_root: Path | None,
) -> bool:
    targets = _path_targets(path, home=home, project_root=project_root)
    if target == "all":
        return bool(targets)
    return target in targets


def _path_targets(path: Path, *, home: Path, project_root: Path | None) -> set[TargetName]:
    targets: set[TargetName] = set()

    if path == home / ".claude.json" or _is_under_path(path, home / ".claude"):
        targets.add("claude")
    if _is_under_path(path, home / ".codex") or _is_under_path(path, home / ".agents"):
        targets.add("codex")

    if project_root is not None:
        if (
            path == project_root / "CLAUDE.md"
            or path == project_root / ".mcp.json"
            or _is_under_path(path, project_root / ".claude")
        ):
            targets.add("claude")
        if path == project_root / "AGENTS.md":
            targets.update({"claude", "codex"})
        if _is_under_path(path, project_root / ".codex") or _is_under_path(
            path, project_root / ".agents"
        ):
            targets.add("codex")

    return targets


def _is_under_path(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _print_plan(writes: list[PlannedWrite], orphans: set[Path]) -> None:
    print("would write:")
    for w in writes:
        if w.kind == "symlink":
            print(f"  symlink {w.path} -> {w.symlink_to}")
        else:
            print(f"  file    {w.path} ({len(w.content)} bytes)")
    if orphans:
        print("would remove (orphans):")
        for p in sorted(orphans, key=str):
            print(f"  {p}")


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _read_existing_or_empty(path: Path) -> str:
    if not path.exists() or path.is_symlink():
        return ""
    try:
        return path.read_text()
    except (OSError, UnicodeDecodeError):
        return ""
