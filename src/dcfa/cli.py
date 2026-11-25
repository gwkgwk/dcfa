"""Infrastructure-only command line interface."""

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
    parser.add_argument("command", choices=["check-sources", "record-run"])
    args = parser.parse_args(argv)
    logging.basicConfig(format="%(levelname)s %(name)s %(message)s", level=logging.INFO)
    logger = logging.getLogger("dcfa")
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
