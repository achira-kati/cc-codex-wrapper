import json

from ccx.cli import main


def test_restore_list_shows_available_snapshots(tmp_ccx_home, capsys):
    main(["init"])
    settings = tmp_ccx_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"existing": True}))
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    main(["sync"])

    main(["restore", "--list"])
    out = capsys.readouterr().out
    # Snapshot dirs are timestamped like 2026-04-24T12-34-56Z — contain "T" and dashes.
    assert "T" in out


def test_restore_applies_latest_backup(tmp_ccx_home):
    main(["init"])
    settings = tmp_ccx_home / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"existing": True}))
    (tmp_ccx_home / ".ccx" / "hooks.yaml").write_text(
        "hooks:\n  SessionStart:\n    - hooks:\n        - command: echo\n"
    )
    main(["sync"])

    # Sync wrote a new settings.json with hooks added.
    assert "hooks" in json.loads(settings.read_text())

    rc = main(["restore"])
    assert rc == 0
    assert json.loads(settings.read_text()) == {"existing": True}
