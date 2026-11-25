import hashlib
import json
import os
from copy import deepcopy

import pytest

from dcfa.cli import main
from dcfa.evidence import build_index
from dcfa.graph import build_graph
from dcfa.scs import extract


def snapshot(root, doc="Accept text.", script=None):
    (root / "SKILL.md").write_text(doc, encoding="utf-8")
    if script:
        (root / "code.py").write_text(script, encoding="utf-8")
    return build_graph(extract(root))


def witness(index, pointer):
    return index["origins"][pointer]["witness"]


def test_original_bytes_and_bidirectional(scs_demo):
    graph = build_graph(extract(scs_demo))
    index = build_index(graph, scs_demo)
    assert index["mapping_status"] == "verified" and index["scs_status"] == "partial"
    assert len(index["by_target"]["edges"]) == len(graph["edges"])
    for key, f in index["by_file"].items():
        assert key.startswith("skill/")
        path = scs_demo / key.removeprefix("skill/")
        assert f["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        for cap in f["capabilities"]:
            for kind in ("nodes", "edges"):
                for target in index["by_capability"][cap][kind]:
                    assert target in f[kind]
                    assert cap in index["by_target"][kind][target]["origins"]


def test_line_reorder_requires_fresh_snapshot(tmp_path):
    graph = snapshot(tmp_path, "Accept text.\nReturn URL.")
    (tmp_path / "SKILL.md").write_text("Return URL.\nAccept text.")
    stale = build_index(graph, tmp_path)
    assert stale["mapping_status"] == "incomplete"
    assert witness(stale, "/scs/ports/0") is None
    fresh = build_index(build_graph(extract(tmp_path)), tmp_path)
    assert witness(fresh, "/scs/ports/0")["snippet"] == "Return URL."


def test_reordered_file_inventory_and_duplicate_lines(tmp_path):
    graph = snapshot(tmp_path, "Accept text.\nAccept text.", "f()")
    data = deepcopy(graph["scs"])
    data["files"].reverse()
    index = build_index(build_graph(data), tmp_path)
    assert witness(index, "/scs/files/0")["path"] == data["files"][0]["path"]
    assert [witness(index, f"/scs/ports/{i}")["start_line"] for i in range(2)] == [1, 2]


def test_duplicate_ast_and_raw_bom_hash(tmp_path):
    graph = snapshot(tmp_path)
    source = "é(); é()\r\n".encode("utf-8-sig")
    (tmp_path / "code.py").write_bytes(source)
    graph = build_graph(extract(tmp_path))
    index = build_index(graph, tmp_path)
    a, b = [witness(index, f"/scs/operations/{i}") for i in (1, 2)]
    assert a["ast"]["start_utf8_column"] == 0
    assert b["ast"]["start_utf8_column"] == 6
    assert b["ast"]["source"] == "é()" and b["ast"]["end_utf8_column"] == 10
    assert a["sha256"] == hashlib.sha256(source).hexdigest()
    data = graph["scs"]
    data["operations"].pop()
    assert witness(build_index(build_graph(data), tmp_path), "/scs/operations/1") is None


def test_tool_multi_origin_and_missing(tmp_path):
    snapshot(tmp_path, script="tool.run(x)")
    summary = extract(tmp_path)
    b = [{"operation": 1, "callee": "tool.run", "tool": "模拟器", "basis": "mock contract"}]
    graph = build_graph(summary, b)
    declaration = tmp_path.parent / (tmp_path.name + "-binding.json")
    raw = json.dumps(b, indent=2, ensure_ascii=False)
    declaration.write_bytes(raw.encode("utf-8-sig"))
    idx = build_index(graph, tmp_path, declaration)
    record = witness(idx, "/bindings/0")
    assert json.loads(raw[record["start_char"] : record["end_char"]]) == b[0]
    assert record["sha256"] == hashlib.sha256(declaration.read_bytes()).hexdigest()
    e = next(i for i, v in enumerate(graph["edges"]) if v["relation"] == "may_invoke")
    key = f"/edges/{e}"
    for f in ("skill/code.py", "analyst/" + declaration.name):
        assert key in idx["by_file"][f]["edges"]
    assert idx["by_target"]["edges"][key]["uncertainty"] == "possible"
    declaration.write_text("[]")
    for path in (None, declaration):
        target = build_index(graph, tmp_path, path)["by_target"]["edges"][key]
        assert target["status"] == "partial"


def test_forged_claim_and_missing_file(tmp_path):
    graph = snapshot(tmp_path, script="real()")
    data = graph["scs"]
    data["operations"][-1]["name"] = "invented"
    assert witness(build_index(build_graph(data), tmp_path), "/scs/operations/1") is None
    data["ports"][0]["evidence"]["end_line"] = 800
    idx = build_index(build_graph(data), tmp_path)
    assert witness(idx, "/scs/ports/0") is None
    (tmp_path / "code.py").rename(tmp_path / "moved.py")
    idx = build_index(build_graph(data), tmp_path)
    assert "skill/code.py" not in idx["by_file"]
    assert idx["mapping_status"] == "incomplete"


def test_hardlink_never_hashed(tmp_path):
    root = tmp_path / "snap"
    root.mkdir()
    graph = snapshot(root, script="local()")
    (root / "code.py").unlink()
    outside = tmp_path / "other"
    outside.write_text("local()")
    os.link(outside, root / "code.py")
    index = build_index(graph, root)
    assert "skill/code.py" not in index["by_file"]
    assert any(d["reason"] == "unsafe_entry" for d in index["scan_diagnostics"])


def test_cli(tmp_path, capsys):
    root = tmp_path / "snap"
    root.mkdir()
    graph = snapshot(root)
    artifact = tmp_path / "graph.json"
    artifact.write_text(json.dumps(graph))
    assert main(["evidence", str(artifact), str(root)]) == 0
    assert json.loads(capsys.readouterr().out) == build_index(graph, root)
    (root / "SKILL.md").write_text("")
    assert main(["evidence", str(artifact), str(root)]) == 1
    graph["edges"].pop()
    artifact.write_text(json.dumps(graph))
    assert main(["evidence", str(artifact), str(root)]) == 2


def test_fake_path_never_followed(tmp_path):
    graph = snapshot(tmp_path)
    data = graph["scs"]
    data["files"][0]["path"] = "../other/SKILL.md"
    for group in ("ports", "operations"):
        data[group][0]["evidence"]["path"] = "../other/SKILL.md"
    index = build_index(build_graph(data), tmp_path)
    assert index["mapping_status"] == "incomplete"
    assert not witness(index, "/scs/ports/0")
    assert "skill/../other/SKILL.md" not in index["by_file"]


def test_identical_line_in_changed_context(tmp_path):
    graph = snapshot(tmp_path, "# Example\nAccept text.")
    (tmp_path / "SKILL.md").write_text("~~~\nAccept text.\n~~~")
    assert witness(build_index(graph, tmp_path), "/scs/ports/0") is None


def test_malformed_binding_file(tmp_path):
    graph = snapshot(tmp_path)
    declaration = tmp_path / "declaration.json"
    declaration.write_text("invalid")
    with pytest.raises(ValueError):
        build_index(graph, tmp_path, declaration)


def test_delivered_index(scs_demo):
    from pathlib import Path

    examples = Path(__file__).resolve().parents[2] / "examples"
    graph = json.loads((examples / "graph.json").read_text(encoding="utf-8"))
    expected = json.loads((examples / "evidence.json").read_text(encoding="utf-8"))
    assert build_index(graph, scs_demo) == expected
    assert all(
        edge["basis"] in expected["edge_rules"] for edge in expected["by_target"]["edges"].values()
    )
