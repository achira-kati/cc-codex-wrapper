import json

from ccx.renderers.memory import PlannedWrite
from ccx.renderers.passthrough import render_passthrough


def test_passthrough_copies_non_overlapping_files(tmp_path):
    home = tmp_path / "home"
    src = home / ".ccx" / "codex" / "rules" / "default.rules"
    src.parent.mkdir(parents=True)
    src.write_text('prefix_rule(pattern=["git","push"], decision="prompt")')

    writes = render_passthrough(
        scope_dir=home / ".ccx",
        target_root=home,
        generated_writes=[],
        subdir="codex",
    )
    dest = home / ".codex" / "rules" / "default.rules"
    w = next(x for x in writes if x.path == dest)
    assert "prefix_rule" in w.content


def test_passthrough_merges_json_with_generated_write(tmp_path):
    home = tmp_path / "home"
    native_settings = home / ".ccx" / "claude" / "settings.json"
    native_settings.parent.mkdir(parents=True)
    native_settings.write_text(json.dumps({"permissions": {"allow": ["Bash(ls)"]}}))

    generated = PlannedWrite(
        path=home / ".claude" / "settings.json",
        kind="file",
        content=json.dumps({"hooks": {"PreToolUse": []}}),
    )
    writes = render_passthrough(
        scope_dir=home / ".ccx",
        target_root=home,
        generated_writes=[generated],
        subdir="claude",
    )
    merged = next(w for w in writes if w.path == home / ".claude" / "settings.json")
    data = json.loads(merged.content)
    assert "permissions" in data
    assert "hooks" in data


def test_passthrough_native_wins_on_scalar_conflict(tmp_path):
    home = tmp_path / "home"
    native = home / ".ccx" / "claude" / "settings.json"
    native.parent.mkdir(parents=True)
    native.write_text(json.dumps({"cleanupPeriodDays": 30}))

    generated = PlannedWrite(
        path=home / ".claude" / "settings.json",
        kind="file",
        content=json.dumps({"cleanupPeriodDays": 7}),
    )
    writes = render_passthrough(
        scope_dir=home / ".ccx", target_root=home,
        generated_writes=[generated], subdir="claude",
    )
    merged = next(w for w in writes if w.path == home / ".claude" / "settings.json")
    assert json.loads(merged.content)["cleanupPeriodDays"] == 30


def test_passthrough_skips_subdirs_used_by_renderer(tmp_path):
    # CLAUDE.md and AGENTS.md inside claude/ and codex/ are handled by memory renderer, not passthrough.
    home = tmp_path / "home"
    claude_md = home / ".ccx" / "claude" / "CLAUDE.md"
    claude_md.parent.mkdir(parents=True)
    claude_md.write_text("cc extras")

    writes = render_passthrough(
        scope_dir=home / ".ccx", target_root=home,
        generated_writes=[], subdir="claude",
    )
    assert home / ".claude" / "CLAUDE.md" not in {w.path for w in writes}


def test_missing_passthrough_dir_returns_empty(tmp_path):
    home = tmp_path / "home"
    (home / ".ccx").mkdir(parents=True)
    writes = render_passthrough(
        scope_dir=home / ".ccx", target_root=home,
        generated_writes=[], subdir="claude",
    )
    assert writes == []
