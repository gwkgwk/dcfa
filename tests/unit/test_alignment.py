"""Independent oracles for the P11 finite-contract fragment, using real P03-P05 inputs."""

from copy import deepcopy

import pytest

from dcfa.alignment import align
from dcfa.evidence import build_index
from dcfa.graph import build_graph
from dcfa.scs import extract

ROLE = ["worker", "display", "in:text", "preview", "show"]
ROWS = [["normal", "sample", "shown", "private/inside/authorized"]]


def snapshot(root, script, *, document="synthetic", filename="main.py"):
    root.mkdir()
    (root / "SKILL.md").write_text(document)
    (root / filename).write_text(script)
    graph = build_graph(extract(root))
    index = build_index(graph, root)
    units = [
        dict(
            members=[n["id"]],
            role=ROLE.copy(),
            observations=deepcopy(ROWS),
            certificate="synthetic finite display contract",
        )
        for n in graph["nodes"]
        if n["kind"] in {"instruction_action", "effect", "call_expression"}
    ]
    contract = dict(
        graph_sha256=index["graph_sha256"],
        skill="demo",
        version=root.name,
        environment="E1",
        scope="display units",
        coverage_certificate="fixture inventory",
        units=units,
    )
    return dict(graph=graph, index=index, contract=contract)


def units(s):
    return s["contract"]["units"]


def test_renamed_moved_and_rephrased(tmp_path):
    a = snapshot(tmp_path / "old", "render(x)", filename="left.py")
    b = snapshot(tmp_path / "new", "display(y)", filename="right.py")
    for s in (a, b):
        s["contract"]["unique_persistent_roles"] = [ROLE]
    r = align(a, b)
    assert len(r["preserved"]) == 1
    assert r["aligned"][0]["identity_basis"] == "unique_persistent_role"
    assert "right.py" in str(r["evidence"]["after"])
    c = snapshot(tmp_path / "text", "", document="Accept text.")
    d = snapshot(tmp_path / "rewrite", "", document="Read text.")
    for s in (c, d):
        assert len(units(s)) == 1
        units(s)[0]["anchor"] = "request-input"
    assert len(align(c, d)["preserved"]) == 1


@pytest.mark.parametrize("column,security", [(2, "equal"), (3, "different")])
def test_semantic_projections(tmp_path, column, security):
    a = snapshot(tmp_path / "old", "display(x)")
    b = deepcopy(a)
    for s in (a, b):
        units(s)[0]["anchor"] = "interface"
    units(b)[0]["observations"][0][column] = "changed"
    r = align(a, b)
    assert len(r["modified"]) == 1
    assert r["aligned"][0]["security"]["state"] == security


def test_ambiguous_and_unbound(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)\ng(x)")
    b = snapshot(tmp_path / "new", "h(y)\ni(y)")
    r = align(a, b)
    assert not r["aligned"] and len(r["unresolved"]) == 4
    units(b).reverse()
    assert align(a, b) == r
    b["contract"]["units"] = []
    assert not align(a, b)["aligned"]


def test_split_merge(tmp_path):
    a = snapshot(tmp_path / "old", "combined(x)")
    b = snapshot(tmp_path / "new", "first(x)\nsecond(x)")
    units(a)[0]["anchor"] = "pipeline"
    first, second = units(b)
    first.update(
        anchor="pipeline",
        members=first["members"] + second["members"],
        aggregation_certificate="ordered composition under E1",
    )
    units(b).pop()
    assert len(align(a, b)["aligned"][0]["after"]) == 2
    assert len(align(b, a)["aligned"][0]["before"]) == 2
    del first["aggregation_certificate"]
    with pytest.raises(ValueError, match="aggregation"):
        align(a, b)


def test_unmatched_and_coverage(tmp_path):
    a = snapshot(tmp_path / "old", "")
    b = snapshot(tmp_path / "new", "f(x)")
    assert len(align(a, b)["added"]) == len(align(b, a)["deleted"]) == 1
    del a["contract"]["coverage_certificate"]
    assert not align(a, b)["added"]
    assert align(a, b)["unresolved"]


