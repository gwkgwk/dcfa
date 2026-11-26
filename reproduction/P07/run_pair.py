"""Invoke the upstream pair runner on a reviewed synthetic pair in a fresh directory."""

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

parser = ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
parser.add_argument("pair", type=Path)
parser.add_argument("--case", choices=("top-level", "function-body"), default="top-level")
args = parser.parse_args()
source, pair = args.source.resolve(), args.pair.resolve()
inputs = Path(__file__).resolve().parent / "inputs" / args.case
pair.mkdir(parents=True, exist_ok=False)
folders = []
for version in ("1.0.0", "1.1.0"):
    folder = pair / f"sample-{version}"
    folder.mkdir()
    manifest = {"name": "sample", "version": version, "main": "index.js"}
    (folder / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "index.js").write_bytes((inputs / f"{version}.js").read_bytes())
    folders.append(folder)

sys.path.insert(0, str(source))
from rogue_one_runner import process_package_pair_given_names  # noqa: E402

args = Namespace(fast=False, log_level="WARNING", raise_all=True, save_odrg=True)
result = process_package_pair_given_names(
    str(pair), pair, *folders, "sample", "1.0.0", "1.1.0", print, args
)
if result["error"] != "OK":
    raise SystemExit(1)
