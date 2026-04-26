import pytest


@pytest.fixture
def tmp_ccx_home(tmp_path, monkeypatch):
    """Isolated HOME so tests never touch the user's real ~/.ccx/ or ~/.claude/."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.chdir(tmp_path)
    return fake_home
