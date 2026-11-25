import copy
import json
import subprocess
import sys

import pytest

from dcfa.program_flow import analyze
from dcfa.trust_diff import compare


def snapshot(root, program):
    (root / "SKILL.md").write_text("synthetic")
    (root / "main.py").write_text(program)
    return analyze(root, "main.py")


def test_domain_delta_and_witnesses(tmp_path):
    old = snapshot(tmp_path, "import first\nfirst.emit('a')")
    new = snapshot(tmp_path, "import first, second\nx=first.read('a')\nsecond.emit(x)")
    r = compare(old, new)
    assert r["added"] == [(":local", "import:second"), ("import:first", "import:second")]
    assert r["retained"] == [(":local", "import:first")]
    assert r["deleted"] == []
    assert [a["pair"] for a in r["alerts"]] == r["added"]
    for f in r["after"]["flows"]:
        for label, kind in zip(f["pair"], ("data_flow", "owns"), strict=True):
            path = f[kind]
            node = path["root"]
            assert node in r["after"]["roots"][label]
            for index in path["edges"]:
                e = new["edges"][index]
                assert (e["kind"], e["source"], e["file"]) == (kind, node, "main.py")
                node = e["target"]
            assert node == f["common_object"]
    reverse = compare(new, old)
    assert reverse["deleted"] == r["added"] and reverse["alerts"] == []


def test_alias_id_change_duplicate_and_independence(tmp_path):
    old = snapshot(tmp_path, "import api\napi.emit('v')")
    new = snapshot(tmp_path, "a='ignored'\nfrom api import emit as e\ne('x')\ne('x')")
    r = compare(old, new)
    assert r["retained"] == [(":local", "import:api")]
    assert not r["added"] and not r["deleted"]
    isolated = snapshot(tmp_path, "import a,b\na.read()\nb.read()")
    assert compare(isolated, isolated)["after"]["flows"] == []


def test_unknown_reference_cycle_and_partial(tmp_path):
    old = snapshot(tmp_path, "if True: pass")
    new = snapshot(tmp_path, "open('synthetic')")
    r = compare(old, new)
    assert r["unresolved_after"] == [(":local", "builtin:file")] and not r["alerts"]
    malformed = copy.deepcopy(new)
    malformed["edges"][0]["target"] = 777
    assert compare(malformed, new)["before"]["status"] == "invalid"
    new["edges"].append(new["edges"][0] | {"source": new["edges"][0]["target"]})
    assert compare(new, new)["retained"] == [(":local", "builtin:file")]
    assert not compare(new, new | {"entry": "other.py"})["retained"]


@pytest.mark.parametrize("contents", [None, "{", "{}"])
def test_cli_failed_input(tmp_path, contents):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(snapshot(tmp_path, "open('x')")))
    bad = tmp_path / "bad.json"
    if contents is not None:
        bad.write_text(contents)
    p = subprocess.run(
        [sys.executable, "-m", "dcfa.trust_diff", str(bad), str(good)],
        capture_output=True,
        text=True,
    )
    result = json.loads(p.stdout)
    assert p.returncode == 1 and result["before"]["issues"] and result["after"]["flows"]
    assert not result["alerts"]
