"""DCFA command line interface."""

import argparse
import json
import logging
from importlib.metadata import version
from pathlib import Path

from .registry import inspect_registry
from .runs import record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dcfa")
    parser.add_argument("--version", action="version", version=version("dcfa"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-sources")
    commands.add_parser("record-run")
    graph = commands.add_parser("graph", help="Build a single Skill graph from p03.2 JSON")
    graph.add_argument("summary", type=Path)
    graph.add_argument("--bindings", type=Path)
    graph.add_argument("--format", choices=("json", "dot"), default="json")
    commands.add_parser("scs", help="Summarize one isolated local Skill snapshot").add_argument(
        "directory", type=Path
    )
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s %(name)s %(message)s", level=logging.INFO)
    logger = logging.getLogger("dcfa")
    if args.command == "graph":
        from fastjsonschema import JsonSchemaException

        from .graph import build_graph, graph_dot, graph_json

        try:
            summary = json.loads(args.summary.read_text(encoding="utf-8-sig"))
            bindings = (
                json.loads(args.bindings.read_text(encoding="utf-8-sig")) if args.bindings else []
            )
            result = build_graph(summary, bindings)
            print(graph_dot(result) if args.format == "dot" else graph_json(result))
        except (JsonSchemaException, OSError, ValueError, RecursionError) as exc:
            logger.error("graph input or export failed (%s)", type(exc).__name__)
            return 1
        return 0
    if args.command == "scs":
        from fastjsonschema import JsonSchemaException

        from .scs import extract, validate

        try:
            summary = extract(args.directory)
            validate(summary)
        except (JsonSchemaException, OSError, ValueError):
            print(json.dumps({"status": "failed", "error": "scs_contract_failure"}))
            return 1
        print(json.dumps(summary, indent=2))
        logger.info("scs %s", summary["status"])
        return 0 if summary["status"] == "complete" else 1
    result = inspect_registry(Path("third_party/sources.json"))
    output = dict(result)
    if args.command == "record-run":
        try:
            output["record"] = str(record(Path("runs"), result))
        except OSError:
            output.update(status="failed", error="record_io", check_result=result)
    ok = output["status"] == "ok"
    logger.log(logging.INFO if ok else logging.ERROR, "%s %s", args.command, output["status"])
    print(json.dumps(output))
    return 0 if ok else 1
