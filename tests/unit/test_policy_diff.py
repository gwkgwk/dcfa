from itertools import product

import pytest

from dcfa.alignment import align
from dcfa.evidence import build_index
from dcfa.graph import build_graph
from dcfa.policy import evaluate
from dcfa.policy_diff import compare, label
from dcfa.scs import extract

CONTEXTS = [("preview", "a"), ("preview", "b")]


def snapshot(root, code, states):
    root.mkdir()
    (root / "SKILL.md").write_text("Synthetic.")
    (root / "main.py").write_text(code)
    g = build_graph(extract(root))
    idx = build_index(g, root)
    ids = [n["id"] for n in g["nodes"] if n["kind"] == "call_expression"][-1:]
    units = [
        dict(
            members=[n],
            role=["worker", "send", "value", "demo", "publish"],
            anchor="api",
            certificate="synthetic interface",
        )
        for n in ids
    ]
    bundle = dict(
        graph=g,
        index=idx,
        contract=dict(
            graph_sha256=idx["graph_sha256"],
            skill="one",
            environment="E",
            scope="dispatch",
            version=root.name,
            units=units,
            coverage_certificate="closed",
        ),
    )
    reports = []
    for (purpose, invocation), state in zip(CONTEXTS, states, strict=False):
        i, e = next(
            (i, e)
            for i, e in enumerate(g["edges"])
            if e["relation"] == "operand" and e["target"] in ids
        )
        scope = dict(
            actor="worker", resource="demo", action="send", purpose=purpose, invocation=invocation
        )
        grants = (
            []
            if state == "?"
            else [dict(scope, source=e["source"], allowed=state == "S", reference="decision")]
        )
        trace = dict(
            source=e["source"],
            effect=e["target"],
            edges=[i],
            reference="binding",
            private=True,
            external=True,
            sensitivity_retained=True,
            feasible=True,
            bound=True,
        )
        reports.append(
            evaluate(
                g,
                idx,
                dict(
                    scope,
                    policy="confidentiality",
                    graph_sha256=idx["graph_sha256"],
                    reference="model",
                    coverage_certificate="closed",
                    prefixes=[trace],
                    authorizations=grants,
                ),
            )
        )
    return bundle, dict(
        graph=g,
        reports=reports,
        members=ids,
        configuration="E/p13/fixed-tools/fixed-budget",
        key=["confidentiality", "worker", "demo", "send"],
    )


@pytest.mark.parametrize(
    "old,new,expected",
    [
        ("SS", "SS", "maintained"),
        ("SS", "SV", "introduced"),
        ("VS", "VS", "maintained"),
        ("VS", "VV", "aggravated"),
        ("VV", "VS", "mitigated"),
        ("VV", "SS", "resolved"),
        ("VS", "SV", "mixed"),
        ("?S", "VS", "unknown"),
    ],
)
def test_paired(tmp_path, old, new, expected):
    a, left = snapshot(tmp_path / "v1", "send(x)", old)
    b, right = snapshot(tmp_path / "v2", "publish(y)", new)
    r = compare(left, right, align(a, b), CONTEXTS)
    assert r["overall"] == expected
    for row, x, y in zip(r["regions"], old, new, strict=True):
        assert row["regions"]["persistent"]["lower"] == (x == y == "V")
        assert row["regions"]["satisfied"]["lower"] == (x == y == "S")
        assert row["regions"]["added"]["lower"] == (x == "S" and y == "V")
    if old.startswith("?"):
        assert r["possible_labels"] == ["introduced", "maintained"]
        assert r["regions"][0]["certainty"] == "increased"
    if "V" in new:
        assert any(report["witnesses"] for report in r["sides"][1]["reports"])


def test_identity_and_missing(tmp_path):
    a, left = snapshot(tmp_path / "v1", "send(x)", "??")
    m = align(a, a)
    r = compare(left, left, m, CONTEXTS)
    assert r["overall"] == "maintained" and all(
        not c["regions"]["added"]["upper"] for c in r["regions"]
    )
    right = dict(left, reports=[])
    assert compare(left, right, m, CONTEXTS)["overall"] == "unknown"
    assert (
        compare(left, dict(right, configuration="other"), m, CONTEXTS)["status"] == "incomparable"
    )


def test_unmatched(tmp_path):
    a, left = snapshot(tmp_path / "v1", "", "")
    b, right = snapshot(tmp_path / "v2", "send(x)", "VS")
    for x, y, i, j, category in [(a, b, left, right, "added"), (b, a, right, left, "deleted")]:
        r = compare(i, j, align(x, y), CONTEXTS)
        assert r["status"] == "capability_" + category
        assert [c["state"] for c in r["observed_states"]] == ["violation", "safe"]


def test_independent_set_oracle():
    for x, y in product(range(8), repeat=2):
        old = {i for i in range(3) if x & 1 << i}
        new = {i for i in range(3) if y & 1 << i}
        expected = (
            "maintained"
            if old == new
            else "introduced"
            if not old
            else "resolved"
            if not new
            else "aggravated"
            if old < new
            else "mitigated"
            if new < old
            else "mixed"
        )
        assert label(bool(old - new) + 2 * bool(new - old) + 4 * bool(old & new)) == expected


