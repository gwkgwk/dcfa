"""Persist one completed infrastructure check per unique directory."""

import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4


def record(root: Path, result: dict) -> Path:
    run_id = uuid4().hex
    directory = root / run_id
    directory.mkdir(parents=True)
    pending = directory / "record.tmp"
    destination = directory / "record.json"
    payload = {
        "schema_version": 1,
        "stage": "P00",
        "operation": "registry-check",
        "run_id": run_id,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "project_version": version("dcfa"),
        "input": "third_party/sources.json",
        "result": result,
    }
    try:
        pending.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        pending.replace(destination)
    except OSError:
        pending.unlink(missing_ok=True)
        directory.rmdir()
        raise
    return destination
