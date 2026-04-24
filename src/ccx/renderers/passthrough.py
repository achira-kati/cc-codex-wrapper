from pathlib import Path

from ccx.formats import merge_content
from ccx.renderers.memory import PlannedWrite

# Files handled by other renderers — never copied by passthrough.
RESERVED_NAMES = {"CLAUDE.md", "AGENTS.md"}


def render_passthrough(
    *,
    scope_dir: Path,
    target_root: Path,
    generated_writes: list[PlannedWrite],
    subdir: str,
) -> list[PlannedWrite]:
    """Walk ~/.ccx/<subdir>/... and produce writes for each file.

    `subdir` is 'claude' or 'codex'.
    `target_root` is home (for user scope) or project_root (for project scope).
    Generated writes that share a path get merged with the passthrough content
    (native from passthrough wins on conflicts).
    """
    passthrough_root = scope_dir / subdir
    if not passthrough_root.is_dir():
        return list(generated_writes)

    target_subdir = ".claude" if subdir == "claude" else ".codex"
    by_path = {w.path: w for w in generated_writes}
    writes: list[PlannedWrite] = list(generated_writes)

    for source in _walk_files(passthrough_root):
        if source.name in RESERVED_NAMES:
            continue
        rel = source.relative_to(passthrough_root)
        target = target_root / target_subdir / rel

        native_content = source.read_text()

        if target in by_path:
            merged_content = merge_content(by_path[target].content, native_content, target)
            new = PlannedWrite(path=target, kind="file", content=merged_content)
            idx = writes.index(by_path[target])
            writes[idx] = new
            by_path[target] = new
        else:
            writes.append(PlannedWrite(path=target, kind="file", content=native_content))

    return writes


def _walk_files(root: Path):
    for p in root.rglob("*"):
        if p.is_file():
            yield p
