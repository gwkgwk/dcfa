"""Verify P04 graph references against a single immutable source snapshot."""

import ast
import hashlib
import json
import os
import re
import stat
from collections import Counter, defaultdict, deque
from pathlib import Path

from . import scs
from .graph import canonical, validate_graph
from .skill_reader import redirected, scan

EDGE_RULES = {
    "contains": "P04 structural membership or operand ownership; no execution order.",
    "operand": "A named call has a syntactic argument or receiver at this source occurrence.",
    "describes": "P03 interprets the anchored instruction as the recorded action.",
    "reads": "Replaying one instruction yields the matching input role and a unique action.",
    "produces": "Replaying one instruction yields the matching output role and a unique action.",
    "exposes": "The same instruction yields a context role and a unique action.",
    "crosses-boundary": "The same instruction yields a boundary role and a unique action.",
    "may_cause": "The same instruction yields an effect role and a unique action.",
    "result_to_operand": "Direct AST call/argument nesting; value flow requires evaluation.",
    "may_invoke": "Analyst declaration binds the named call slot; runtime dispatch is unknown.",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replay(root):
    files = {}
    readable = {}
    occurrences = defaultdict(deque)
    issues = []

    def issue(state, reason, path, line=None):
        issues.append(dict(state=state, reason=reason, path=path, line=line))

    def raw(path, data):
        readable[path] = {"sha256": digest(data), "bytes": len(data)}

    for path, role, text in scan(root, issue, on_bytes=raw):
        if text is None:
            files[path] = role
            continue
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        facts = {group: [] for group in scs.GROUPS}
        positions = {}
        material = scs.Material(path, text, facts, issue)

        def on_call(claim, node, positions=positions, text=text):
            positions[id(claim)] = {
                "node_type": "Call",
                "source": ast.get_source_segment(text, node),
                "start_utf8_column": node.col_offset,
                "end_utf8_column": node.end_col_offset,
            }

        if role == "skill_document":
            material.document()
        elif role == "metadata":
            material.metadata(material.lines, 0)
        else:
            material.python(text, on_call=on_call)
        for group, claims in facts.items():
            for claim in claims:
                ev = claim["evidence"]
                snippet = "\n".join(material.lines[ev["start_line"] - 1 : ev["end_line"]])
                if not (
                    1 <= ev["start_line"] <= ev["end_line"] <= len(material.lines)
                    and snippet == ev["snippet"]
                ):
                    continue
                occurrences[(group, canonical(claim))].append(
                    {
                        "path": path,
                        "namespace": "skill",
                        "sha256": readable[path]["sha256"],
                        "source": ev["method"],
                        "start_line": ev["start_line"],
                        "end_line": ev["end_line"],
                        "snippet": snippet,
                        "ast": positions.get(id(claim)),
                        "confidence": ev["confidence"],
                    }
                )
    return files, readable, occurrences, issues


def binding_spans(path, bindings):
    """Read an explicitly supplied analyst JSON array, retaining exact object extents."""
    if path is None:
        return []
    path = Path(path)
    if (
        ".." in path.parts
        or path.drive.startswith("\\\\")
        or (os.name == "nt" and any(":" in part for part in path.parts if part != path.anchor))
    ):
        raise ValueError("unsafe binding path")
    path = path.absolute()
    for parent in reversed(path.parents):
        if redirected(parent.lstat()):
            raise ValueError("redirected binding directory")
    info = path.lstat()
    if redirected(info) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("unsafe binding artifact")
    with path.open("rb") as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError("binding artifact exceeds budget")
    text = data.decode("utf-8-sig")

    def unique(pairs):
        if len(dict(pairs)) != len(pairs):
            raise ValueError("duplicate binding key")
        return dict(pairs)

    if canonical(json.loads(text, object_pairs_hook=unique)) != canonical(bindings):
        return []
    whitespace = re.compile(r"[ \r\n\t]*")
    cursor = whitespace.match(text).end() + 1
    decoder = json.JSONDecoder()
    result = []
    sha = digest(data)
    for binding in bindings:
        start = whitespace.match(text, cursor).end()
        _, end = decoder.raw_decode(text, start)
        result.append(
            {
                "namespace": "analyst",
                "path": Path(path).name,
                "sha256": sha,
                "source": "tool_declaration",
                "start_char": start,
                "end_char": end,
                "snippet": text[start:end],
                "basis": binding["basis"],
            }
        )
        cursor = whitespace.match(text, end).end() + 1
    return result


def build_index(graph, root, binding_file=None):
    validate_graph(graph)
    summary = graph["scs"]
    files, readable, occurrences, issues = replay(root)
    origins = {}
    entities = {}
    forward = {}

    def origin(ref, witness, reason):
        origins[ref] = {"witness": witness, "missing_reason": None if witness else reason}
        if witness:
            key = witness["namespace"] + "/" + witness["path"]
            forward.setdefault(
                key, {"sha256": witness["sha256"], "capabilities": [], "nodes": [], "edges": []}
            )

    def file_witness(path):
        if path not in readable:
            return None
        return {
            "namespace": "skill",
            "path": path,
            "source": "snapshot_file",
            "sha256": readable[path]["sha256"],
            "byte_range": [0, readable[path]["bytes"]],
        }

    document = next((p for p in files if files[p] == "skill_document"), None)
    origin("/scs", file_witness(document), "snapshot_entry_unavailable")
    for i, entry in enumerate(summary["files"]):
        path = entry["path"]
        w = file_witness(path) if files.get(path) == entry["role"] else None
        origin(f"/scs/files/{i}", w, "file_unavailable_or_role_mismatch")
        if not w:
            origins[f"/scs/files/{i}"]["claimed_path"] = path
    for group in scs.GROUPS:
        counts = Counter(canonical(claim) for claim in summary[group])
        verified = {key for key, count in counts.items() if len(occurrences[(group, key)]) == count}
        for i, claim in enumerate(summary[group]):
            ref = f"/scs/{group}/{i}"
            key = canonical(claim)
            w = occurrences[(group, key)].popleft() if key in verified else None
            origin(ref, w, "claim_location_or_multiplicity_mismatch")
            if not w:
                ev = claim["evidence"]
                origins[ref]["unverified_location"] = {
                    field: ev[field] for field in ("path", "start_line", "end_line", "method")
                }
            entities[ref] = group

    try:
        spans = binding_spans(binding_file, graph["bindings"])
    except FileNotFoundError:
        spans = []
    for i, _ in enumerate(graph["bindings"]):
        origin(
            f"/bindings/{i}",
            spans[i] if spans else None,
            "binding_original_unavailable_or_mismatch",
        )

    def owner(pointer):
        # P04 operand and instruction-text references refine their parent SCS claim.
        while pointer not in origins:
            if "/" not in pointer:
                raise ValueError("unresolvable graph evidence pointer")
            pointer = pointer.rsplit("/", 1)[0]
        return pointer

    reverse = {"capabilities": {}, "nodes": {}, "edges": {}}
    by_capability = {ref: {"nodes": [], "edges": []} for ref in entities}

    def target(kind, key, pointers, basis, uncertainty):
        refs = list(dict.fromkeys(owner(p) for p in pointers))
        for ref in tuple(refs):
            if ref.startswith("/bindings/"):
                slot = graph["bindings"][int(ref.split("/")[-1])]["operation"]
                call = f"/scs/operations/{slot}"
                if call not in refs:
                    refs.append(call)
        valid = [ref for ref in refs if origins[ref]["witness"] is not None]
        status = "verified" if len(valid) == len(refs) else ("partial" if valid else "missing")
        reverse[kind][key] = {
            "status": status,
            "origins": refs,
            "graph_pointers": pointers,
            "capabilities": [r for r in refs if r in entities],
            "basis": basis,
            "uncertainty": uncertainty,
        }
        if kind != "capabilities":
            for ref in refs:
                if ref in entities:
                    by_capability[ref][kind].append(key)
        for filename in dict.fromkeys(
            origins[r]["witness"]["namespace"] + "/" + origins[r]["witness"]["path"] for r in valid
        ):
            forward[filename][kind].append(key)

    for ref, group in entities.items():
        target("capabilities", ref, [ref], group, "static_claim_only")
    for node in graph["nodes"]:
        refs = [node["evidence"]]
        target("nodes", node["id"], refs, node["kind"], "no_runtime_observation")
    for i, edge in enumerate(graph["edges"]):
        target("edges", f"/edges/{i}", edge["evidence"], edge["relation"], edge["certainty"])

    complete = all(
        e["status"] == "verified" for targets in reverse.values() for e in targets.values()
    )
    return {
        "schema_version": "p05.1",
        "edge_rules": {
            key: EDGE_RULES[key] for key in sorted({e["relation"] for e in graph["edges"]})
        },
        "graph_sha256": digest(canonical(graph).encode()),
        "mapping_status": "verified" if complete else "incomplete",
        "scs_status": summary["status"],
        "runtime_observation": graph["runtime_observation"],
        "origins": origins,
        "by_file": forward,
        "by_capability": by_capability,
        "by_target": reverse,
        "scan_diagnostics": issues,
    }
