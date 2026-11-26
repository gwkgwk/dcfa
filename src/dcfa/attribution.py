"""Relate finite P14 context changes to replayable, version-local edits."""

import ast
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import PurePosixPath, PureWindowsPath

from .evidence import digest
from .graph import canonical, validate_graph


def structure(path, data):
    if data is None or not path.endswith(".py"):
        return None
    try:
        return ast.dump(ast.parse(data))
    except (SyntaxError, ValueError, RecursionError):
        return None


def edits(before, after):
    """Compute byte-sensitive file edits with 1-based, inclusive source line ranges."""
    result = []
    for path in sorted(before.keys() | after.keys()):
        if (
            not isinstance(path, str)
            or not path
            or PurePosixPath(path).as_posix() != path
            or PureWindowsPath(path).anchor
            or ".." in PurePosixPath(path).parts
            or "\\" in path
        ):
            raise ValueError("invalid relative file path")
        old, new = before.get(path), after.get(path)
        if old == new:
            continue
        values = (old, new)
        lines = [v.splitlines(keepends=True) if v is not None else [] for v in values]
        ops = SequenceMatcher(None, *lines, autojunk=False).get_opcodes()
        record = dict(
            path=path,
            kind="added" if old is None else "deleted" if new is None else "modified",
            structure=[structure(path, v) for v in values],
            hunks=[],
        )
        for side, v in zip(("before", "after"), values, strict=True):
            record[side] = digest(v) if v is not None else None
        for tag, a, b, c, d in ops:
            if tag != "equal":
                record["hunks"].append(
                    dict(
                        kind=tag,
                        before=[a + 1, b] if a < b else None,
                        after=[c + 1, d] if c < d else None,
                    )
                )
        result.append(record)
    return result


def replay(side, snapshot, info, changes):
    graph, index, files = (snapshot[k] for k in ("graph", "index", "files"))
    validate_graph(graph)
    if (
        digest(canonical(graph).encode()) != index["graph_sha256"]
        or index["graph_sha256"] != info["graph_sha256"]
    ):
        raise ValueError("snapshot graph mismatch")
    if not all(isinstance(v, bytes) for v in files.values()):
        raise ValueError("expected immutable file bytes")
    for entry in graph["scs"]["files"]:
        if entry["path"] not in files:
            raise ValueError("incomplete file inventory")
    for name, entry in index["by_file"].items():
        if name.startswith("skill/"):
            path = name[len("skill/") :]
            if path not in files or digest(files[path]) != entry["sha256"]:
                raise ValueError("source digest mismatch")
    hits = {}
    for group, targets in index["by_target"].items():
        for target, rec in targets.items():
            matches = []
            for ref in rec["origins"]:
                w = index["origins"][ref]["witness"]
                if not w or w["namespace"] != "skill" or "start_line" not in w:
                    continue
                path = w["path"]
                data = files[path]
                lines = (
                    data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").split("\n")
                )
                lo, hi = w["start_line"], w["end_line"]
                if (
                    digest(data) != w["sha256"]
                    or not 1 <= lo <= hi <= len(lines)
                    or "\n".join(lines[lo - 1 : hi]) != w["snippet"]
                ):
                    raise ValueError("source span mismatch")
                for n, h in enumerate(changes.get(path, {}).get("hunks", [])):
                    span = h[side]
                    if span and span[0] <= hi and lo <= span[1]:
                        matches.append(
                            dict(
                                path=path,
                                hunk=n,
                                matched_lines=[max(lo, span[0]), min(hi, span[1])],
                                origin=ref,
                                witness=deepcopy(w),
                            )
                        )
            if matches:
                hits[group, target] = matches
    return hits


def literal(edge, evidence):
    """Recover only a single direct call's AST literal at a verified positional operand."""
    if edge["relation"] != "operand":
        return None
    prefix = edge["target"] + "/arg"
    slot = edge["source"].removeprefix(prefix)
    if not edge["source"].startswith(prefix) or not slot.isdecimal():
        return None
    for hit in evidence:
        w = hit["witness"]
        loc = w.get("ast", {})
        if not loc or w["start_line"] != w["end_line"]:
            continue
        segment = w["snippet"].encode()[loc["start_utf8_column"] : loc["end_utf8_column"]].decode()
        if segment != loc["source"]:
            raise ValueError("AST span mismatch")
        call = ast.parse(segment, mode="eval").body
        if isinstance(call, ast.Call) and int(slot) < len(call.args):
            value = call.args[int(slot)]
            if isinstance(value, ast.Constant):
                return dict(callee=ast.dump(call.func), slot=int(slot), value=ast.dump(value))
    return None


