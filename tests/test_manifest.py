import hashlib
from pathlib import Path

from ccx.manifest import Manifest


def test_empty_manifest_has_no_entries(tmp_path):
    m = Manifest.load(tmp_path / "nonexistent.json")
    assert m.entries == {}


def test_manifest_roundtrip(tmp_path):
    path = tmp_path / "manifest.json"
    m = Manifest()
    m.record(Path("/a/b.txt"), "abc123")
    m.save(path)
    loaded = Manifest.load(path)
    assert loaded.entries == {"/a/b.txt": "abc123"}


def test_hash_file(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert Manifest.hash_file(f) == expected


def test_is_managed_true_when_hash_matches(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("content")
    m = Manifest()
    m.record(target, Manifest.hash_file(target))
    assert m.is_managed(target) is True


def test_is_managed_false_when_hash_drifts(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("original")
    m = Manifest()
    m.record(target, Manifest.hash_file(target))
    target.write_text("edited by user")
    assert m.is_managed(target) is False


def test_is_managed_false_when_not_in_manifest(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("x")
    m = Manifest()
    assert m.is_managed(target) is False


def test_orphans_returns_entries_no_longer_in_desired():
    m = Manifest()
    m.record(Path("/a.txt"), "h1")
    m.record(Path("/b.txt"), "h2")
    m.record(Path("/c.txt"), "h3")
    desired = {Path("/a.txt"), Path("/c.txt")}
    orphans = m.orphans(desired)
    assert orphans == {Path("/b.txt")}