def test_conflict_and_missing_observation(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    b = deepcopy(a)
    for s in (a, b):
        units(s)[0]["anchor"] = "stable"
    del units(b)[0]["observations"]
    (pair,) = align(a, b)["aligned"]
    assert pair["full"]["state"] == pair["security"]["state"] == "unknown"
    units(b)[0]["role"][0] = "other actor"
    with pytest.raises(ValueError, match="contradicts"):
        align(a, b)


def test_directional_slot_disambiguates_under_persistent_role(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)\ng(y)")
    b = snapshot(tmp_path / "new", "renamed(y)\nother(x)")
    for s, bindings in ((a, ["first-input", "second-input"]), (b, ["second-input", "first-input"])):
        s["contract"]["unique_persistent_roles"] = [ROLE]
        for unit, binding in zip(units(s), bindings, strict=True):
            edge = next(
                i
                for i, e in enumerate(s["graph"]["edges"])
                if e["relation"] == "operand" and e["target"] in unit["members"]
            )
            unit["slots"] = [dict(edge=edge, slot="argument", neighbor_binding=binding)]
    assert [(p["before"][0], p["after"][0]) for p in align(a, b)["aligned"]] == [
        (units(a)[0]["members"][0], units(b)[1]["members"][0]),
        (units(a)[1]["members"][0], units(b)[0]["members"][0]),
    ]
    for s in (a, b):
        for u in units(s):
            del u["slots"]
    assert not align(a, b)["aligned"]


def test_evidence_isolation(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    edge = next(i for i, e in enumerate(a["graph"]["edges"]) if e["relation"] == "operand")
    units(a)[0]["slots"] = [dict(edge=edge, slot="arg", neighbor_binding="input")]
    original = deepcopy(a)
    r = align(a, a)
    old, new = (r["evidence"][side]["units"][0] for side in ("before", "after"))
    expected = deepcopy(new)
    old["role"][0] = "changed"
    old["slot_evidence"].clear()
    old["evidence"][0]["witnesses"][0].clear()
    assert a == original
    assert new == expected
    units(a)[0]["role"][0] = "input mutation"
    assert new == expected
    assert align(original, original)["evidence"]["before"]["units"][0] == expected


def test_endpoint_contract(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    i, edge = next((i, e) for i, e in enumerate(a["graph"]["edges"]) if e["relation"] == "operand")
    a["contract"]["neighbor_bindings"] = {edge["source"]: "input"}
    units(a)[0]["slots"] = [dict(edge=i, slot="arg", neighbor_binding="input")]
    b = deepcopy(a)
    align(a, b)
    units(b)[0]["slots"][0]["neighbor_binding"] = "other"
    with pytest.raises(ValueError, match="neighbor"):
        align(a, b)
    del b["contract"]["neighbor_bindings"]
    with pytest.raises(ValueError, match="neighbor"):
        align(a, b)


def test_single_candidate_requires_persistence(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    r = align(a, a)
    assert not r["aligned"] and len(r["unresolved"]) == 2


def test_unbound_competitor(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    b = snapshot(tmp_path / "new", "f(x)\ng(y)")
    units(b).pop()
    for s in (a, b):
        s["contract"]["unique_persistent_roles"] = [ROLE]
    r = align(a, b)
    assert not r["aligned"] and len(r["unresolved"]) == 3


def test_input_change_only(tmp_path):
    a = snapshot(tmp_path / "old", "f(x)")
    units(a)[0]["anchor"] = "stable"
    b = deepcopy(a)
    units(b)[0]["observations"][0][1] = "other input"
    (pair,) = align(a, b)["aligned"]
    assert pair["full"]["state"] == "different"
    assert pair["security"]["state"] == "equal"


def test_two_unit_reference(tmp_path):
    from itertools import permutations, product

    a = snapshot(tmp_path / "old", "f(x)\ng(y)")
    b = snapshot(tmp_path / "new", "h(z)\ni(w)")
    for s in (a, b):
        s["contract"]["unique_persistent_roles"] = [ROLE]
    for labels in product(("p", "q"), repeat=4):
        for s, values in ((a, labels[:2]), (b, labels[2:])):
            for unit, value in zip(units(s), values, strict=True):
                unit["role"][0] = value
            s["contract"]["unique_persistent_roles"] = [[v, *ROLE[1:]] for v in ("p", "q")]
        mappings = [
            order
            for order in permutations(range(2))
            if all(labels[i] == labels[2 + j] for i, j in enumerate(order))
        ]
        if not mappings:
            continue
        expected = {
            (units(a)[i]["members"][0], units(b)[j]["members"][0])
            for i, j in enumerate(mappings[0])
            if all(m[i] == j for m in mappings)
        }
        actual = align(a, b)
        assert {(p["before"][0], p["after"][0]) for p in actual["aligned"]} == expected
