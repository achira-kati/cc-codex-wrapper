import sys
from dataclasses import dataclass
from pathlib import Path

from ccx.atomic import atomic_write, replace_with_symlink
from ccx.backup import backup_file, new_backup_dir
from ccx.loader import Canonical, LoaderError, load_canonical
from ccx.manifest import Manifest
from ccx.renderers.hooks import render_hooks
from ccx.renderers.mcp import render_mcp
from ccx.renderers.memory import PlannedWrite, render_memory
from ccx.renderers.passthrough import render_passthrough
from ccx.renderers.skills import render_skills
from ccx.scope import Scopes


@dataclass
class SyncOptions:
    dry_run: bool = False
    force: bool = False
    quiet: bool = False


def run(scopes: Scopes, home: Path, project_root: Path | None, opts: SyncOptions) -> int:
    try:
        user = load_canonical(scopes.user)
        project = load_canonical(scopes.project) if scopes.project else None
    except LoaderError as e:
        print(f"canonical validation failed: {e}", file=sys.stderr)
        return 2

    writes = _plan(user=user, project=project, home=home, project_root=project_root)
    manifest_path = scopes.user / ".state" / "manifest.json"
    manifest = Manifest.load(manifest_path)

    desired_paths = {w.path for w in writes}
    orphans = manifest.orphans(desired_paths)

    # Drift detection for non-force runs.
    if not opts.force:
        for w in writes:
            if w.path.exists() and str(w.path) in manifest.entries and not w.path.is_symlink():
                if Manifest.hash_file(w.path) != manifest.entries[str(w.path)]:
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
        if w.path.exists() and not w.path.is_symlink():
            if str(w.path) not in manifest.entries:
                if backup_dir is None:
                    backup_dir = new_backup_dir(scopes.user / "backups")
                tree_root = home if _is_under(w.path, home) else (project_root or home)
                backup_file(w.path, backup_dir, tree_root)
                if not opts.quiet:
                    print(f"backed up {w.path} -> {backup_dir}")

    # Write phase.
    new_manifest = Manifest()
    for w in writes:
        if w.kind == "symlink":
            assert w.symlink_to is not None
            replace_with_symlink(w.path, w.symlink_to)
            # Symlinks aren't hash-tracked; record with a sentinel.
            new_manifest.record(w.path, "symlink")
        else:
            atomic_write(w.path, w.content)
            new_manifest.record(w.path, Manifest.hash_file(w.path))

    # Orphan cleanup.
    for orphan in orphans:
        if orphan.exists() or orphan.is_symlink():
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
    return writes


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
