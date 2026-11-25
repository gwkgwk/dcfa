"""Compare the public phase-one interfaces with preregistered semantic projections."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from dcfa.evidence import build_index
from dcfa.graph import build_graph
from dcfa.scs import extract

ORACLE = Path(__file__).resolve().parents[1] / "fixtures/synthetic/p06-oracle.json"
CASES = json.loads(ORACLE.read_text(encoding="utf-8"))


def observe(case, files, root):
    root.mkdir()
    for name, content in files.items():
        (root / name).write_text(content, encoding="utf-8")
    summary = extract(root)
    graph = build_graph(summary, case.get("bindings"))
    labels = {n["id"]: n["kind"] + ":" + n["label"] for n in graph["nodes"]}
    facts = ["port:" + p["direction"] + ":" + p["data_type"] for p in summary["ports"]]
    facts += ["effect:" + e["name"] for e in summary["effects"]]
    facts += [o["kind"] + ":" + o["name"] for o in summary["operations"]]
    facts += ["context:" + c["scope"] for c in summary["context_exposure"]]
    facts += [
        "boundary:" + b["source"] + "→" + b["destination"] for b in summary["trust_boundaries"]
    ]
    edges = [
        "|".join([labels[e["source"]], e["relation"], labels[e["target"]], e["certainty"]])
        for e in graph["edges"]
        if e["relation"] != "contains"
    ]
    capability_nodes = [
        labels[n["id"]]
        for n in graph["nodes"]
        if n["kind"]
        in {
            "input_port",
            "output_port",
            "effect",
            "instruction_action",
            "call_expression",
            "context",
            "trust_boundary",
        }
    ]
    actual = {
        "scs": sorted(facts),
        "edges": sorted(edges),
        "capability_nodes": sorted(capability_nodes),
        "runtime": graph["runtime_observation"],
    }
    if "authorization" in case:
        actual["authorization"] = summary["effects"][0]["requires_authorization"]
    if "unrepresented" in case:
        actual["all_node_kinds"] = sorted({n["kind"] for n in graph["nodes"]})
    if "arguments" in case:
        actual["arguments"] = [o["parameters"] for o in summary["operations"]]
    if "unknown" in case:
        actual["unknown"] = sorted({u["reason"] for u in graph["unknowns"]})
    if "sourceFiles" in case:
        declaration = root.parent / "bindings.json"
        declaration.write_text(json.dumps(case["bindings"]), encoding="utf-8")
        index = build_index(graph, root, declaration)
        (slot,) = [i for i, e in enumerate(graph["edges"]) if e["relation"] == "may_invoke"]
        ref = f"/edges/{slot}"
        actual["sourceFiles"] = sorted(k for k, v in index["by_file"].items() if ref in v["edges"])
        actual["mapping"] = index["by_target"]["edges"][ref]["status"]
    return actual


def check(case, actual):
    expected = case["expected"]
    assert actual["scs"] == sorted(expected["scs"])
    assert actual["edges"] == sorted(expected["edges"])
    nodes = [
        v.replace("port:input:", "input_port:")
        .replace("port:output:", "output_port:")
        .replace("boundary:", "trust_boundary:")
        .replace("→", " → ")
        for v in expected["scs"]
    ]
    assert actual["capability_nodes"] == sorted(nodes)
    assert actual["runtime"] == "none"
    if "unrepresented" in case:
        kinds = {"skill", "file", "call_expression"}
        if any("|operand|" in e for e in expected["edges"]):
            kinds.add("data_expression")
        assert actual["all_node_kinds"] == sorted(kinds)
    for key in ("arguments", "authorization", "sourceFiles"):
        if key in case:
            assert actual[key] == (sorted(case[key]) if key == "sourceFiles" else case[key])
    if "unknown" in case:
        assert case["unknown"] in actual["unknown"]
    if "sourceFiles" in case:
        assert actual["mapping"] == "verified"


def verify(case, workdir):
    outputs = []
    for name in ("files", "variant"):
        if name in case:
            observed = observe(case, case[name], workdir / name)
            check(case, observed)
            outputs.append(observed)
    if len(outputs) == 2:
        assert outputs[0] == outputs[1]
    return outputs


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_semantic_property(case, tmp_path):
    verify(case, tmp_path)


if __name__ == "__main__":
    results = {}
    for case in CASES:
        with TemporaryDirectory() as workdir:
            results[case["id"]] = verify(case, Path(workdir))
    print(json.dumps(results, indent=2))
