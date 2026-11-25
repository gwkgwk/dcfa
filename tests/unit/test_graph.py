import json
from copy import deepcopy

import pytest

from dcfa.cli import main
from dcfa.graph import build_graph, graph_dot, graph_json, validate_graph
from dcfa.scs import extract


def relations(graph, kind):
    return [edge for edge in graph["edges"] if edge["relation"] == kind]


def sample(root, body, script=None):
    (root / "SKILL.md").write_text(body, encoding="utf-8")
    if script:
        (root / "sample.py").write_text(script, encoding="utf-8")
    return extract(root)


def test_instruction_roles(tmp_path):
    data = sample(tmp_path, "Accept text.\nWrite URL from workspace to external.")
    graph = build_graph(data)
    for kind in ("reads", "produces", "exposes", "crosses-boundary", "may_cause"):
        (edge,) = relations(graph, kind)
        assert edge["certainty"] == "possible"
        assert len(edge["evidence"]) == 2
    assert graph["runtime_observation"] == "none"
    assert json.loads(graph_json(graph)) == graph


def test_same_type_no_flow(tmp_path):
    data = sample(tmp_path, "---\ninput: Text\noutput: Text\neffect: send\n---\nAccept text.")
    graph = build_graph(data)
    assert not relations(graph, "may_cause")
    assert not relations(graph, "produces")
    assert relations(graph, "reads")[0]["source"] == "/scs/ports/2"
    assert any(g["reason"] == "semantic_link_unresolved" for g in graph["unknowns"])


def test_different_line_and_conflicting_roles(tmp_path):
    data = sample(tmp_path, "Return text.")
    data["ports"][0]["evidence"]["start_line"] = 2
    data["ports"][0]["evidence"]["end_line"] = 2
    assert not relations(build_graph(data), "produces")
    data["ports"][0]["evidence"] = deepcopy(data["operations"][0]["evidence"])
    data["ports"][0]["data_type"] = "Command"
    assert not relations(build_graph(data), "produces")
    data["ports"][0]["data_type"] = "Text"
    data["operations"] *= 2
    assert not relations(build_graph(data), "produces")


def test_call_binding_and_operands(tmp_path):
    data = sample(tmp_path, "# Demo", "adapter.process(item, mode='trim')")
    graph = build_graph(data)
    operands = relations(graph, "operand")
    assert len(operands) == 3
    assert all(e["certainty"] == "static" for e in operands)
    assert not relations(graph, "may_invoke")
    b = {
        "operation": 0,
        "callee": "adapter.process",
        "tool": "mock",
        "basis": "synthetic interface",
    }
    bound = build_graph(data, [b])
    assert relations(bound, "may_invoke")[0]["certainty"] == "possible"
    with pytest.raises(ValueError):
        build_graph(data, [b | {"callee": "other"}])
    with pytest.raises(ValueError):
        build_graph(data, [b, b])


def test_resource_is_not_read_and_input_preserved(scs_demo):
    data = extract(scs_demo)
    graph = build_graph(data)
    assert graph["scs"] == data
    assert any(n["kind"] == "resource" for n in graph["nodes"])
    assert all(e["source"] != "/scs/files/2" for e in relations(graph, "reads"))
    assert any(g["reason"] == "resource_usage_unresolved" for g in graph["unknowns"])
    assert build_graph(data) == graph


@pytest.mark.parametrize("change", ["target", "certainty", "evidence", "missing", "runtime"])
def test_validator_rejects_tampering(tmp_path, change):
    graph = build_graph(sample(tmp_path, "Return URL."))
    if change == "runtime":
        graph["runtime_observation"] = "confirmed"
    elif change == "missing":
        graph["edges"].pop()
    else:
        graph["edges"][-1][change] = "fabricated"
    with pytest.raises(ValueError):
        validate_graph(graph)


def test_cli_export(tmp_path, capsys):
    data = sample(tmp_path, "Accept text.")
    path = tmp_path / "scs.json"
    path.write_text(json.dumps(data))
    assert main(["graph", str(path)]) == 0
    graph = json.loads(capsys.readouterr().out)
    assert main(["graph", str(path), "--format", "dot"]) == 0
    assert capsys.readouterr().out.strip() == graph_dot(graph)
    assert "style=dashed" in graph_dot(graph)
    path.write_text("{}")
    assert main(["graph", str(path)]) == 1


def test_failed_snapshot(tmp_path):
    graph = build_graph(extract(tmp_path))
    assert graph["scs"]["status"] == "failed"
    assert graph["unknowns"]
    assert not graph["edges"]


def test_nested_call_result_requires_ast_parent(tmp_path):
    data = sample(tmp_path, "Read text.", "consume(item=make())\nmake()\nconsume(item)")
    graph = build_graph(data)
    (edge,) = relations(graph, "result_to_operand")
    assert (edge["source"], edge["target"]) == ("/scs/operations/2", "/scs/operations/1/arg0")
    assert edge["certainty"] == "possible"
    data["operations"][2]["name"] = "unmatched"
    graph = build_graph(data)
    assert not relations(graph, "result_to_operand")
    assert any(g["reason"] == "local_value_flow_unresolved" for g in graph["unknowns"])


def test_delivered_exports_rebuild(scs_demo):
    from pathlib import Path

    examples = Path(__file__).resolve().parents[2] / "examples"
    graph = build_graph(extract(scs_demo))
    assert graph == json.loads((examples / "graph.json").read_text(encoding="utf-8"))
    assert graph_dot(graph) == (examples / "graph.dot").read_text(encoding="utf-8").rstrip("\n")
