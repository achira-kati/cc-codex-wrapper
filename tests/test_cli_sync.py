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
    # Use .codex/config.toml (owned mode) to test orphan removal.
    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    main(["sync"])
    codex_toml = tmp_ccx_home / ".codex" / "config.toml"
    assert codex_toml.is_file()

    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text("servers: {}\n")
    main(["sync"])
    assert not codex_toml.exists()


def test_sync_preserves_edited_orphan_without_force(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    main(["sync"])
    hooks_json = tmp_ccx_home / ".codex" / "hooks.json"
    assert hooks_json.exists()

    # User edits the file.
    hooks_json.write_text('{"edited": "by user"}')

    # Remove hooks from canonical so the file becomes an orphan.
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text("hooks: {}\n")

    main(["sync"])
    # Edited orphan is preserved.
    assert hooks_json.exists()
    assert "edited" in hooks_json.read_text()


def test_sync_force_removes_edited_orphan(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    main(["sync"])
    hooks_json = tmp_ccx_home / ".codex" / "hooks.json"
    hooks_json.write_text('{"edited": "by user"}')
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text("hooks: {}\n")

    main(["sync", "--force"])
    assert not hooks_json.exists()


def test_claude_json_merge_preserves_existing_cc_state(tmp_ccx_home):
    """CC state in ~/.claude.json must survive ccx sync."""
    import yaml

    # Simulate CC's pre-existing state.
    claude_json = tmp_ccx_home / ".claude.json"
    claude_json.write_text(json.dumps({
        "projects": {"/path/to/repo": {"lastOpened": "2026-01-01"}},
        "autoConnectIde": True,
    }))

    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    assert main(["sync"]) == 0

    data = json.loads(claude_json.read_text())
    # CC state preserved:
    assert "projects" in data
    assert data["projects"]["/path/to/repo"]["lastOpened"] == "2026-01-01"
    assert data["autoConnectIde"] is True
    # ccx's mcpServers added:
    assert "mcpServers" in data
    assert data["mcpServers"]["s1"]["command"] == "npx"


def test_claude_json_merge_no_backup_created(tmp_ccx_home):
    """Merge-mode should not create a backup (non-destructive)."""
    import yaml

    tmp_ccx_home.mkdir(exist_ok=True)
    claude_json = tmp_ccx_home / ".claude.json"
    claude_json.write_text(json.dumps({"some": "state"}))

    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    main(["sync"])

    # Backups dir should not contain .claude.json (but may have other files).
    backups = list((tmp_ccx_home / ".ccx" / "backups").glob("**/.claude.json"))
    assert backups == []


def test_claude_json_merge_accepts_cc_rewrites_between_syncs(tmp_ccx_home):
    """If CC rewrites ~/.claude.json between syncs, ccx re-merges without error."""
    import yaml

    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    assert main(["sync"]) == 0

    # Simulate CC rewriting the file with a new key.
    claude_json = tmp_ccx_home / ".claude.json"
    data = json.loads(claude_json.read_text())
    data["newKeyFromCC"] = "added by cc"
    claude_json.write_text(json.dumps(data))

    # Second sync should not error and should preserve CC's addition.
    assert main(["sync"]) == 0
    data = json.loads(claude_json.read_text())
    assert data["newKeyFromCC"] == "added by cc"
    assert "mcpServers" in data


def test_claude_json_orphan_not_unlinked_when_merge_mode(tmp_ccx_home):
    """If canonical loses all MCP, merge-mode file is NOT unlinked."""
    import yaml

    main(["init"])
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text(
        yaml.dump({"servers": {"s1": {"command": "npx"}}})
    )
    main(["sync"])
    claude_json = tmp_ccx_home / ".claude.json"
    assert claude_json.exists()

    # Remove MCP from canonical.
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text("servers: {}\n")
    main(["sync"])

    # File should still exist — we don't own it wholesale.
    assert claude_json.exists()
