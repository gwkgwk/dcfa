"""P11 §5 finite-context differential for one policy key and one P12 capability unit."""

from copy import deepcopy
from hashlib import sha256
from itertools import product
from string import hexdigits

from .graph import canonical, validate_graph
from .policy import RULES, symbol

VALUES = {"safe": (0,), "violation": (1,), "unknown": (0, 1), "missing": (0, 1)}


def label(mask):
    removed, added, common = mask & 1, mask & 2, mask & 4
    if removed and added:
        return "mixed"
    if removed:
        return "mitigated" if common else "resolved"
    if added:
        return "aggravated" if common else "introduced"
    return "maintained"


def prepare(side, evidence, domain):
    graph = side["graph"]
    validate_graph(graph)
    digest = sha256(canonical(graph).encode()).hexdigest()
    members = tuple(sorted(side["members"]))
    inventory = {tuple(sorted(unit["members"])) for unit in evidence["units"]}
    if digest != evidence["graph_sha256"] or (members and members not in inventory):
        raise ValueError("snapshot or capability mismatch")
    key = side["key"]
    if len(key) != 4 or key[0] not in RULES or not all(map(symbol, key)):
        raise ValueError("invalid policy key")
    if not symbol(side["configuration"]):
        raise ValueError("missing configuration identity")
    reports = {}
    for r in side["reports"]:
        scope = r["scope"]
        ctx = scope["purpose"], scope["invocation"]
        actual = [r["policy"], scope["actor"], scope["resource"], scope["action"]]
        if (
            not members
            or digest != r["graph_sha256"]
            or actual != list(key)
            or ctx in reports
            or ctx not in domain
        ):
            raise ValueError("misbound or duplicate policy report")
        state = r["state"]
        bounds = {
            "safe": (False, False),
            "unknown": (False, True),
            "violation": (True, True),
            "not_applicable": (None, None),
        }[state]
        if (
            r["lower"] is not bounds[0]
            or r["upper"] is not bounds[1]
            or bool(r["witnesses"]) != (state == "violation")
            or (state == "not_applicable") != (RULES[key[0]][0] != key[3])
        ):
            raise ValueError("inconsistent policy report")
        for entry in r["witnesses"] + r["candidates"] + r["excluded"]:
            if entry["prefix"]["effect"] not in members:
                raise ValueError("effect outside policy unit")
        reports[ctx] = r
    return members, reports


def compare(before, after, mapping, contexts):
    """Compare one key. key order is policy, actor, resource, action."""
    domain = set()
    for row in contexts:
        if (
            not isinstance(row, (list, tuple))
            or len(row) != 2
            or not all(map(symbol, row))
            or tuple(row) in domain
        ):
            raise ValueError("invalid context domain")
        domain.add(tuple(row))
    if not domain:
        raise ValueError("empty context domain")
    a, b = (mapping["evidence"][s] for s in ("before", "after"))
    old, left = prepare(before, a, domain)
    new, right = prepare(after, b, domain)
    result = dict(
        contexts=sorted(domain),
        sides=[
            dict(
                version=e["version"],
                graph_sha256=e["graph_sha256"],
                environment=e["environment"],
                skill=e["skill"],
                members=m,
                key=deepcopy(side["key"]),
                configuration=side["configuration"],
                reports=deepcopy(side["reports"]),
            )
            for side, e, m in ((before, a, old), (after, b, new))
        ],
    )
    if (
        any(a[k] != b[k] for k in ("environment", "scope", "skill"))
        or before["configuration"] != after["configuration"]
        or tuple(before["key"]) != tuple(after["key"])
    ):
        return dict(result, status="incomparable", reason="different_key_or_configuration")
    if not old or not new:
        category = "added" if new else "deleted"
        if (new or old) in {tuple(sorted(m)) for m in mapping[category]}:
            return dict(
                result,
                status="capability_" + category,
                observed_states=[
                    dict(context=c, state=(right or left).get(c, {}).get("state", "missing"))
                    for c in sorted(domain)
                ],
            )
        return dict(result, status="incomparable", reason="absence_unproved")
    matches = [
        p
        for p in mapping["aligned"]
        if tuple(sorted(p["before"])) == old or tuple(sorted(p["after"])) == new
    ]
    if (
        len(matches) != 1
        or tuple(sorted(matches[0]["before"])) != old
        or tuple(sorted(matches[0]["after"])) != new
    ):
        return dict(result, status="incomparable", reason="identity_unresolved")
    result["alignment"] = deepcopy(matches[0])
    fingerprints = [side.get("snapshot_sha256") for side in (before, after)]
    identical_snapshot = before is after or (
        all(
            isinstance(f, str) and len(f) == 64 and all(c in hexdigits for c in f)
            for f in fingerprints
        )
        and fingerprints[0].lower() == fingerprints[1].lower()
    )
    same = (
        identical_snapshot
        and a["graph_sha256"] == b["graph_sha256"]
        and old == new
        and left == right
    )
    regions = []
    masks = {0}
    for c in sorted(domain):
        x, y = (r.get(c, {}).get("state", "missing") for r in (left, right))
        if RULES[before["key"][0]][0] != before["key"][3]:
            if x != y:
                return dict(
                    result, status="incomparable", reason="applicability_unresolved", context=c
                )
            regions.append(dict(context=c, status="not_applicable"))
            continue
        worlds = [(i, j) for i, j in product(VALUES[x], VALUES[y]) if not same or i == j]
        bits = {(1 if i else 2) if i != j else (4 if i else 0) for i, j in worlds}
        masks = {previous | bit for previous, bit in product(masks, bits)}
        bounds = {
            name: dict(lower=bits == {bit}, upper=bit in bits)
            for bit, name in ((1, "removed"), (2, "added"), (4, "persistent"), (0, "satisfied"))
        }
        certainty = (
            "unchanged"
            if len(VALUES[x]) == len(VALUES[y])
            else "increased"
            if len(VALUES[x]) > len(VALUES[y])
            else "decreased"
        )
        regions.append(dict(context=c, before=x, after=y, certainty=certainty, regions=bounds))
    labels = sorted({label(m) for m in masks})
    if all(r.get("status") == "not_applicable" for r in regions):
        return dict(result, status="not_applicable", regions=regions)
    return dict(
        result,
        status="compared",
        overall=labels[0] if len(labels) == 1 else "unknown",
        possible_labels=labels,
        identity_certificate=same,
        regions=regions,
    )
