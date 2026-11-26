import json

import pytest

from dcfa.evidence import digest
from dcfa.graph import build_graph, canonical
from dcfa.scs import extract
from dcfa.update import analyze_update, snapshot_digest

DOMAIN = [["preview", "a"], ["preview", "b"]]
INSTRUCTION = "Send text from workspace to external."


def scenario(root, versions):
    """Generate only trusted bindings and input facts, never expected labels from a detector."""
    cfg = dict(configuration="P16.synthetic.v1", queries=[])
    queries = {}
    for name, (document, script, authorization) in zip(("before", "after"), versions, strict=True):
        folder = root / name
        folder.mkdir()
        (folder / "SKILL.md").write_bytes(document.encode())
        if script is not None:
            (folder / "main.py").write_bytes(script.encode())
        graph = build_graph(extract(folder))
        sha = digest(canonical(graph).encode())
        units = []
        cfg[name] = dict(
            contract=dict(
                graph_sha256=sha,
                skill="synthetic",
                version=name,
                environment="fixed",
                scope="finite events",
                units=units,
                coverage_certificate="inventory",
            )
        )
        for i, e in enumerate(graph["edges"]):
            if e["relation"] not in {"may_cause", "operand"}:
                continue
            channel = e["relation"]
            members = [e["target"]]
            units.append(
                dict(
                    members=members,
                    anchor=channel,
                    certificate="fixed interface",
                    role=["worker", "send", "text", channel, "publish"],
                )
            )
            q = queries.setdefault(
                channel,
                dict(
                    id=channel, key=["confidentiality", "worker", channel, "send"], contexts=DOMAIN
                ),
            )
            contracts = []
            q[name] = dict(members=members, contracts=contracts)
            for (purpose, invocation), allowed in zip(DOMAIN, authorization, strict=True):
                scope = dict(
                    actor="worker",
                    resource=channel,
                    action="send",
                    purpose=purpose,
                    invocation=invocation,
                )
                trace = dict(
                    reference="fixture payload binding",
                    source=e["source"],
                    effect=e["target"],
                    edges=[i],
                    bound=True,
                    feasible=True,
                    private=True,
                    external=True,
                    sensitivity_retained=True,
                )
                grants = (
                    []
                    if allowed is None
                    else [
                        dict(
                            scope, source=e["source"], allowed=allowed, reference="fixture decision"
                        )
                    ]
                )
                contracts.append(
                    dict(
                        scope,
                        policy="confidentiality",
                        graph_sha256=sha,
                        reference="fixture environment",
                        coverage_certificate="finite domain",
                        prefixes=[trace],
                        authorizations=grants,
                    )
                )
    cfg["queries"] = list(queries.values())
    return cfg


def run(root, cfg):
    return analyze_update(root / "before", root / "after", cfg)


def test_snapshot_digest():
    assert snapshot_digest({"b": b"1", "a": b"2"}) == snapshot_digest({"a": b"2", "b": b"1"})
    assert snapshot_digest({"a": b"1"}) != snapshot_digest({"b": b"1"})


@pytest.mark.parametrize("mode", ["instruction", "program", "mixed"])
def test_modalities_and_direction(tmp_path, mode):
    doc = INSTRUCTION if mode != "program" else "Synthetic."
    old, new = (None, None) if mode == "instruction" else ("send(1)", "send(2)")
    cfg = scenario(
        tmp_path,
        [
            (doc, old, [False, True]),
            (doc.upper() if mode != "program" else doc, new, [False, False]),
        ],
    )
    r = run(tmp_path, cfg)
    assert r["status"] == "completed"
    expected = {
        "instruction": {"may_cause"},
        "program": {"operand"},
        "mixed": {"may_cause", "operand"},
    }[mode]
    assert {row["id"] for row in r["results"]} == expected
    for row in r["results"]:
        a = row["analysis"]
        assert a["change"]["overall"] == "aggravated"
        x, y = a["change"]["regions"]
        assert x["regions"]["persistent"]["lower"] and y["regions"]["added"]["lower"]
        if row["id"] == "operand":
            (dep,) = a["associations"][0]["semantic_dependencies"]
            assert dep["before"]["value"] != dep["after"]["value"]
            hits = a["associations"][0]["paths"][1]["locations"]
            assert hits[0]["edits"][0]["matched_lines"] == [1, 1]
    cfg["before"], cfg["after"] = cfg["after"], cfg["before"]
    for q in cfg["queries"]:
        q["before"], q["after"] = q["after"], q["before"]
    rev = analyze_update(tmp_path / "after", tmp_path / "before", cfg)
    assert all(row["analysis"]["change"]["overall"] == "mitigated" for row in rev["results"])


def test_identity_unknown_and_equivalence(tmp_path):
    cfg = scenario(
        tmp_path,
        [
            (INSTRUCTION, "send(x)", [None, None]),
            (INSTRUCTION.upper(), "publish(y)", [False, None]),
        ],
    )
    unknown = run(tmp_path, cfg)
    for row in unknown["results"]:
        assert row["analysis"]["change"]["overall"] == "unknown"
        assert not row["analysis"]["change"]["regions"][0]["regions"]["added"]["lower"]
    cfg["after"] = cfg["before"]
    for q in cfg["queries"]:
        q["after"] = q["before"]
    same = analyze_update(tmp_path / "before", tmp_path / "before", cfg)
    for row in same["results"]:
        assert row["analysis"]["change"]["overall"] == "maintained"
        assert row["analysis"]["associations"] == []


