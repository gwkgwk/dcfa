"""Publish a GraphML copy with its synthetic input entry relative to the pair."""

from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://graphml.graphdrawing.org/xmlns}"


def localize_entry(graph: Path, pair: Path, entry: Path) -> None:
    relative = entry.relative_to(pair).as_posix()
    tree = ET.parse(graph)
    changed = False
    for field in tree.iter(NS + "data"):
        if field.text in (str(entry), entry.as_posix()):
            field.text = relative
            changed = True
    if changed:
        ET.register_namespace("", NS[1:-1])
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        tree.write(graph, encoding="utf-8", xml_declaration=True)
