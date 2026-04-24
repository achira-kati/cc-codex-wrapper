from ccx.scope import discover


def test_user_scope_always_returns_home_ccx(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    scopes = discover(cwd=tmp_path)
    assert scopes.user == tmp_path / ".ccx"


def test_no_project_scope_when_no_dotccx_found(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    subdir = tmp_path / "unrelated"
    subdir.mkdir()
    scopes = discover(cwd=subdir)
    assert scopes.project is None


def test_project_scope_found_at_cwd(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    project = tmp_path / "repo"
    (project / ".ccx").mkdir(parents=True)
    scopes = discover(cwd=project)
    assert scopes.project == project / ".ccx"


def test_project_scope_found_in_ancestor(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    project = tmp_path / "repo"
    (project / ".ccx").mkdir(parents=True)
    deep = project / "src" / "nested"
    deep.mkdir(parents=True)
    scopes = discover(cwd=deep)
    assert scopes.project == project / ".ccx"


def test_project_walk_stops_at_first_match(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    outer = tmp_path / "outer"
    inner = outer / "inner"
    (outer / ".ccx").mkdir(parents=True)
    (inner / ".ccx").mkdir(parents=True)
    deep = inner / "src"
    deep.mkdir(parents=True)
    scopes = discover(cwd=deep)
    assert scopes.project == inner / ".ccx"