def attribute(before, after, mapping, delta):
    """Consume trusted P12/P14 results and complete in-memory file inventories."""
    changes = edits(before["files"], after["files"])
    by_path = {edit["path"]: edit for edit in changes}
    sides = (before, after)
    mappings = []
    for name, snap, info in zip(("before", "after"), sides, delta["sides"], strict=True):
        aligned = mapping["evidence"][name]
        if any(aligned[k] != info[k] for k in ("graph_sha256", "skill", "version", "environment")):
            raise ValueError("alignment version mismatch")
        mappings.append(replay(name, snap, info, by_path))
    output = dict(
        change=deepcopy(delta),
        files=changes,
        edit_targets=[
            [dict(group=g, target=t, locations=h) for (g, t), h in side.items()]
            for side in mappings
        ],
        associations=[],
        causal_status="not_established",
    )
    if delta["status"] != "compared":
        output["uncertainty"] = "no comparable policy change"
        return output
    pair = delta["alignment"]
    if canonical(pair) not in {canonical(p) for p in mapping["aligned"]} or any(
        list(pair[k]) != list(info["members"])
        for k, info in zip(("before", "after"), delta["sides"], strict=True)
    ):
        raise ValueError("missing semantic alignment")
    for region in delta["regions"]:
        for direction in ("added", "removed"):
            bound = region.get("regions", {}).get(direction, {})
            if not bound.get("upper"):
                continue
            context = region["context"]
            association = dict(
                context=context,
                direction=direction,
                certainty="definite" if bound["lower"] else "possible",
                paths=[],
                semantic_dependencies=[],
                uncertainty=["policy facts and authorizations are external contracts"],
            )
            operands = [[], []]
            for i, (snap, info, hits) in enumerate(
                zip(sides, delta["sides"], mappings, strict=True)
            ):
                graph = snap["graph"]
                for report in info["reports"]:
                    if [report["scope"][k] for k in ("purpose", "invocation")] != list(context):
                        continue
                    for bucket in ("witnesses", "excluded", "candidates"):
                        for item in report[bucket]:
                            trace = item["prefix"]
                            node = trace["source"]
                            ids = [("nodes", node)]
                            for j in trace["edges"]:
                                if type(j) is not int or not 0 <= j < len(graph["edges"]):
                                    raise ValueError("invalid witness edge")
                                edge = graph["edges"][j]
                                if edge["source"] != node:
                                    raise ValueError("disconnected witness")
                                node = edge["target"]
                                ids.extend([("edges", f"/edges/{j}"), ("nodes", node)])
                            if (
                                not trace["edges"]
                                or node != trace["effect"]
                                or node not in info["members"]
                            ):
                                raise ValueError("unbound effect")
                            indexed = snap["index"]
                            expected = {
                                (g, t): [
                                    indexed["origins"][ref]["witness"]
                                    for ref in indexed["by_target"][g][t]["origins"]
                                ]
                                for g, t in ids
                            }
                            reported = {
                                (e["group"], e["id"]): e["witnesses"] for e in item["evidence"]
                            }
                            if expected != reported:
                                raise ValueError("witness evidence mismatch")
                            if any(
                                indexed["by_target"][g][t]["status"] != "verified" for g, t in ids
                            ):
                                association["uncertainty"].append("partial path evidence")
                            pos = len(association["paths"])
                            path = dict(
                                side=("before", "after")[i],
                                bucket=bucket,
                                targets=ids,
                                edges=[deepcopy(graph["edges"][j]) for j in trace["edges"]],
                                locations=[
                                    dict(group=g, target=t, edits=hits[g, t])
                                    for g, t in ids
                                    if (g, t) in hits
                                ],
                            )
                            association["paths"].append(path)
                            if len(trace["edges"]) == 1 and item["conditions"].get("bound") is True:
                                key = ids[1]
                                if (
                                    snap["index"]["by_target"]["edges"][key[1]]["status"]
                                    == "verified"
                                ):
                                    value = literal(edge, hits.get(key, []))
                                    if value:
                                        operands[i].append((value, pos))
            if (
                all(len(lst) == 1 for lst in operands)
                and len(pair["before"]) == len(pair["after"]) == 1
            ):
                (x, p), (y, q) = operands[0][0], operands[1][0]
                if (
                    x["callee"] == y["callee"]
                    and x["slot"] == y["slot"]
                    and x["value"] != y["value"]
                ):
                    association["semantic_dependencies"].append(
                        dict(
                            rule="aligned_bound_literal_operand",
                            before=x,
                            after=y,
                            path_indices=[p, q],
                        )
                    )
            if not association["semantic_dependencies"]:
                association["uncertainty"].append(
                    "no replayed change to a supported semantic premise"
                )
            association["candidate_edits"] = [
                dict(path=path, hunk=hunk)
                for path, hunk in sorted(
                    {
                        (hit["path"], hit["hunk"])
                        for witness in association["paths"]
                        for location in witness["locations"]
                        for hit in location["edits"]
                    }
                )
            ]
            association["joint_sufficiency"] = "unknown"
            output["associations"].append(association)
    return output
