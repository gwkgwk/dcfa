"""Check the published evidence against the two reviewed synthetic inputs."""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://graphml.graphdrawing.org/xmlns}"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_top_level(graph, paths):
    keys = {k.attrib["id"]: k.attrib["attr.name"] for k in graph.iter(NS + "key")}

    def fields(element):
        return {keys[d.attrib["key"]]: d.text for d in element.findall(NS + "data")}

    nodes = {n.attrib["id"]: fields(n) for n in graph.iter(NS + "node")}
    edges = set()
    for e in graph.iter(NS + "edge"):
        values = fields(e)
        edges.add((e.attrib["source"], e.attrib["target"], values["type"], values.get("name")))
    require(graph.find(NS + "graph").get("edgedefault") == "directed", "graph direction")
    require(sorted(map(len, paths)) == [2, 3], "expected argument and callee witnesses")
    argument, callee = sorted(paths, key=len)
    literal, result = argument
    module, method, returned = callee
    require(returned == result and len({literal, result, module, method}) == 4, "object identity")
    require(nodes[literal].get("code") == "demo.txt", "argument code")
    require(nodes[literal].get("trust_domain") == ":local:demo.txt", "argument domain")
    require(nodes[module].get("trust_domain") == "path", "module domain")
    require(nodes[method].get("name") == "path.basename", "callee name")
    require(nodes[result].get("obj_type") == "ObjTypes.APIRetVal", "return object")
    expected = {
        (literal, result, "CONTRIBUTES_TO", None),
        (module, method, "PARENT_TO_CHILD", "basename"),
        (method, result, "FUNC_OBJ_TO_RET_VAL", None),
    }
    require(expected <= edges, "missing directed witness edge or property")


def check(root, case):
    data = json.loads((root / "module-returns.json").read_text(encoding="utf-8"))
    for side in ("before", "after"):
        graph = ET.parse(root / f"{side}.graphml").getroot()
        relations = data[side]["relations"]
        if case == "top-level" and side == "after":
            require(len(relations) == 1 and relations[0][0] == [":local:demo", "path"], "relation")
            check_top_level(graph, relations[0][1])
        else:
            require(relations == [], f"unexpected {side} relation")
    expected = [[":local", "path"]] if case == "top-level" else []
    require(data["flagged_single_local_rels_from_tuples"] == expected, "version delta")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path)
    parser.add_argument("--case", choices=("function-body", "top-level"), default="top-level")
    args = parser.parse_args()
    folder = "top-level" if args.case == "top-level" else "results"
    check(args.directory or Path(__file__).parent / folder, args.case)
    print(f"{args.case} evidence verified")
