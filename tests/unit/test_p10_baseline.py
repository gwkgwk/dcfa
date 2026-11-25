"""Run the preregistered synthetic updates through the public baseline interfaces."""

import json
from pathlib import Path

import pytest

from dcfa.program_flow import analyze
from dcfa.trust_diff import compare

ORACLE = Path(__file__).resolve().parents[1] / "fixtures/synthetic/p10-oracle.json"
PAIRS = {"L": (":local", "import:api"), "AB": ("import:a", "import:b")}


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
    for version, difference in (("before", "deleted"), ("after", "added")):
        side = result[version]
        observed = sorted(tuple(f["pair"]) for f in side["flows"])
        assert observed == sorted(
            expected["retained"] + expected[difference] + expected["unresolved_" + version]
        )
        reason = case.get("reason") if version == "after" else None
        assert [i["reason"] for i in side["issues"]] == ([reason] if reason else [])
        assert side["entry_analysis"] == ("incomplete" if reason else "finished")
    assert result["status"] == ("unknown_or_partial" if "reason" in case else "complete_in_subset")
