from ccx.loader import Canonical
from ccx.renderers.memory import render_memory


def test_user_scope_cc_writes_include_stub(tmp_path):
    home = tmp_path / "home"
    (home / ".ccx").mkdir(parents=True)
    (home / ".ccx" / "AGENTS.md").write_text("# body")
    user = Canonical(root=home / ".ccx", agents_md="# body")

    writes = render_memory(user=user, project=None, home=home, project_root=None)

    claude_md = home / ".claude" / "CLAUDE.md"
    stub = next(w for w in writes if w.path == claude_md)
    assert f"@{home}/.ccx/AGENTS.md" in stub.content


def test_user_scope_codex_copies_agents_md(tmp_path):
    home = tmp_path / "home"
    (home / ".ccx").mkdir(parents=True)
    (home / ".ccx" / "AGENTS.md").write_text("# body\n")
    user = Canonical(root=home / ".ccx", agents_md="# body\n")

    writes = render_memory(user=user, project=None, home=home, project_root=None)
    codex_agents = home / ".codex" / "AGENTS.md"
    copy = next(w for w in writes if w.path == codex_agents)
    assert copy.content == "# body\n"


def test_user_scope_codex_appends_extras(tmp_path):
    home = tmp_path / "home"
    (home / ".ccx" / "codex").mkdir(parents=True)
    (home / ".ccx" / "AGENTS.md").write_text("# portable\n")
    (home / ".ccx" / "codex" / "AGENTS.md").write_text("# codex-only\n")
    user = Canonical(
        root=home / ".ccx",
        agents_md="# portable\n",
        codex_passthrough=home / ".ccx" / "codex",
    )

    writes = render_memory(user=user, project=None, home=home, project_root=None)
    codex_agents = home / ".codex" / "AGENTS.md"
    copy = next(w for w in writes if w.path == codex_agents)
    assert "# portable" in copy.content
    assert "# codex-only" in copy.content


def test_project_scope_symlink_planned(tmp_path):
    home = tmp_path / "home"
    proj_root = tmp_path / "repo"
    (proj_root / ".ccx").mkdir(parents=True)
    (proj_root / ".ccx" / "AGENTS.md").write_text("# project\n")
    project = Canonical(root=proj_root / ".ccx", agents_md="# project\n")

    writes = render_memory(user=None, project=project, home=home, project_root=proj_root)
    symlink_entry = next(
        (w for w in writes if w.path == proj_root / "AGENTS.md" and w.kind == "symlink"),
        None,
    )
    assert symlink_entry is not None
    assert symlink_entry.symlink_to == proj_root / ".ccx" / "AGENTS.md"
