from ccx.cli import main


def test_status_shows_clean_when_in_sync(tmp_ccx_home, capsys):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# hi")
    main(["sync"])
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "clean" in out.lower() or "in sync" in out.lower()


def test_status_shows_drift_after_canonical_edit(tmp_ccx_home, capsys):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# one")
    main(["sync"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# two")
    rc = main(["status"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "drift" in out.lower() or "stale" in out.lower()


def test_sync_check_exits_nonzero_on_drift(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# one")
    main(["sync"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# two")
    assert main(["sync", "--check"]) != 0


def test_sync_check_exits_zero_when_clean(tmp_ccx_home):
    main(["init"])
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# body")
    main(["sync"])
    assert main(["sync", "--check"]) == 0
