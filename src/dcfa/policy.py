"""Single-context finite-prefix monitors for the two P11 safety properties."""

from copy import deepcopy
from hashlib import sha256

from .graph import canonical, validate_graph

RULES = {
    "confidentiality": ("send", ("private", "sensitivity_retained", "external")),
    "integrity": ("write", ("untrusted", "protected")),
}
SCOPE = ("actor", "action", "resource", "purpose", "invocation")


def symbol(value):
    return isinstance(value, str) and bool(value.strip())


def truth(value):
    if value is not None and type(value) is not bool:
        raise ValueError("expected boolean or null")
    return value


def evaluate(graph, index, contract):
    """Evaluate a trusted, graph-bound finite contract. Missing required fields raise KeyError."""
    validate_graph(graph)
    digest = sha256(canonical(graph).encode()).hexdigest()
    if digest != index["graph_sha256"] or digest != contract["graph_sha256"]:
        raise ValueError("graph digest mismatch")
    policy = contract["policy"]
    action, predicates = RULES[policy]
    scope = {k: contract[k] for k in SCOPE}
    if not all(symbol(v) for v in (*scope.values(), contract["reference"])):
        raise ValueError("invalid scope or provenance")
    closure = contract.get("coverage_certificate")
    if closure is not None and not symbol(closure):
        raise ValueError("invalid coverage certificate")
    report = dict(
        policy=policy,
        scope=scope,
        graph_sha256=digest,
        reference=contract["reference"],
        coverage_certificate=closure,
        witnesses=[],
        candidates=[],
        excluded=[],
        graph_gaps=deepcopy(graph["unknowns"]),
        reasons=[],
    )
    applicable = scope["action"] == action
    protection = set()

    nodes = {n["id"]: n for n in graph["nodes"]}
    permissions = {}
    for grant in contract["authorizations"]:
        key = tuple(grant[k] for k in SCOPE) + (grant["source"],)
        if (
            not all(symbol(v) for v in (*key, grant["reference"]))
            or type(grant["allowed"]) is not bool
        ):
            raise ValueError("invalid authorization")
        if key in permissions and permissions[key]["allowed"] != grant["allowed"]:
            raise ValueError("conflicting authorizations")
        permissions[key] = grant

    for trace in contract["prefixes"]:
        start, end = trace["source"], trace["effect"]
        if start not in nodes or end not in nodes or not symbol(trace["reference"]):
            raise ValueError("invalid prefix endpoint or reference")
        cursor = start
        targets = [("nodes", start)]
        for i in trace["edges"]:
            if type(i) is not int or not 0 <= i < len(graph["edges"]):
                raise ValueError("invalid edge index")
            edge = graph["edges"][i]
            if edge["source"] != cursor or edge["relation"] not in {
                "operand",
                "result_to_operand",
                "reads",
                "may_cause",
            }:
                raise ValueError("invalid propagation edge")
            cursor = edge["target"]
            targets.extend([("edges", f"/edges/{i}"), ("nodes", cursor)])
        if (
            not trace["edges"]
            or cursor != end
            or nodes[end]["kind"] not in {"call_expression", "instruction_action", "effect"}
        ):
            raise ValueError("invalid effect path")

        evidence = {}
        complete = True
        for group, key in targets:
            record = index["by_target"][group][key]
            facts = [index["origins"][ref]["witness"] for ref in record["origins"]]
            complete &= (
                record["status"] == "verified" and bool(facts) and all(bool(f) for f in facts)
            )
            evidence[(group, key)] = facts
        grant = permissions.get(tuple(scope.values()) + (start,))
        conditions = {k: truth(trace.get(k)) for k in (*predicates, "feasible", "bound")}
        if not applicable:
            continue
        if policy == "integrity" and conditions["protected"] is not None:
            protection.add(conditions["protected"])
            if len(protection) > 1:
                raise ValueError("conflicting resource classification")
        conditions["unauthorized"] = None if grant is None else not grant["allowed"]
        conditions["traceable"] = True if complete else None
        reasons = [k for k, v in conditions.items() if v is None]
        bucket = (
            "excluded" if False in conditions.values() else "candidates" if reasons else "witnesses"
        )
        report[bucket].append(
            dict(
                prefix=deepcopy(trace),
                conditions=conditions,
                authorization=deepcopy(grant),
                unknown=reasons,
                evidence=[
                    dict(group=g, id=k, witnesses=deepcopy(v)) for (g, k), v in evidence.items()
                ],
            )
        )
    if not applicable:
        return dict(report, state="not_applicable", lower=None, upper=None)
    lower = bool(report["witnesses"])
    upper = lower or bool(report["candidates"]) or closure is None
    if policy == "integrity" and protection != {False}:
        upper = True
        report["reasons"].append("unrepresented_control_influence")
    if closure is None:
        report["reasons"].append("open_coverage")
    return dict(
        report,
        lower=lower,
        upper=upper,
        state="violation" if lower else "unknown" if upper else "safe",
    )
