from pathlib import Path

from ccx.backup import backup_file, new_backup_dir


def test_new_backup_dir_creates_timestamped_subdir(tmp_path):
    root = tmp_path / "backups"
    d = new_backup_dir(root)
    assert d.parent == root
    assert d.name.count("-") >= 2  # ISO timestamp has dashes
    assert d.is_dir()


def test_backup_file_moves_into_backup_dir(tmp_path):
    source = tmp_path / "home" / ".claude" / "settings.json"
    source.parent.mkdir(parents=True)
    source.write_text("content")
    backup_root = tmp_path / "backups"
    dest = new_backup_dir(backup_root)
    backup_file(source, dest, tmp_path / "home")
    assert not source.exists()
    moved = dest / ".claude" / "settings.json"
    assert moved.read_text() == "content"


def test_backup_file_preserves_tree_from_given_root(tmp_path):
    home = tmp_path / "home"
    source = home / "a" / "b" / "file.txt"
    source.parent.mkdir(parents=True)
    source.write_text("x")
    dest = tmp_path / "backup"
    dest.mkdir()
    backup_file(source, dest, home)
    assert (dest / "a" / "b" / "file.txt").read_text() == "x"