def test_changed_local_id_and_unresolved_identity(tmp_path):
    a, left = snapshot(tmp_path / "old", "send(x)", "VS")
    b, right = snapshot(tmp_path / "new", "local(z)\npublish(y)", "VS")
    assert left["members"] != right["members"]
    assert compare(left, right, align(a, b), CONTEXTS)["overall"] == "maintained"
    for bundle in (a, b):
        del bundle["contract"]["units"][0]["anchor"]
    assert compare(left, right, align(a, b), CONTEXTS)["reason"] == "identity_unresolved"


@pytest.mark.parametrize("action,expected", [("write", "not_applicable"), ("send", "compared")])
def test_empty_reports_applicability(tmp_path, action, expected):
    a, left = snapshot(tmp_path / "old", "send(x)", "")
    b, right = snapshot(tmp_path / "new", "send(y)", "")
    for side in (left, right):
        side["key"][3] = action
    r = compare(left, right, align(a, b), CONTEXTS)
    assert r["status"] == expected
    if expected == "not_applicable":
        assert "possible_labels" not in r
        assert all(row["status"] == expected for row in r["regions"])


@pytest.mark.parametrize(
    "before,after,identical",
    [
        ("aB" * 32, "Ab" * 32, True),
        ("AB" * 32, "AB" * 32, True),
        ("aa" * 32, "ab" * 32, False),
        ("Ａ" * 64, "Ａ" * 64, False),
        ("a" * 63, "a" * 63, False),
    ],
)
def test_digest_representation(tmp_path, before, after, identical):
    a, left = snapshot(tmp_path / "old", "send(x)", "??")
    m = align(a, a)
    left["snapshot_sha256"] = before
    right = dict(left, snapshot_sha256=after)
    result = compare(left, right, m, CONTEXTS)
    assert result["identity_certificate"] is identical
    assert result["regions"][0]["regions"]["added"]["upper"] is not identical
    assert not compare(left, dict(right, reports=[]), m, CONTEXTS)["identity_certificate"]


def test_certainty_not_direction(tmp_path):
    a, left = snapshot(tmp_path / "old", "send(x)", "SV")
    b, right = snapshot(tmp_path / "new", "send(y)", "V?")
    rows = compare(left, right, align(a, b), CONTEXTS)["regions"]
    assert [r["certainty"] for r in rows] == ["unchanged", "decreased"]
    assert rows[0]["regions"]["added"]["lower"]


def test_context_table_against_sets(tmp_path):
    from itertools import combinations

    a, left = snapshot(tmp_path / "old", "send(x)", "SS")
    b, right = snapshot(tmp_path / "new", "send(y)", "SS")
    mapping = align(a, b)

    def variants(side, root, code):
        tables = {
            s: snapshot(root / str(i), code, s * 2)[1]["reports"] for i, s in enumerate("SV?")
        }
        for states in product("SV?-", repeat=2):
            reports = [tables[s][i] for i, s in enumerate(states) if s != "-"]
            sets = [
                set(sub)
                for size in range(3)
                for sub in combinations(range(2), size)
                if all(
                    (s != "V" or i in sub) and (s != "S" or i not in sub)
                    for i, s in enumerate(states)
                )
            ]
            yield dict(side, reports=reports), sets

    for (x, old), (y, new) in product(
        variants(left, tmp_path / "old", "send(x)"), variants(right, tmp_path / "new", "send(y)")
    ):
        labels = set()
        for i, j in product(old, new):
            labels.add(
                "maintained"
                if i == j
                else "introduced"
                if not i
                else "resolved"
                if not j
                else "aggravated"
                if i < j
                else "mitigated"
                if j < i
                else "mixed"
            )
        assert compare(x, y, mapping, CONTEXTS)["possible_labels"] == sorted(labels)


def test_missing_and_reported_inapplicability(tmp_path):
    a, left = snapshot(tmp_path / "before", "send(x)", "")
    b, right = snapshot(tmp_path / "after", "send(y)", "")
    for bundle, side in ((a, left), (b, right)):
        side["key"][3] = "write"
        for purpose, invocation in CONTEXTS:
            side["reports"].append(
                evaluate(
                    side["graph"],
                    bundle["index"],
                    dict(
                        graph_sha256=bundle["index"]["graph_sha256"],
                        policy="confidentiality",
                        actor="worker",
                        resource="demo",
                        action="write",
                        purpose=purpose,
                        invocation=invocation,
                        reference="synthetic",
                        prefixes=[],
                        authorizations=[],
                    ),
                )
            )
    mapping = align(a, b)
    assert compare(left, right, mapping, CONTEXTS)["status"] == "not_applicable"
    right["reports"].pop()
    r = compare(left, right, mapping, CONTEXTS)
    assert r["status"] == "incomparable" and r["reason"] == "applicability_unresolved"
