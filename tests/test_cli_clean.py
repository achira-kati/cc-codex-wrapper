import json

import yaml

from ccx.cli import main
from ccx.manifest import Manifest


def test_clean_deletes_generated_targets_after_status_clean(tmp_ccx_home, capsys):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    assert main(["sync"]) == 0

    claude_json = tmp_ccx_home / ".claude.json"
    assert (tmp_ccx_home / ".claude" / "CLAUDE.md").is_file()
    assert (tmp_ccx_home / ".codex" / "AGENTS.md").is_file()
    assert claude_json.is_file()

    assert main(["clean"]) == 0

    out = capsys.readouterr().out
    assert "clean" in out.lower()
    assert not (tmp_ccx_home / ".claude" / "CLAUDE.md").exists()
    assert not (tmp_ccx_home / ".claude" / "settings.json").exists()
    assert not (tmp_ccx_home / ".codex" / "AGENTS.md").exists()
    assert not (tmp_ccx_home / ".codex" / "config.toml").exists()
    assert not (tmp_ccx_home / ".codex" / "hooks.json").exists()
    assert not (tmp_ccx_home / ".agents" / "skills").exists()
    assert not claude_json.exists()
    manifest = Manifest.load(tmp_ccx_home / ".ccx" / ".state" / "manifest.json")
    assert manifest.entries == {}


def test_clean_preserves_existing_merge_file_state(tmp_ccx_home):
    claude_json = tmp_ccx_home / ".claude.json"
    claude_json.write_text(json.dumps({"projects": {"/repo": {"lastOpened": "today"}}}))
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    assert main(["sync"]) == 0
    assert "mcpServers" in json.loads(claude_json.read_text())

    assert main(["clean"]) == 0

    data = json.loads(claude_json.read_text())
    assert data == {"projects": {"/repo": {"lastOpened": "today"}}}


def test_clean_aborts_when_status_reports_drift(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# first")
    assert main(["sync"]) == 0
    generated = tmp_ccx_home / ".codex" / "AGENTS.md"
    generated.write_text("manual edit")

    assert main(["clean"]) != 0

    assert generated.read_text() == "manual edit"


def test_clean_after_codex_only_sync_ignores_unsynced_claude_targets(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    assert main(["sync", "--codex"]) == 0

    codex_config = tmp_ccx_home / ".codex" / "config.toml"
    claude_settings = tmp_ccx_home / ".claude" / "settings.json"
    assert codex_config.is_file()
    assert not claude_settings.exists()

    assert main(["clean"]) == 0

    assert not codex_config.exists()
    assert not claude_settings.exists()
    manifest = Manifest.load(tmp_ccx_home / ".ccx" / ".state" / "manifest.json")
    assert manifest.entries == {}


def test_clean_ignores_manifest_entries_from_other_projects(tmp_ccx_home, tmp_path, monkeypatch):
    main(["init"])
    project = tmp_path / "current-project"
    project.mkdir()
    monkeypatch.chdir(project)
    main(["init", "--project"])
    (project / ".ccx" / "AGENTS.md").write_text("# current project")
    assert main(["sync"]) == 0

    other_project = tmp_path / "other-project"
    other_target = other_project / "AGENTS.md"
    other_target.parent.mkdir()
    other_target.write_text("# other project")
    manifest_path = tmp_ccx_home / ".ccx" / ".state" / "manifest.json"
    manifest = Manifest.load(manifest_path)
    manifest.record(other_target, Manifest.hash_file(other_target))
    manifest.save(manifest_path)

    assert main(["clean"]) == 0

    assert not (project / "AGENTS.md").exists()
    assert other_target.exists()
    manifest = Manifest.load(manifest_path)
    assert str(project / "AGENTS.md") not in manifest.entries
    assert manifest.entries[str(other_target)] == Manifest.hash_file(other_target)
