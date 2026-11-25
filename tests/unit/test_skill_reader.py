import os

import pytest

from dcfa import skill_reader as reader


def collect(root):
    issues = []
    rows = list(reader.scan(root, lambda *args: issues.append(args)))
    return rows, issues


def test_inventory_and_budget(tmp_path, monkeypatch):
    (tmp_path / "SKILL.md").write_bytes(b"1234")
    (tmp_path / "notes.bin").write_bytes(b"\xff")
    monkeypatch.setattr(reader, "MAX_FILE", 3)
    rows, issues = collect(tmp_path)
    assert all(text is None for _, _, text in rows)
    assert {issue[1] for issue in issues} == {"byte_limit", "inventory_only"}
    monkeypatch.setattr(reader, "MAX_ENTRIES", 1)
    assert collect(tmp_path)[1][0][1] == "entry_limit"


def test_hardlink_and_invalid_root(tmp_path):
    root = tmp_path / "skill"
    root.mkdir()
    outside = tmp_path / "synthetic.txt"
    outside.write_text("synthetic")
    os.link(outside, root / "SKILL.md")
    assert collect(root) == ([], [("read_failure", "unsafe_entry", "SKILL.md")])
    assert collect(outside)[1][0][1] == "unsafe_root"


def test_directory_redirect(tmp_path):
    root = tmp_path / "skill"
    root.mkdir()
    redirect = tmp_path / "redirect"
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(root), str(redirect))
    else:
        redirect.symlink_to(root, target_is_directory=True)
    assert collect(redirect)[1][0][1] == "unsafe_root"
    with pytest.raises(StopIteration):
        next(iter(collect(redirect)[0]))
