from pathlib import Path

import pytest

from ccx.loader import LoaderError, load_canonical

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_minimal():
    scope = FIXTURES / "canonical_minimal"
    c = load_canonical(scope)
    assert c.agents_md == "# Project conventions\nAlways run tests before committing.\n"
    assert "context7" in c.mcp_servers
    assert c.mcp_servers["context7"]["command"] == "npx"
    assert c.hooks["PreToolUse"][0]["matcher"] == "Bash"
    assert c.skills_dir == scope / "skills"
    assert (c.skills_dir / "example" / "SKILL.md").exists()


def test_load_missing_scope_returns_empty():
    c = load_canonical(Path("/nonexistent/ccx/scope"))
    assert c.agents_md == ""
    assert c.mcp_servers == {}
    assert c.hooks == {}


def test_load_mcp_missing_command_and_url_raises():
    scope = FIXTURES / "canonical_broken"
    with pytest.raises(LoaderError) as exc:
        load_canonical(scope)
    assert "servers.bad" in str(exc.value)
    assert "command" in str(exc.value) or "url" in str(exc.value)


def test_passthrough_dirs_returned_as_paths(tmp_path):
    (tmp_path / "claude" / "settings.json").parent.mkdir(parents=True)
    (tmp_path / "claude" / "settings.json").write_text('{"permissions": {}}')
    (tmp_path / "codex" / "rules").mkdir(parents=True)
    (tmp_path / "codex" / "rules" / "r.rules").write_text('prefix_rule(pattern=["x"])')
    c = load_canonical(tmp_path)
    assert c.claude_passthrough == tmp_path / "claude"
    assert c.codex_passthrough == tmp_path / "codex"
