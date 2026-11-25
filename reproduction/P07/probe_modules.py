"""Collect original graph/domain/diff function returns without using memory telemetry."""

import json
import sys
from pathlib import Path

source, pair, output = (Path(arg).resolve() for arg in sys.argv[1:])
sys.path.insert(0, str(source))
import rogue_one_runner as runner  # noqa: E402

output.mkdir(exist_ok=True)
domains = []
record = {}
for label, version in [("before", "1.0.0"), ("after", "1.1.0")]:
    folder = pair / f"sample-{version}"
    with runner.wd(folder):
        odg = runner.odgen_main(argv=[(folder / "index.js").as_posix(),
                                     "-t", "data_flow", "--json", "--run-all"])
    graph = runner.ex.extract_idg(odg)
    if not any(str(a.get("name", "")).endswith("index.js") for _, a in odg.graph.nodes(data=True)):
        raise RuntimeError("No source AST")
    mapped = runner.td.td_rel_map(graph, odgen_graph=odg, consolidate_tds=True)
    domains.append(runner.td.rels_as_tuples(mapped))
    record[label] = {
        "file_node_nums": odg.file_node_nums,
        "objects": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "trust_domains": sorted({a["trust_domain"] for _, a in graph.nodes(data=True)
                                  if a.get("trust_domain")}),
        "relations": sorted(domains[-1]),
    }
    runner.td.sanitize_and_export(graph, output / f"{label}.graphml")

record["flagged_single_local_rels_from_tuples"] = sorted(
    runner.td.flagged_single_local_rels_from_tuples(*domains)
)
(output / "module-returns.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
