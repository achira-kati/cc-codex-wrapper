from ccx.loader import Canonical
from ccx.renderers.skills import render_skills


def test_user_scope_creates_two_symlinks(tmp_path):
    home = tmp_path / "home"
    skills_dir = home / ".ccx" / "skills"
    skills_dir.mkdir(parents=True)
    user = Canonical(root=home / ".ccx", skills_dir=skills_dir)

    writes = render_skills(user=user, project=None, home=home, project_root=None)
    paths = {w.path for w in writes}
    assert home / ".claude" / "skills" in paths
    assert home / ".agents" / "skills" in paths
    for w in writes:
        assert w.kind == "symlink"
        assert w.symlink_to == skills_dir


def test_no_skills_dir_no_writes(tmp_path):
    home = tmp_path / "home"
    user = Canonical(root=home / ".ccx", skills_dir=None)
    writes = render_skills(user=user, project=None, home=home, project_root=None)
    assert writes == []


def test_project_scope_creates_project_symlinks(tmp_path):
    home = tmp_path / "home"
    proj_root = tmp_path / "repo"
    project_skills = proj_root / ".ccx" / "skills"
    project_skills.mkdir(parents=True)
    project = Canonical(root=proj_root / ".ccx", skills_dir=project_skills)

    writes = render_skills(user=None, project=project, home=home, project_root=proj_root)
    paths = {w.path for w in writes}
    assert proj_root / ".claude" / "skills" in paths
    assert proj_root / ".agents" / "skills" in paths
