import json
import tomllib
from pathlib import Path

import yaml

from ccx.renderers.mcp import render_mcp

FIXTURES = Path(__file__).parent / "fixtures" / "mcp"


def _load_input(name: str) -> dict:
    data = yaml.safe_load((FIXTURES / name / "input.yaml").read_text())
    return data["servers"]


def test_stdio_renders_to_cc_json():
    servers = _load_input("stdio")
    writes = render_mcp(user_servers=servers, project_servers={}, home=Path("/h"), project_root=None)
    cc_write = next(w for w in writes if w.path == Path("/h/.claude.json"))
    actual = json.loads(cc_write.content)
    expected = json.loads((FIXTURES / "stdio" / "expected-claude.json").read_text())
    assert actual == expected


def test_stdio_renders_to_codex_toml():
    servers = _load_input("stdio")
    writes = render_mcp(user_servers=servers, project_servers={}, home=Path("/h"), project_root=None)
    codex_write = next(w for w in writes if w.path == Path("/h/.codex/config.toml"))
    actual = tomllib.loads(codex_write.content)
    expected = tomllib.loads((FIXTURES / "stdio" / "expected-codex.toml").read_text())
    assert actual == expected


def test_http_renders_to_codex_toml():
    servers = _load_input("http")
    writes = render_mcp(user_servers=servers, project_servers={}, home=Path("/h"), project_root=None)
    codex_write = next(w for w in writes if w.path == Path("/h/.codex/config.toml"))
    actual = tomllib.loads(codex_write.content)
    expected = tomllib.loads((FIXTURES / "http" / "expected-codex.toml").read_text())
    assert actual == expected


def test_project_overrides_user_by_server_name():
    user = {"s1": {"command": "old"}}
    project = {"s1": {"command": "new"}}
    writes = render_mcp(
        user_servers=user, project_servers=project,
        home=Path("/h"), project_root=Path("/repo"),
    )
    project_cc = next(w for w in writes if w.path == Path("/repo/.mcp.json"))
    data = json.loads(project_cc.content)
    assert data["mcpServers"]["s1"]["command"] == "new"


def test_empty_servers_produces_no_writes():
    writes = render_mcp(user_servers={}, project_servers={}, home=Path("/h"), project_root=None)
    assert writes == []
