"""Align evidenced capability occurrences under an analyst-supplied finite contract."""

import argparse
import hashlib
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from .graph import canonical

KINDS = {"instruction_action", "call_expression", "effect"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def symbol(value):
    return isinstance(value, str) and bool(value.strip())


def prepare(bundle):
    graph, index, contract = (bundle[k] for k in ("graph", "index", "contract"))
    digest = hashlib.sha256(canonical(graph).encode()).hexdigest()
    require(index["graph_sha256"] == contract["graph_sha256"] == digest, "snapshot digest mismatch")
    for key in ("skill", "environment", "version", "scope"):
        require(symbol(contract[key]), f"missing {key}")
    closed = contract.get("coverage_certificate")
    require(closed is None or symbol(closed), "invalid coverage certificate")
    nodes = {n["id"]: n for n in graph["nodes"]}
    bindings = contract.get("neighbor_bindings")
    if "neighbor_bindings" in contract:
        require(
            isinstance(bindings, dict)
            and all(k in nodes and symbol(v) for k, v in bindings.items()),
            "invalid neighbor bindings",
        )
    eligible = {key for key, n in nodes.items() if n["kind"] in KINDS}
    used, units, anchors = set(), {}, set()
    specs = list(contract["units"])
    for spec in specs:
        members = spec["members"]
        require(
            isinstance(members, list)
            and members
            and len(set(members)) == len(members)
            and set(members) <= eligible - used,
            "invalid or overlapping unit",
        )
        used.update(members)
    specs.extend({"members": [key]} for key in sorted(eligible - used))
    for spec in specs:
        members = tuple(sorted(spec["members"]))
        evidence = []
        verified = True
        for member in members:
            record = index["by_target"]["nodes"][member]
            witnesses = [index["origins"][p]["witness"] for p in record["origins"]]
            verified &= record["status"] == "verified" and bool(witnesses) and all(witnesses)
            evidence.append(dict(node=member, witnesses=witnesses))
        cert = spec.get("certificate")
        require(cert is None or symbol(cert), "invalid capability certificate")
        require(
            len(members) == 1 or symbol(spec.get("aggregation_certificate")),
            "missing aggregation contract",
        )
        known = bool(verified and cert)
        role = spec.get("role", [None] * 5)
        require(
            isinstance(role, list) and len(role) == 5 and all(x is None or symbol(x) for x in role),
            "invalid role",
        )
        anchor = spec.get("anchor") if known else None
        require(
            anchor is None or symbol(anchor) and anchor not in anchors, "invalid or repeated anchor"
        )
        if anchor:
            anchors.add(anchor)
        # Only positively evidenced invariant slots constrain identity.
        slots = {}
        for slot in spec.get("slots", []):
            i, name, value = slot["edge"], slot["slot"], slot["neighbor_binding"]
            require(
                type(i) is int and 0 <= i < len(graph["edges"]) and symbol(name) and symbol(value),
                "invalid invariant slot",
            )
            edge = graph["edges"][i]
            inside = [end for end in ("source", "target") if edge[end] in members]
            require(len(inside) == 1 and edge["relation"] != "contains", "invalid boundary edge")
            if bindings is not None:
                neighbor = edge["target" if inside[0] == "source" else "source"]
                record = index["by_target"]["nodes"][neighbor]
                require(
                    bindings.get(neighbor) == value
                    and record["status"] == "verified"
                    and bool(record["origins"])
                    and all(index["origins"][p]["witness"] for p in record["origins"]),
                    "unverified or conflicting neighbor binding",
                )
            if known and index["by_target"]["edges"][f"/edges/{i}"]["status"] == "verified":
                binding = (inside[0], edge["relation"], value)
                require(name not in slots or slots[name] == binding, "inconsistent slot")
                slots[name] = binding
        rows = spec.get("observations")
        if rows is not None:
            require(
                isinstance(rows, list)
                and all(
                    isinstance(r, list) and len(r) == 4 and all(symbol(x) for x in r) for r in rows
                ),
                "invalid observation relation",
            )
        units[members] = dict(
            role=role if known else [None] * 5,
            anchor=anchor,
            slots=slots,
            rows=set(map(tuple, rows)) if known and rows is not None else None,
            evidence=evidence,
            certificate=cert if known else None,
            aggregation=spec.get("aggregation_certificate"),
            slot_evidence=spec.get("slots", []),
        )
    return contract, units


def compatible(x, y):
    return (
        not (x["anchor"] and y["anchor"] and x["anchor"] != y["anchor"])
        and all(a is None or b is None or a == b for a, b in zip(x["role"], y["role"], strict=True))
        and all(x["slots"][k] == y["slots"][k] for k in x["slots"].keys() & y["slots"].keys())
    )


def compare_rows(a, b):
    if a is None or b is None:
        return {"state": "unknown"}
    return dict(
        state="equal" if a == b else "different", removed=sorted(a - b), added=sorted(b - a)
    )


def align(before, after):
    old, left = prepare(before)
    new, right = prepare(after)
    require(all(old[k] == new[k] for k in ("skill", "environment", "scope")), "incomparable scopes")
    require(
        ("neighbor_bindings" in old) == ("neighbor_bindings" in new), "different neighbor contracts"
    )
    persistent = old.get("unique_persistent_roles", [])
    require(
        all(
            isinstance(r, list) and len(r) == 5 and all(symbol(v) for v in r)
            for r in persistent + new.get("unique_persistent_roles", [])
        ),
        "invalid persistent role",
    )
    roles = set(map(tuple, persistent))
    require(
        roles == set(map(tuple, new.get("unique_persistent_roles", []))), "different role contracts"
    )
    closed = bool(old.get("coverage_certificate") and new.get("coverage_certificate"))
    targets = defaultdict(set)
    sources = defaultdict(set)
    paired = []
    for i, x in left.items():
        for j, y in right.items():
            ok = compatible(x, y)
            if x["anchor"] and x["anchor"] == y["anchor"]:
                require(ok, "stable anchor contradicts identity constraints")
                paired.append((i, j, "stable_binding"))
            if ok:
                targets[i].add(j)
                sources[j].add(i)
    fixed_left = {i for i, _, _ in paired}
    fixed_right = {j for _, j, _ in paired}
    for i in targets:
        targets[i].difference_update(fixed_right)
    for j in sources:
        sources[j].difference_update(fixed_left)
    for i in sorted(left.keys() - fixed_left):
        if closed and tuple(left[i]["role"]) in roles and len(targets[i]) == 1:
            (j,) = targets[i]
            if left[i]["role"] == right[j]["role"] and len(sources[j]) == 1:
                paired.append((i, j, "unique_persistent_role"))
    aligned = []
    for i, j, basis in sorted(paired):
        fixed_left.add(i)
        fixed_right.add(j)
        x, y = left[i], right[j]
        a, b = x["rows"], y["rows"]
        full = compare_rows(a, b)
        security = compare_rows(
            *(None if rows is None else {(r[0], r[3]) for r in rows} for rows in (a, b))
        )
        if full["state"] == "equal" and (None in x["role"] or x["role"] != y["role"]):
            full = {"state": "unknown"}
        aligned.append(
            dict(
                before=i,
                after=j,
                identity_basis=basis,
                confidence="conditional_on_contract",
                full=full,
                security=security,
            )
        )
    result = dict(
        aligned=aligned, preserved=[], modified=[], added=[], deleted=[], unresolved=[], evidence={}
    )
    for pair in aligned:
        state = pair["full"]["state"]
        if state != "unknown":
            result["preserved" if state == "equal" else "modified"].append(
                [pair["before"], pair["after"]]
            )
    for side, contract, units, fixed, adj, other, absent in (
        ("before", old, left, fixed_left, targets, fixed_right, "deleted"),
        ("after", new, right, fixed_right, sources, fixed_left, "added"),
    ):
        evidence = dict(
            version=contract["version"],
            graph_sha256=contract["graph_sha256"],
            environment=contract["environment"],
            scope=contract["scope"],
            skill=contract["skill"],
            coverage_certificate=contract.get("coverage_certificate"),
            unique_persistent_roles=sorted(roles),
            units=[
                dict(
                    members=k,
                    **{n: v for n, v in u.items() if n != "rows"},
                    observations=None if u["rows"] is None else sorted(u["rows"]),
                )
                for k, u in sorted(units.items())
            ],
        )
        if "neighbor_bindings" in contract:
            evidence["neighbor_bindings"] = contract["neighbor_bindings"]
        result["evidence"][side] = deepcopy(evidence)
        for k in sorted(units.keys() - fixed):
            candidates = sorted(adj[k] - other)
            if (
                closed
                and not candidates
                and units[k]["certificate"]
                and None not in units[k]["role"]
            ):
                result[absent].append(k)
            else:
                result["unresolved"].append(
                    dict(
                        side=side,
                        members=k,
                        candidates=candidates,
                        reason="ambiguous_or_unproved"
                        if candidates
                        else "insufficient_coverage_or_role",
                    )
                )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        result = align(
            *(json.loads(p.read_text(encoding="utf-8-sig")) for p in (args.before, args.after))
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
        RecursionError,
    ) as exc:
        print(json.dumps({"status": "invalid_or_conflict", "reason": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