def test_equivalent_update(tmp_path):
    cfg = scenario(
        tmp_path,
        [
            (INSTRUCTION, "send(x)", [False, True]),
            (INSTRUCTION.upper(), "publish(y)", [False, True]),
        ],
    )
    report = run(tmp_path, cfg)
    assert len(report["results"]) == 2
    for row in report["results"]:
        assert row["analysis"]["change"]["overall"] == "maintained"
        assert not row["analysis"]["associations"]
    assert json.loads(json.dumps(report))["status"] == "completed"


def test_parse_failure(tmp_path):
    cfg = scenario(tmp_path, [("Synthetic.", "send(x)", [True, True])] * 2)
    (tmp_path / "before" / "main.py").write_text("if (")
    r = run(tmp_path, cfg)
    assert r["status"] == "analysis_failed" and not r["results"]
    assert any(p["reason"] == "invalid_python" for p in r["snapshots"]["before"]["problems"])


def test_new_versus_existing(tmp_path):
    cfg = scenario(
        tmp_path,
        [("Synthetic.", "send(1)", [True, True]), ("Synthetic.", "send(2)", [False, True])],
    )
    result = run(tmp_path, cfg)["results"][0]["analysis"]
    assert (
        result["change"]["overall"] == "introduced"
        and result["associations"][0]["direction"] == "added"
    )
    cfg["queries"][0]["before"]["contracts"] = []
    uncertain = run(tmp_path, cfg)["results"][0]["analysis"]["change"]
    assert uncertain["overall"] == "unknown"
    assert all(r["before"] == "missing" for r in uncertain["regions"])


def test_no_queries_or_unresolved_identity(tmp_path):
    cfg = scenario(tmp_path, [("Synthetic.", "send(x)", [True, True])] * 2)
    for side in ("before", "after"):
        del cfg[side]["contract"]["units"][0]["anchor"]
    analysis = run(tmp_path, cfg)["results"][0]["analysis"]
    assert analysis["change"]["reason"] == "identity_unresolved" and not analysis["associations"]
    cfg["queries"] = []
    assert run(tmp_path, cfg)["status"] == "no_queries"


def test_failure_summary_is_independent(tmp_path):
    cfg = scenario(tmp_path, [("", "send(x)", [True, True])] * 2)
    (tmp_path / "before" / "main.py").write_text("if (")
    side = run(tmp_path, cfg)["snapshots"]["before"]
    summary = next(d for d in side["problems"] if d["reason"] == "invalid_python")
    original = next(d for d in side["scs"]["diagnostics"] if d["reason"] == "invalid_python")
    summary["reason"] = "edited"
    assert original["reason"] == "invalid_python"
    assert any(
        p["reason"] == "invalid_python"
        for p in run(tmp_path, cfg)["snapshots"]["before"]["problems"]
    )


def test_opposite_keys_only_authorizations(tmp_path):
    cfg = scenario(
        tmp_path, [(INSTRUCTION, "send(1)", [True, True]), (INSTRUCTION, "send(1)", [False, True])]
    )
    q = next(q for q in cfg["queries"] if q["id"] == "may_cause")
    q["before"], q["after"] = q["after"], q["before"]
    analyses = {r["id"]: r["analysis"] for r in run(tmp_path, cfg)["results"]}
    for key, expected in (("operand", "introduced"), ("may_cause", "resolved")):
        a = analyses[key]
        assert a["change"]["overall"] == expected
        assert a["causal_status"] == "not_established" and a["files"] == []
        (link,) = a["associations"]
        assert link["certainty"] == "definite" and not link["semantic_dependencies"]


def test_shifted_evidence_stays_in_its_modality(tmp_path):
    cfg = scenario(
        tmp_path,
        [(INSTRUCTION, "send(1)", [True, True]), (INSTRUCTION.upper(), "\nsend(2)", [False, True])],
    )
    report = run(tmp_path, cfg)
    for row in report["results"]:
        program = row["id"] == "operand"
        paths = row["analysis"]["associations"][0]["paths"]
        for p in paths:
            expected_file = "main.py" if program else "SKILL.md"
            line = 2 if program and p["side"] == "after" else 1
            hits = [h for loc in p["locations"] for h in loc["edits"]]
            assert hits and all(
                h["path"] == expected_file and h["matched_lines"] == [line, line] for h in hits
            )
    for side in report["snapshots"].values():
        g = side["graph"]
        kinds = {n["id"]: n["kind"] for n in g["nodes"]}
        assert all(
            {kinds[e["source"]], kinds[e["target"]]} != {"instruction_action", "call_expression"}
            for e in g["edges"]
        )


@pytest.mark.parametrize("invalid", ["configuration", "duplicate", "skill", "digest", "members"])
def test_invalid_contract(tmp_path, invalid):
    cfg = scenario(tmp_path, [("Synthetic.", "send(x)", [True, True])] * 2)
    if invalid == "configuration":
        cfg["configuration"] = " "
    elif invalid == "duplicate":
        cfg["queries"] *= 2
    elif invalid == "skill":
        cfg["before"]["contract"]["skill"] = "different"
    elif invalid == "digest":
        cfg["before"]["contract"]["graph_sha256"] = "0" * 64
    else:
        cfg["queries"][0]["before"]["members"] = ["unknown"]
    with pytest.raises(ValueError):
        run(tmp_path, cfg)
