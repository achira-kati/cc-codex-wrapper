from ccx.atomic import atomic_write, replace_with_symlink


def test_atomic_write_creates_file(tmp_path):
    target = tmp_path / "out.txt"
    atomic_write(target, "hello")
    assert target.read_text() == "hello"


def test_atomic_write_creates_parent_dirs(tmp_path):
    target = tmp_path / "nested" / "deep" / "out.txt"
    atomic_write(target, "x")
    assert target.read_text() == "x"


def test_atomic_write_overwrites(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("old")
    atomic_write(target, "new")
    assert target.read_text() == "new"


def test_atomic_write_leaves_no_tmp_on_success(tmp_path):
    atomic_write(tmp_path / "out.txt", "x")
    leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".ccx.tmp")]
    assert leftovers == []


def test_replace_with_symlink_creates_link(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    target = tmp_path / "link"
    replace_with_symlink(target, source)
    assert target.samefile(source)


def test_replace_with_symlink_replaces_existing_symlink(tmp_path):
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    target = tmp_path / "link"
    replace_with_symlink(target, old)
    replace_with_symlink(target, new)
    assert target.samefile(new)
