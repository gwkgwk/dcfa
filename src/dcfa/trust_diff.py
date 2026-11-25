"""Independent, directional RogueOne-style comparison of P08 program snapshots."""

import argparse
import hashlib
import json
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def location(item):
    require(isinstance(item.get("file"), str) and item["file"], "missing evidence file")
    require(type(item.get("line")) is int and item["line"] > 0, "invalid evidence line")


def closure(starts, adjacency, edges):
    parents = dict.fromkeys(sorted(starts))
    queue = deque(parents)
    while queue:
        node = queue.popleft()
        for index in adjacency[node]:
            target = edges[index]["target"]
            if target not in parents:
                parents[target] = index
                queue.append(target)
    return parents


def witness(node, parents, edges):
    path = []
    while parents[node] is not None:
        edge = parents[node]
        path.append(edge)
        node = edges[edge]["source"]
    return {"root": node, "edges": path[::-1]}


def extract(raw):
    require(isinstance(raw, dict), "expected snapshot object")
    status, phase = raw["status"], raw["entry_analysis"]
    require(isinstance(raw["entry"], str) and raw["entry"], "invalid entry")
    for key in ("nodes", "edges", "issues", "unvisited_functions"):
        require(isinstance(raw[key], list), f"expected list: {key}")
    complete = status == "complete_in_subset" and phase == "finished" and not raw["issues"]
    require(
        complete
        or (status == "partial" and phase in ("not_started", "incomplete") and raw["issues"]),
        "inconsistent analysis status",
    )
    require(phase != "not_started" or not (raw["nodes"] or raw["edges"]), "unstarted graph")
    nodes, roots, assumptions = {}, defaultdict(list), {}
    for n in raw["nodes"]:
        require(isinstance(n, dict), "invalid node")
        location(n)
        ident = n["id"]
        require(type(ident) is int and ident >= 0 and ident not in nodes, "invalid node identity")
        nodes[ident] = n
        kind, name = n["kind"], n["name"]
        require(
            kind in ("module", "api", "function", "literal", "result", "file_handle")
            and isinstance(name, str),
            "unsupported node",
        )
        if kind == "module":
            label = "import:" + name
            require(
                name.isidentifier()
                and n["domain"] == label
                and n["resolution"] in ("stdlib_name_unverified", "unverified_external"),
                "invalid import root",
            )
            assumptions[label] = n["resolution"]
        elif kind == "literal":
            label = ":local"
        elif kind == "api" and name == "open" and n["domain"] == "file":
            label = "builtin:file"
        else:
            continue
        roots[label].append(ident)
    edges = raw["edges"]
    adjacency = {kind: defaultdict(list) for kind in ("data_flow", "owns")}
    for i, e in enumerate(edges):
        require(isinstance(e, dict), "invalid edge")
        location(e)
        require(
            e["kind"] in adjacency
            and all(type(e[k]) is int and e[k] in nodes for k in ("source", "target")),
            "invalid edge reference",
        )
        adjacency[e["kind"]][e["source"]].append(i)
    owners = defaultdict(list)
    owns = {}
    for label, starts in roots.items():
        owns[label] = closure(starts, adjacency["owns"], edges)
        for obj in owns[label]:
            owners[obj].append(label)
    flows = {}
    for source, starts in sorted(roots.items()):
        reached = closure(starts, adjacency["data_flow"], edges)
        for obj in reached:
            for dest in owners[obj]:
                pair = (source, dest)
                if source != dest and pair not in flows:
                    flows[pair] = dict(
                        pair=list(pair),
                        common_object=obj,
                        data_flow=witness(obj, reached, edges),
                        owns=witness(obj, owns[dest], edges),
                    )
    return dict(
        status=status,
        entry=raw["entry"],
        entry_analysis=phase,
        issues=deepcopy(raw["issues"]),
        unvisited_functions=deepcopy(raw["unvisited_functions"]),
        import_assumptions=assumptions,
        roots=dict(roots),
        nodes=deepcopy(raw["nodes"]),
        edges=deepcopy(edges),
        flows=[flows[k] for k in sorted(flows)],
    )


def compare(before, after):
    sides = {}
    for label, raw in (("before", before), ("after", after)):
        try:
            sides[label] = extract(raw)
        except (ValueError, KeyError, TypeError, RecursionError) as exc:
            sides[label] = dict(status="invalid", issues=[str(exc)], flows=[])
    old, new = sides.values()
    left, right = ({tuple(f["pair"]) for f in s["flows"]} for s in (old, new))
    compatible = old.get("entry") == new.get("entry") and "entry" in old and "entry" in new
    added = right - left if compatible and old["status"] == "complete_in_subset" else set()
    deleted = left - right if compatible and new["status"] == "complete_in_subset" else set()
    kept = left & right if compatible else set()
    return dict(
        **sides,
        status="complete_in_subset"
        if compatible and all(s["status"] == "complete_in_subset" for s in (old, new))
        else "unknown_or_partial",
        compatible_entry=compatible,
        added=sorted(added),
        deleted=sorted(deleted),
        retained=sorted(kept),
        unresolved_before=sorted(left - kept - deleted),
        unresolved_after=sorted(right - kept - added),
        alerts=[
            dict(pair=p, reason="new_possible_cross_domain_flow", evidence_version="after")
            for p in sorted(added)
        ],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    inputs, errors, hashes = [], {}, {}
    for side in ("before", "after"):
        try:
            payload = getattr(args, side).read_bytes()
            hashes[side] = hashlib.sha256(payload).hexdigest()
            inputs.append(json.loads(payload.decode("utf-8-sig")))
        except (OSError, ValueError, RecursionError) as exc:
            inputs.append(None)
            errors[side] = f"{type(exc).__name__}: {exc}"
    result = compare(*inputs)
    result["input_sha256"] = hashes
    for side, error in errors.items():
        result[side]["issues"] = [error]
    print(json.dumps(result, indent=2))
    return int(result["status"] != "complete_in_subset")


if __name__ == "__main__":
    raise SystemExit(main())
