import json

import yaml

from ccx.cli import main


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_sync_backs_up_existing_claude_settings(tmp_ccx_home):
    existing = tmp_ccx_home / ".claude" / "settings.json"
    _write(existing, json.dumps({"my_key": "pre-existing"}))
    main(["init"])
    _write(tmp_ccx_home / ".ccx" / "hooks.yaml", "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo hi\n")

    assert main(["sync"]) == 0
    backups = list((tmp_ccx_home / ".ccx" / "backups").glob("*"))
    assert len(backups) == 1
    backed_up = backups[0] / ".claude" / "settings.json"
    assert json.loads(backed_up.read_text()) == {"my_key": "pre-existing"}


def test_sync_writes_claude_md_include_stub(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# Rules\nRun tests.\n")
    assert main(["sync"]) == 0
    claude_md = tmp_ccx_home / ".claude" / "CLAUDE.md"
    assert claude_md.is_file()
    content = claude_md.read_text()
    assert str(tmp_ccx_home / ".ccx" / "AGENTS.md") in content


def test_sync_aborts_on_manual_edit_to_managed_file(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# first")
    main(["sync"])

    claude_md = tmp_ccx_home / ".claude" / "CLAUDE.md"
    claude_md.write_text("edited by user")
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# second")

    assert main(["sync"]) != 0
    assert claude_md.read_text() == "edited by user"


def test_sync_force_overwrites_manual_edits(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# first")
    main(["sync"])

    claude_md = tmp_ccx_home / ".claude" / "CLAUDE.md"
    claude_md.write_text("edited by user")
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# second")

    assert main(["sync", "--force"]) == 0
    assert "edited by user" not in claude_md.read_text()


def test_sync_dry_run_does_not_write(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# body")
    assert main(["sync", "--dry-run"]) == 0
    assert not (tmp_ccx_home / ".claude" / "CLAUDE.md").exists()


def test_sync_removes_orphan_when_canonical_entry_gone(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    main(["sync"])
    cc_mcp = tmp_ccx_home / ".claude.json"
    assert cc_mcp.is_file()

    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text("servers: {}\n")
    main(["sync"])
    assert not cc_mcp.exists()
