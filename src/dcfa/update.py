"""Single-Skill update analysis over immutable snapshots and trusted finite contracts."""

from copy import deepcopy
from pathlib import Path

from .alignment import align
from .attribution import attribute
from .evidence import build_index, digest
from .graph import build_graph, canonical
from .policy import evaluate, symbol
from .policy_diff import compare
from .scs import extract
from .skill_reader import scan


def snapshot_digest(files):
    return digest(canonical(sorted((path, digest(data)) for path, data in files.items())).encode())


def _snapshot(root, spec):
    files = {}
    issues = []

    def issue(state, reason, path, line=None):
        issues.append(dict(state=state, reason=reason, path=path, line=line))

    for _ in scan(root, issue, on_bytes=files.__setitem__):
        pass
    summary = extract(root)
    problems = [
        deepcopy(d)
        for d in issues + summary["diagnostics"]
        if d["state"] in {"read_failure", "parse_failure"}
        or d["reason"] in {"named_stream_unexamined", "python_token_limit"}
    ]
    public = dict(scs=summary, snapshot_sha256=snapshot_digest(files), problems=problems)
    if problems or summary["status"] == "failed":
        return public, None
    graph = build_graph(summary, spec.get("bindings"))
    index = build_index(graph, root, spec.get("binding_file"))
    problems.extend(
        d for d in index["scan_diagnostics"] if d["state"] in {"parse_failure", "read_failure"}
    )
    hashes = {
        name.removeprefix("skill/"): record["sha256"]
        for name, record in index["by_file"].items()
        if name.startswith("skill/")
    }
    if hashes != {p: digest(v) for p, v in files.items()}:
        problems.append(dict(state="read_failure", reason="inventory_digest_mismatch"))
    if problems:
        return public, None
    public.update(graph=graph, index=index)
    return public, dict(graph=graph, index=index, files=files, contract=spec["contract"])


def analyze_update(old_path, new_path, config):
    """Return a JSON-compatible report. Invalid analyst contracts raise ValueError/KeyError."""
    configuration = config["configuration"]
    if not symbol(configuration):
        raise ValueError("invalid shared configuration")
    report = dict(
        configuration=configuration,
        config_sha256=digest(canonical(config).encode()),
        snapshots={},
        results=[],
    )
    bundles = []
    for name, root in (("before", old_path), ("after", new_path)):
        public, bundle = _snapshot(Path(root), config[name])
        report["snapshots"][name] = public
        bundles.append(bundle)
    if any(bundle is None for bundle in bundles):
        return dict(report, status="analysis_failed")
    old, new = bundles
    mapping = align(old, new)
    report["alignment"] = mapping
    seen = set()
    for query in config["queries"]:
        ident = query["id"]
        if not symbol(ident) or ident in seen:
            raise ValueError("invalid or duplicate query id")
        seen.add(ident)
        sides = []
        for name, b in zip(("before", "after"), bundles, strict=True):
            request = query[name]
            reports = [evaluate(b["graph"], b["index"], c) for c in request["contracts"]]
            sides.append(
                dict(
                    graph=b["graph"],
                    configuration=configuration,
                    key=query["key"],
                    reports=reports,
                    members=request["members"],
                    snapshot_sha256=report["snapshots"][name]["snapshot_sha256"],
                )
            )
        delta = compare(*sides, mapping, query["contexts"])
        report["results"].append(dict(id=ident, analysis=attribute(old, new, mapping, delta)))
    return deepcopy(dict(report, status="completed" if seen else "no_queries"))
