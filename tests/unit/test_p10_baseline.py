"""Run the preregistered synthetic updates through the public baseline interfaces."""

import json
from pathlib import Path

import pytest

from dcfa.program_flow import analyze
from dcfa.trust_diff import compare

ORACLE = Path(__file__).resolve().parents[1] / "fixtures/synthetic/p10-oracle.json"
PAIRS = {"L": (":local", "import:api"), "AB": ("import:a", "import:b")}


def assert_metadata(side, modules):
    assert side["import_assumptions"] == {
        f"import:{name}": "unverified_external" for name in modules
    }


@pytest.mark.parametrize("case", json.loads(ORACLE.read_text()), ids=lambda c: c["case"])
def test_update(case, tmp_path):
    snapshots = []
    for version in ("before", "after"):
        root = tmp_path / version
        root.mkdir()
        (root / "SKILL.md").write_text(case.get(version + "_doc", "synthetic"))
        (root / "main.py").write_text(case.get(version, case["before"]))
        snapshots.append(analyze(root, "main.py"))
    result = compare(*snapshots)
    expected = {}
    for field in ("retained", "added", "deleted", "unresolved_before", "unresolved_after"):
        expected[field] = sorted(PAIRS[p] for p in case.get(field, []))
        assert result[field] == expected[field]
    assert [a["pair"] for a in result["alerts"]] == expected["added"]
    assert all(a["reason"] == "new_possible_cross_domain_flow" for a in result["alerts"])
    # Both versions of these nine fixed programs declare the same imports before any stop.
    modules = ("a", "b") if case["case"] in {"added", "deleted"} else ("api",)
    for version, difference in (("before", "deleted"), ("after", "added")):
        side = result[version]
        assert_metadata(side, modules)
        observed = sorted(tuple(f["pair"]) for f in side["flows"])
        assert observed == sorted(
            expected["retained"] + expected[difference] + expected["unresolved_" + version]
        )
        reason = case.get("reason") if version == "after" else None
        assert [i["reason"] for i in side["issues"]] == ([reason] if reason else [])
        assert side["entry_analysis"] == ("incomplete" if reason else "finished")
    assert result["status"] == ("unknown_or_partial" if "reason" in case else "complete_in_subset")


def test_metadata_changes_between_versions(tmp_path):
    snapshots = []
    for version, code in (
        ("old", "import source as s\ns.read()"),
        ("new", "import source as s, preview as p\np.render(s.read())"),
    ):
        root = tmp_path / version
        root.mkdir()
        (root / "SKILL.md").write_text("synthetic")
        (root / "main.py").write_text(code)
        snapshots.append(analyze(root, "main.py"))
    result = compare(*snapshots)
    assert_metadata(result["before"], ("source",))
    assert_metadata(result["after"], ("source", "preview"))
    assert result["alerts"] == [
        {
            "pair": ("import:source", "import:preview"),
            "reason": "new_possible_cross_domain_flow",
            "evidence_version": "after",
        }
    ]
