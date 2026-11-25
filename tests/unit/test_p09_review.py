import json
import subprocess
import sys
from copy import deepcopy
from itertools import permutations

import pytest

from dcfa.program_flow import analyze
from dcfa.trust_diff import compare, extract


def snapshot(root, program):
    (root / "SKILL.md").write_text("synthetic")
    (root / "main.py").write_text(program)
    return analyze(root, "main.py")


@pytest.mark.parametrize("field", ["nodes", "edges", "issues", "unvisited_functions"])
def test_owned_evidence(tmp_path, field):
    raw = snapshot(tmp_path, "def spare(): pass\nopen('x')\nif True: pass")
    result = compare(raw, raw)
    original = deepcopy(result)
    raw[field][0]["line"] = 999
    assert result == original
    result["before"][field].clear()
    assert result["after"] == original["after"]
    assert raw[field]


def reachable(root, edges, kind):
    reached = {root}
    while True:
        more = {e["target"] for e in edges if e["kind"] == kind and e["source"] in reached}
        if more <= reached:
            return reached
        reached |= more


def test_cycles_permutations_and_witnesses(tmp_path):
    raw = snapshot(tmp_path, "import a,b\na.send(b.read())")
    module = {n["name"]: n["id"] for n in raw["nodes"] if n["kind"] == "module"}
    edges = raw["edges"]
    # Reverse a real non-self edge to close a two-object directed cycle.
    for kind in ("owns", "data_flow"):
        e = next(e for e in edges if e["kind"] == kind and e["source"] == module["a"])
        edges.append(e | {"source": e["target"], "target": e["source"]})
    expected = {
        ("import:" + a, "import:" + b)
        for a, b in permutations(module, 2)
        if reachable(module[a], edges, "data_flow") & reachable(module[b], edges, "owns")
    }
    assert expected == {("import:b", "import:a")}
    for node_order in (raw["nodes"], raw["nodes"][::-1]):
        for edge_order in (edges, edges[::-1]):
            side = extract(raw | {"nodes": node_order, "edges": edge_order})
            assert {tuple(f["pair"]) for f in side["flows"]} == expected
            for f in side["flows"]:
                for domain, kind in zip(f["pair"], ("data_flow", "owns"), strict=True):
                    path = f[kind]
                    current = path["root"]
                    assert current in side["roots"][domain]
                    for index in path["edges"]:
                        e = edge_order[index]
                        assert (e["source"], e["kind"]) == (current, kind)
                        current = e["target"]
                    assert current == f["common_object"]


def test_nonroot_labels_and_domain_granularity(tmp_path):
    old = snapshot(tmp_path, "import a\na.read('first')")
    new = snapshot(tmp_path, "import a,unused\na.other('second')")
    for n in new["nodes"]:
        if n["kind"] == "result":
            n["domain"] = "import:invented"
    r = compare(old, new)
    assert set(r["after"]["roots"]) == {":local", "import:a", "import:unused"}
    assert r["added"] == r["deleted"] == []
    assert "import:unused" in r["after"]["import_assumptions"]


@pytest.mark.parametrize("tail,code", [("", 0), ("\nif True: pass", 1)])
def test_cli_positive_witness_and_completion(tmp_path, tail, code):
    (tmp_path / "helper.py").write_text("def deliver(x):\n import api\n api.send(x)")
    old = snapshot(tmp_path, "open('old')")
    new = snapshot(tmp_path, "from helper import deliver\ndeliver('new')" + tail)
    files = [tmp_path / name for name in ("before.json", "after.json")]
    for path, side in zip(files, [old, new], strict=True):
        path.write_text(json.dumps(side))
    proc = subprocess.run(
        [sys.executable, "-m", "dcfa.trust_diff", *files], capture_output=True, text=True
    )
    r = json.loads(proc.stdout)
    assert proc.returncode == code
    assert [a["pair"] for a in r["alerts"]] == [[":local", "import:api"]]
    assert r["unresolved_before"] == ([[":local", "builtin:file"]] if code else [])
    (f,) = r["after"]["flows"]
    last = new["edges"][f["data_flow"]["edges"][-1]]
    assert (last["file"], last["line"]) == ("helper.py", 3)
