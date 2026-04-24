import yaml

from ccx.cli import main


def test_init_creates_scope_directory(tmp_ccx_home):
    exit_code = main(["init"])
    assert exit_code == 0
    scope = tmp_ccx_home / ".ccx"
    assert scope.is_dir()
    assert (scope / "AGENTS.md").is_file()
    assert (scope / "mcp.yaml").is_file()
    assert (scope / "hooks.yaml").is_file()
    assert (scope / "skills").is_dir()
    assert (scope / "claude").is_dir()
    assert (scope / "codex").is_dir()
    assert (scope / ".gitignore").is_file()


def test_init_is_idempotent(tmp_ccx_home):
    assert main(["init"]) == 0
    (tmp_ccx_home / ".ccx" / "AGENTS.md").write_text("# my content")
    assert main(["init"]) == 0
    assert (tmp_ccx_home / ".ccx" / "AGENTS.md").read_text() == "# my content"


def test_init_scaffolds_valid_starter_mcp_yaml(tmp_ccx_home):
    main(["init"])
    data = yaml.safe_load((tmp_ccx_home / ".ccx" / "mcp.yaml").read_text())
    assert data == {"servers": {}}
