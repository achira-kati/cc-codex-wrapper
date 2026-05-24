import os
import sys

import pytest

from ccx.cli import main


@pytest.fixture
def fake_claude_on_path(tmp_path, monkeypatch):
    """Install a fake `claude` binary that echoes its args to a log file."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "claude-call.log"
    if sys.platform == "win32":
        script = bindir / "claude.cmd"
        script.write_text(f"@echo off\r\necho %* > \"{log}\"\r\nexit /b 0\r\n")
    else:
        script = bindir / "claude"
        script.write_text(f"#!/bin/sh\necho \"$@\" > {log}\nexit 0\n")
        script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    return log


def test_launcher_execs_claude_with_args(tmp_ccx_home, fake_claude_on_path, monkeypatch):
    main(["init"])
    monkeypatch.setenv("CCX_TEST_EXEC", "1")
    rc = main(["claude", "foo", "bar"])
    assert rc == 0
    assert fake_claude_on_path.read_text().strip() == "foo bar"


def test_launcher_skips_sync_when_env_set(tmp_ccx_home, fake_claude_on_path, monkeypatch):
    main(["init"])
    monkeypatch.setenv("CCX_SKIP_SYNC", "1")
    monkeypatch.setenv("CCX_TEST_EXEC", "1")
    rc = main(["claude"])
    assert rc == 0
    # Sync did not run → no manifest.
    assert not (tmp_ccx_home / ".ccx" / ".state" / "manifest.json").exists()


def test_launcher_aborts_on_sync_failure(tmp_ccx_home, fake_claude_on_path, monkeypatch):
    main(["init"])
    # Corrupt mcp.yaml to force LoaderError (missing command/url).
    (tmp_ccx_home / ".ccx" / "mcp.yaml").write_text("servers:\n  bad:\n    args: [x]\n")
    monkeypatch.setenv("CCX_TEST_EXEC", "1")
    rc = main(["claude"])
    assert rc != 0
