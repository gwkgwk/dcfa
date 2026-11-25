"""Invoke the upstream pair runner on a reviewed synthetic pair in a fresh directory."""

import json
import sys
from argparse import Namespace
from pathlib import Path

source, pair = (Path(arg).resolve() for arg in sys.argv[1:])
pair.mkdir(parents=True, exist_ok=False)
folders = []
for version, code in [
    ("1.0.0", "module.exports = 'demo.txt';"),
    ("1.1.0", "const path = require('path');\nmodule.exports = path.basename('demo.txt');"),
]:
    folder = pair / f"sample-{version}"
    folder.mkdir()
    manifest = {"name": "sample", "version": version, "main": "index.js"}
    (folder / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    (folder / "index.js").write_text(code + "\n", encoding="utf-8")
    folders.append(folder)

sys.path.insert(0, str(source))
from rogue_one_runner import process_package_pair_given_names  # noqa: E402

args = Namespace(fast=False, log_level="WARNING", raise_all=True, save_odrg=True)
result = process_package_pair_given_names(
    str(pair), pair, *folders, "sample", "1.0.0", "1.1.0", print, args
)
if result["error"] != "OK":
    raise SystemExit(1)
