import json

import yaml

from ccx.cli import main


def test_project_mcp_overrides_user_by_server_name(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    (project / ".ccx").mkdir(parents=True)
    (project / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"shared": {"command": "project-command"}}})
    )

    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"shared": {"command": "user-command"}}})
    )

    monkeypatch.chdir(project)
    assert main(["sync"]) == 0

    project_mcp = json.loads((project / ".mcp.json").read_text())
    assert project_mcp["mcpServers"]["shared"]["command"] == "project-command"


def test_project_hooks_append_under_same_event(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    (project / ".ccx").mkdir(parents=True)
    (project / ".ccx" / "hooks.yaml").write_text(
        yaml.dump({
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Edit", "hooks": [{"command": "project"}]}
                ]
            }
        })
    )

    main(["init"])
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        yaml.dump({
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Bash", "hooks": [{"command": "user"}]}
                ]
            }
        })
    )

    monkeypatch.chdir(project)
    assert main(["sync"]) == 0

    proj_settings = json.loads((project / ".claude" / "settings.json").read_text())
    matchers = [m["matcher"] for m in proj_settings["hooks"]["PreToolUse"]]
    assert matchers == ["Bash", "Edit"]


def test_project_passthrough_writes_to_project_targets(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    (project / ".ccx" / "claude").mkdir(parents=True)
    (project / ".ccx" / "claude" / "settings.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(pnpm *)"]}})
    )

    main(["init"])
    monkeypatch.chdir(project)
    assert main(["sync"]) == 0

    proj_settings = json.loads((project / ".claude" / "settings.json").read_text())
    assert "Bash(pnpm *)" in proj_settings["permissions"]["allow"]
