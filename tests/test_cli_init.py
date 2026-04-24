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


def test_init_project_creates_local_ccx_dir(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    monkeypatch.chdir(project)
    assert main(["init", "--project"]) == 0

    scope = project / ".ccx"
    assert scope.is_dir()
    assert (scope / "AGENTS.md").is_file()
    assert (scope / "mcp.yaml").is_file()
    assert (scope / "hooks.yaml").is_file()
    assert (scope / "skills").is_dir()
    assert (scope / "claude").is_dir()
    assert (scope / "codex").is_dir()
    assert (scope / ".gitignore").is_file()


def test_init_project_appends_to_gitignore(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    # Pre-existing .gitignore with unrelated content.
    (project / ".gitignore").write_text("node_modules/\n")
    monkeypatch.chdir(project)
    main(["init", "--project"])

    content = (project / ".gitignore").read_text()
    assert "node_modules/" in content  # preserved
    assert "# --- ccx (managed) ---" in content
    assert "/CLAUDE.md" in content
    assert "/.claude/" in content


def test_init_project_creates_gitignore_if_missing(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    monkeypatch.chdir(project)
    main(["init", "--project"])

    assert (project / ".gitignore").is_file()
    content = (project / ".gitignore").read_text()
    assert "# --- ccx (managed) ---" in content


def test_init_project_is_idempotent_for_gitignore(tmp_ccx_home, tmp_path, monkeypatch):
    project = tmp_path / "repo"
    project.mkdir()
    monkeypatch.chdir(project)
    main(["init", "--project"])
    content_first = (project / ".gitignore").read_text()
    main(["init", "--project"])
    content_second = (project / ".gitignore").read_text()
    assert content_first == content_second  # no duplicate block


def test_init_without_project_flag_still_creates_user_scope(tmp_ccx_home):
    assert main(["init"]) == 0
    # User scope created.
    assert (tmp_ccx_home / ".ccx" / "AGENTS.md").is_file()
