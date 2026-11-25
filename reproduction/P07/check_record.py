"""Check stored evidence for the reviewed top-level pair."""
import json
from pathlib import Path
from xml.etree import ElementTree

root = Path(__file__).parent / "top-level"
data = json.loads((root / "module-returns.json").read_text(encoding="utf-8"))
ns = {"g": "http://graphml.graphdrawing.org/xmlns"}
for side in ("before", "after"):
    graph = ElementTree.parse(root / f"{side}.graphml")
    nodes = {n.attrib["id"] for n in graph.findall(".//g:node", ns)}
    edges = graph.findall(".//g:edge", ns)
    print(side, len(nodes), "exported nodes,", len(edges), "exported edges")
    if side == "after":
        assert edges
        relation, paths = next(
            row for row in data[side]["relations"] if row[0] == [":local:demo", "path"]
        )
        assert paths and all(path and set(path) <= nodes for path in paths)
assert data["before"]["relations"] == []
assert [":local", "path"] in data["flagged_single_local_rels_from_tuples"]
print("Recorded cross-domain relation, witness nodes and version delta verified")
