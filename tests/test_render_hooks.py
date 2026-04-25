import json
import tomllib
from pathlib import Path

import yaml

from ccx.renderers.hooks import render_hooks

FIXTURES = Path(__file__).parent / "fixtures" / "hooks"


def _load_input(name: str) -> dict:
    return yaml.safe_load((FIXTURES / name / "input.yaml").read_text())["hooks"]


def test_shared_events_render_to_cc_settings():
    hooks = _load_input("basic")
    writes = render_hooks(user_hooks=hooks, project_hooks={}, home=Path("/h"), project_root=None)
    cc = next(w for w in writes if w.path == Path("/h/.claude/settings.json"))
    actual = json.loads(cc.content)
    expected = json.loads((FIXTURES / "basic" / "expected-cc-settings.json").read_text())
    assert actual == expected


def test_shared_events_render_to_codex_hooks_json():
    hooks = _load_input("basic")
    writes = render_hooks(user_hooks=hooks, project_hooks={}, home=Path("/h"), project_root=None)
    cx = next(w for w in writes if w.path == Path("/h/.codex/hooks.json"))
    actual = json.loads(cx.content)
    expected = json.loads((FIXTURES / "basic" / "expected-codex-hooks.json").read_text())
    assert actual == expected


def test_codex_features_config_toml_enables_hooks():
    hooks = _load_input("basic")
    writes = render_hooks(user_hooks=hooks, project_hooks={}, home=Path("/h"), project_root=None)
    cfg = next(w for w in writes if w.path == Path("/h/.codex/config.toml"))
    data = tomllib.loads(cfg.content)
    assert data["features"]["codex_hooks"] is True


def test_project_hooks_append_to_user_hooks_under_same_event():
    user = {
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "user_cmd"}]}]
    }
    project = {
        "PreToolUse": [{"matcher": "Edit", "hooks": [{"command": "project_cmd"}]}]
    }
    writes = render_hooks(
        user_hooks=user, project_hooks=project, home=Path("/h"), project_root=Path("/repo"),
    )
    proj_cc = next(w for w in writes if w.path == Path("/repo/.claude/settings.json"))
    data = json.loads(proj_cc.content)
    matchers = [m["matcher"] for m in data["hooks"]["PreToolUse"]]
    assert matchers == ["Bash", "Edit"]
    handlers = [m["hooks"][0] for m in data["hooks"]["PreToolUse"]]
    assert handlers == [
        {"type": "command", "command": "user_cmd"},
        {"type": "command", "command": "project_cmd"},
    ]


def test_empty_hooks_produces_no_writes():
    writes = render_hooks(user_hooks={}, project_hooks={}, home=Path("/h"), project_root=None)
    assert writes == []
