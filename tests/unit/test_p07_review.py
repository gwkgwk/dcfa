"""Regression oracles for P07 published evidence, independent of upstream node IDs."""

import hashlib
import importlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
P07 = ROOT / "reproduction" / "P07"


@pytest.fixture
def checker(monkeypatch):
    monkeypatch.syspath_prepend(str(P07))
    return importlib.import_module("check_record")


@pytest.mark.parametrize("case,folder", [("function-body", "results"), ("top-level", "top-level")])
def test_archived_and_repeated_records(checker, case, folder):
    for location in (P07 / folder, P07 / "recheck" / case):
        checker.check(location, case)
        for f in location.glob("*.graphml"):
            fields = [d.text or "" for d in ET.parse(f).iter(checker.NS + "data")]
            assert not any(":/Users/" in value or "\\Users\\" in value for value in fields)
            if f.stem == "after":
                assert "sample-1.1.0/index.js" in fields


@pytest.mark.parametrize(
    "change", ["code", "name", "type", "direction", "remove", "other-result", "missing-graph"]
)
def test_invalid_witness_fails(checker, tmp_path, change):
    case = tmp_path / "record"
    shutil.copytree(P07 / "top-level", case)
    file = case / "after.graphml"
    if change == "missing-graph":
        file.unlink()
        with pytest.raises(FileNotFoundError):
            checker.check(case, "top-level")
        return
    tree = ET.parse(file)
    graph = tree.getroot().find(checker.NS + "graph")
    record = json.loads((case / "module-returns.json").read_text())
    argument, callee = sorted(record["after"]["relations"][0][1], key=len)
    edge = next(
        e
        for e in graph.iter(checker.NS + "edge")
        if (e.get("source"), e.get("target")) == tuple(callee[-2:])
    )
    if change in ("code", "name", "type"):
        value = {"code": "demo.txt", "name": "path.basename", "type": "FUNC_OBJ_TO_RET_VAL"}[change]
        parent = (
            edge
            if change == "type"
            else graph.find(
                checker.NS + f"node[@id='{argument[0] if change == 'code' else callee[1]}']"
            )
        )
        next(d for d in parent if d.text == value).text = "unrelated"
    elif change == "direction":
        edge.set("source", callee[-1])
        edge.set("target", callee[-2])
    elif change == "remove":
        graph.remove(edge)
    else:
        callee[-1] = argument[0]
        (case / "module-returns.json").write_text(json.dumps(record))
    tree.write(file)
    with pytest.raises(ValueError):
        checker.check(case, "top-level")


def test_portability_only_rewrites_exact_entry(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(P07))
    portable = importlib.import_module("portable_graph")
    entry = tmp_path / "nested & pair" / "input.js"
    f = tmp_path / "graph.xml"
    tree = ET.Element(portable.NS + "graphml")
    for text in (entry.as_posix(), str(entry), entry.as_posix() + ".backup"):
        ET.SubElement(tree, portable.NS + "data").text = text
    ET.ElementTree(tree).write(f)
    portable.localize_entry(f, tmp_path, entry)
    assert [d.text for d in ET.parse(f).getroot()] == [
        "nested & pair/input.js",
        "nested & pair/input.js",
        entry.as_posix() + ".backup",
    ]


def test_recovered_function_body_bytes():
    for version, digest in (
        ("1.0.0", "56b48c58de91f33ebcfc648a01b5d356c24439462dda5ba3f7028dd820d36944"),
        ("1.1.0", "0a97d18bc0d533d413f022fb6e3b7d8ee0b0857c7a7241c82f3a9f95443b775b"),
    ):
        source = P07 / "inputs" / "function-body" / f"{version}.js"
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


def test_preflight_identifies_history_and_final_report():
    preflight = (ROOT / "docs/P07-preflight.md").read_text(encoding="utf-8")
    assert "历史预检状态（d0f4dd9" in preflight
    assert "(P07-report.md)" in preflight
    assert (ROOT / "docs/P07-report.md").is_file()


def test_confirmed_upstream_in_registry():
    from dcfa.registry import validate

    contents = (ROOT / "third_party/sources.json").read_bytes()
    assert validate(contents) >= 1
    item = next(i for i in json.loads(contents)["sources"] if i["id"] == "rogueone-p07")
    assert item["commit"] == "d92d7de0eedb5754dc4d41b426d45a83715c0bd1"
    assert item["kind"] == "original"
