import pytest

from dcfa.evidence import build_index
from dcfa.graph import build_graph
from dcfa.policy import evaluate
from dcfa.scs import extract


@pytest.fixture
def case(tmp_path):
    (tmp_path / "SKILL.md").write_text("Synthetic.")
    (tmp_path / "main.py").write_text("dispatch(value)")
    g = build_graph(extract(tmp_path))
    idx = build_index(g, tmp_path)
    i, e = next((i, e) for i, e in enumerate(g["edges"]) if e["relation"] == "operand")
    t = dict(
        source=e["source"],
        effect=e["target"],
        edges=[i],
        reference="fixture event contract",
        private=True,
        external=True,
        sensitivity_retained=True,
        feasible=True,
        bound=True,
    )
    scope = dict(actor="worker", action="send", resource="demo", purpose="preview", invocation="1")
    grant = dict(scope, source=t["source"], allowed=False, reference="synthetic decision")
    c = dict(
        scope,
        policy="confidentiality",
        graph_sha256=idx["graph_sha256"],
        reference="fixture environment",
        coverage_certificate="complete finite event inventory",
        authorizations=[grant],
        prefixes=[t],
    )
    return g, idx, c


@pytest.mark.parametrize(
    "field,value,state",
    [
        ("private", False, "safe"),
        ("external", False, "safe"),
        ("sensitivity_retained", False, "safe"),
        ("feasible", False, "safe"),
        ("feasible", None, "unknown"),
        ("bound", None, "unknown"),
        ("private", True, "violation"),
    ],
)
def test_confidentiality(case, field, value, state):
    case[2]["prefixes"][0][field] = value
    r = evaluate(*case)
    assert r["state"] == state
    assert (r["lower"], r["upper"]) == (state == "violation", state != "safe")
    if r["lower"]:
        assert any(
            w["path"] == "main.py"
            for entry in r["witnesses"][0]["evidence"]
            for w in entry["witnesses"]
        )


def test_permission_scope(case):
    grant = case[2]["authorizations"][0]
    grant["allowed"] = True
    assert evaluate(*case)["state"] == "safe"
    grant["purpose"] = "publish"
    assert evaluate(*case)["state"] == "unknown"


def test_integrity_and_applicability(case):
    c = case[2]
    c["policy"] = "integrity"
    assert evaluate(*case)["state"] == "not_applicable"
    c["action"] = c["authorizations"][0]["action"] = "write"
    c["prefixes"][0].update(untrusted=True, protected=True)
    assert evaluate(*case)["state"] == "violation"
    c["prefixes"][0]["protected"] = False
    assert evaluate(*case)["state"] == "safe"


def test_coverage(case):
    c = case[2]
    c["prefixes"] = []
    assert evaluate(*case)["state"] == "safe"
    del c["coverage_certificate"]
    assert evaluate(*case)["state"] == "unknown"


def test_reject_structural_edge(case):
    g, _, c = case
    i, e = next((i, e) for i, e in enumerate(g["edges"]) if e["relation"] == "contains")
    c["prefixes"][0].update(source=e["source"], effect=e["target"], edges=[i])
    with pytest.raises(ValueError, match="propagation"):
        evaluate(*case)


def test_missing_source_evidence(case):
    _, index, c = case
    node = c["prefixes"][0]["source"]
    index["by_target"]["nodes"][node]["status"] = "unknown"
    result = evaluate(*case)
    assert result["state"] == "unknown"
    assert "traceable" in result["candidates"][0]["unknown"]


def test_nested_program_prefix(tmp_path):
    (tmp_path / "SKILL.md").write_text("Synthetic.")
    (tmp_path / "main.py").write_text("dispatch(transform(value))")
    g = build_graph(extract(tmp_path))
    idx = build_index(g, tmp_path)
    middle, link = next(
        (i, e) for i, e in enumerate(g["edges"]) if e["relation"] == "result_to_operand"
    )
    first, start = next(
        (i, e)
        for i, e in enumerate(g["edges"])
        if e["relation"] == "operand" and e["target"] == link["source"]
    )
    last, end = next(
        (i, e)
        for i, e in enumerate(g["edges"])
        if e["relation"] == "operand" and e["source"] == link["target"]
    )
    scope = dict(actor="a", action="write", resource="r", purpose="p", invocation="c")
    trace = dict(
        source=start["source"],
        effect=end["target"],
        edges=[first, middle, last],
        reference="bound payload through identity transform",
        untrusted=True,
        protected=True,
        bound=True,
        feasible=None,
    )
    contract = dict(
        scope,
        policy="integrity",
        reference="fixture",
        graph_sha256=idx["graph_sha256"],
        authorizations=[dict(scope, source=trace["source"], allowed=False, reference="decision")],
        prefixes=[trace],
    )
    assert evaluate(g, idx, contract)["state"] == "unknown"
    trace["feasible"] = True
    assert evaluate(g, idx, contract)["lower"]
    trace["edges"].remove(middle)
    with pytest.raises(ValueError, match="propagation"):
        evaluate(g, idx, contract)


@pytest.mark.parametrize("empty", [True, False])
def test_control_channel_open(case, empty):
    c = case[2]
    c.update(policy="integrity", action="write")
    c["authorizations"][0]["action"] = "write"
    c["prefixes"][0].update(protected=True, untrusted=False)
    if empty:
        c["prefixes"].clear()
    r = evaluate(*case)
    assert r["state"] == "unknown" and not r["lower"] and r["upper"]
    assert "unrepresented_control_influence" in r["reasons"]


def test_conflicting_resource_classification(case):
    c = case[2]
    c.update(policy="integrity", action="write")
    t = c["prefixes"][0]
    t.update(protected=False, untrusted=False)
    c["prefixes"].append(dict(t, protected=True))
    with pytest.raises(ValueError, match="resource classification"):
        evaluate(*case)


def test_invalid_inapplicable(case):
    c = case[2]
    c["action"] = "write"
    c["prefixes"][0]["edges"] = [-1]
    with pytest.raises(ValueError, match="edge"):
        evaluate(*case)


def test_review_absorption_and_gaps(case):
    c = case[2]
    c["authorizations"].clear()
    c["prefixes"][0].update(private=False, feasible=None)
    result = evaluate(*case)
    assert result["graph_gaps"] and result["state"] == "safe"
    assert result["excluded"][0]["conditions"]["unauthorized"] is None


def test_mixed_evidence_isolation(case):
    from copy import deepcopy

    c = case[2]
    t = c["prefixes"][0]
    c["prefixes"].append(dict(t, bound=None))
    original = deepcopy(case)
    result = evaluate(*case)
    assert result["lower"] and len(result["witnesses"]) == len(result["candidates"]) == 1
    result["witnesses"][0]["evidence"][0]["witnesses"][0].clear()
    result["graph_gaps"].clear()
    assert case == original
    c["authorizations"][0]["source"] = t["effect"]
    assert evaluate(*case)["state"] == "unknown"


def test_completion_oracle(case):
    from itertools import product

    trace = case[2]["prefixes"][0]
    for a, b in product((True, False, None), repeat=2):
        trace.update(private=a, bound=b)
        outcomes = {
            x and y
            for x, y in product((False, True), repeat=2)
            if (a is None or x == a) and (b is None or y == b)
        }
        r = evaluate(*case)
        assert (r["lower"], r["upper"]) == (all(outcomes), any(outcomes))
