import runpy
from copy import deepcopy
from pathlib import Path

import pytest

from dcfa.attribution import attribute, edits

# Reuse the accepted P14 synthetic producer. P15 expectations below are independent.
fixture = runpy.run_path(str(Path(__file__).with_name("test_policy_diff.py")))


def case(tmp_path, old, new, states=("SS", "SV")):
    sides = []
    bundles = []
    for name, code, s in zip(("old", "new"), (old, new), states, strict=True):
        root = tmp_path / name
        b, side = fixture["snapshot"](root, code, s)
        b["files"] = {p.name: p.read_bytes() for p in root.iterdir()}
        bundles.append(b)
        sides.append(side)
    m = fixture["align"](*bundles)
    d = fixture["compare"](*sides, m, fixture["CONTEXTS"])
    return (*bundles, m, d)


def test_changed_operand_and_unrelated_edits(tmp_path):
    args = case(tmp_path, "a=1\n\nsend(1)", "a=2\n\nsend(2)")
    r = attribute(*args)
    (association,) = r["associations"]
    assert association["certainty"] == "definite" and association["direction"] == "added"
    (dep,) = association["semantic_dependencies"]
    assert dep["before"]["value"] != dep["after"]["value"]
    assert len(r["files"][0]["hunks"]) == 2
    assert {
        h["hunk"] for p in association["paths"] for loc in p["locations"] for h in loc["edits"]
    } == {1}
    assert r["causal_status"] == "not_established"


def test_comment_and_unknown(tmp_path):
    r = attribute(*case(tmp_path, "send(1) # a", "send(1) # b", ("S?", "SV")))
    (a,) = r["associations"]
    assert a["certainty"] == "possible" and not a["semantic_dependencies"]
    assert all(p["locations"] for p in a["paths"])
    assert r["files"][0]["structure"][0] == r["files"][0]["structure"][1]


def test_unchanged_risk(tmp_path):
    r = attribute(*case(tmp_path, "send(1)", "send(2)", ("SV", "SV")))
    assert r["files"] and not r["associations"]


def test_evidence_mismatch(tmp_path):
    a, b, m, d = case(tmp_path, "send(1)", "send(2)")
    changed = deepcopy(d)
    changed["sides"][1]["reports"][1]["witnesses"][0]["evidence"][0]["witnesses"][0]["path"] = (
        "bogus"
    )
    with pytest.raises(ValueError, match="evidence mismatch"):
        attribute(a, b, m, changed)
    b["files"]["main.py"] = b"other"
    with pytest.raises(ValueError, match="digest mismatch"):
        attribute(a, b, m, d)


def test_deletion_and_addition():
    old, new = edits({"a.py": b"f(1)\n"}, {"b.py": b""})
    assert old["kind"] == "deleted" and old["after"] is None
    assert old["hunks"][0]["before"] == [1, 1] and old["hunks"][0]["after"] is None
    assert new["kind"] == "added" and new["before"] is None


def test_multiple_hunks_on_one_witness(tmp_path):
    old = "send(\n    1,\n    2,\n    3,\n)"
    new = "send(\n    4,\n    2,\n    5,\n)"
    r = attribute(*case(tmp_path, old, new))
    (a,) = r["associations"]
    assert a["candidate_edits"] == [{"path": "main.py", "hunk": 0}, {"path": "main.py", "hunk": 1}]
    assert a["joint_sufficiency"] == "unknown"


@pytest.mark.parametrize(
    "old,new,expected",
    [
        ("spare()\npublish('old')", "publish('new')", {"before": 2, "after": 1}),
        ("send(1)", "aux=0\nsend(2)", {"before": 1, "after": 2}),
        ("aux=0\nf(3)\nlast=1", "aux=4\nf(5)\nlast=7", {"before": 2, "after": 2}),
    ],
)
def test_adjacent_hunk_intersection(tmp_path, old, new, expected):
    import ast

    r = attribute(*case(tmp_path, old, new))
    (association,) = r["associations"]
    (dep,) = association["semantic_dependencies"]
    for side, code in (("before", old), ("after", new)):
        line = expected[side]
        value = ast.parse(code.splitlines()[line - 1]).body[0].value.args[0]
        assert dep[side]["value"] == ast.dump(value)
        (path,) = (p for p in association["paths"] if p["side"] == side)
        hits = [h for loc in path["locations"] for h in loc["edits"]]
        assert hits and all(h["matched_lines"] == [line, line] for h in hits)
    assert r["causal_status"] == "not_established" and association["joint_sufficiency"] == "unknown"


def test_multiline_clips_both_ways(tmp_path):
    old = "spare=0\nsend(\n    1,\n    2\n)"
    new = "spare=1\npublish(\n    3,\n    2\n)"
    r = attribute(*case(tmp_path, old, new))
    (a,) = r["associations"]
    for p in a["paths"]:
        hits = [hit for loc in p["locations"] for hit in loc["edits"]]
        assert hits and all(h["matched_lines"] == [2, 3] for h in hits)
    assert not a["semantic_dependencies"]


def test_authorization_only_has_no_edit(tmp_path):
    r = attribute(*case(tmp_path, "send('same')", "send('same')"))
    (a,) = r["associations"]
    assert a["certainty"] == "definite"
    assert not r["files"] and not a["candidate_edits"] and not a["semantic_dependencies"]
