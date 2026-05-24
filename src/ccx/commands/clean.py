import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from ccx.atomic import atomic_write
from ccx.commands import status as cmd_status
from ccx.commands.sync import _path_matches_target, _plan
from ccx.loader import LoaderError, load_canonical
from ccx.manifest import Manifest
from ccx.scope import Scopes


def run(scopes: Scopes, home: Path, project_root: Path | None) -> int:
    """Remove generated targets only when status says they are in sync."""
    status_rc, summary = cmd_status.run(
        scopes, home=home, project_root=project_root, managed_only=True
    )
    print(summary, end="")
    if status_rc != 0:
        print("Refusing to clean because generated targets are not in sync.", file=sys.stderr)
        return status_rc

    try:
        user = load_canonical(scopes.user)
        project = load_canonical(scopes.project) if scopes.project else None
    except LoaderError as e:
        print(f"canonical validation failed: {e}", file=sys.stderr)
        return 2

    writes = _plan(user=user, project=project, home=home, project_root=project_root)
    writes_by_path = {w.path: w for w in writes}
    manifest_path = scopes.user / ".state" / "manifest.json"
    manifest = Manifest.load(manifest_path)
    remaining_entries = dict(manifest.entries)

    removed = 0
    for raw_path, recorded in list(manifest.entries.items()):
        path = Path(raw_path)
        if not _path_matches_target(
            path, target="all", home=home, project_root=project_root
        ):
            continue
        remaining_entries.pop(raw_path, None)
        if recorded == "merge":
            write = writes_by_path.get(path)
            if write is not None and _clean_merge_target(path, write.content):
                removed += 1
            continue
        if path.exists() or path.is_symlink():
            path.unlink()
            removed += 1

    _remove_empty_generated_dirs(home, project_root)
    Manifest(entries=remaining_entries).save(manifest_path)
    print(f"removed {removed} generated target(s)")
    return 0


def _clean_merge_target(path: Path, generated_content: str) -> bool:
    if not path.exists() or path.is_symlink():
        return False

    if path.suffix == ".json":
        existing = json.loads(path.read_text())
        generated = json.loads(generated_content)
        cleaned = _subtract_generated(existing, generated)
        if cleaned:
            atomic_write(path, json.dumps(cleaned, indent=2, sort_keys=True) + "\n")
        else:
            path.unlink()
        return True

    if path.suffix == ".toml":
        existing = tomllib.loads(path.read_text())
        generated = tomllib.loads(generated_content)
        cleaned = _subtract_generated(existing, generated)
        if cleaned:
            atomic_write(path, tomli_w.dumps(cleaned))
        else:
            path.unlink()
        return True

    if path.read_text() == generated_content:
        path.unlink()
        return True

    return False


def _subtract_generated(existing: Any, generated: Any) -> Any:
    if not isinstance(existing, dict) or not isinstance(generated, dict):
        return existing

    cleaned = dict(existing)
    for key, generated_value in generated.items():
        if key not in cleaned:
            continue
        existing_value = cleaned[key]
        if existing_value == generated_value:
            del cleaned[key]
        elif isinstance(existing_value, dict) and isinstance(generated_value, dict):
            nested = _subtract_generated(existing_value, generated_value)
            if nested:
                cleaned[key] = nested
            else:
                del cleaned[key]
    return cleaned


def _remove_empty_generated_dirs(home: Path, project_root: Path | None) -> None:
    roots = [home / ".claude", home / ".codex", home / ".agents"]
    if project_root is not None:
        roots.extend(
            [project_root / ".claude", project_root / ".codex", project_root / ".agents"]
        )

    for root in roots:
        _remove_empty_tree(root)


def _remove_empty_tree(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        return
    for child in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if child.is_dir() and not child.is_symlink():
            _rmdir_if_empty(child)
    _rmdir_if_empty(root)


def _rmdir_if_empty(path: Path) -> None:
    try:
        path.rmdir()
    except OSError:
        pass
