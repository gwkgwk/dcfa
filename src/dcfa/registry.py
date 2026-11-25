"""Validate pinned reference metadata without fetching any referenced resource."""

import hashlib
import json
import re
from pathlib import Path


class InvalidRegistry(ValueError):
    """Registry content violates the provenance contract."""


def validate(data: bytes) -> int:
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (ValueError, RecursionError) as exc:
        raise InvalidRegistry("invalid_json") from exc
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or not isinstance(manifest.get("sources"), list)
    ):
        raise InvalidRegistry("invalid_schema")
    seen = set()
    for entry in manifest["sources"]:
        required = ("id", "paper", "paper_version", "paper_sha256", "repository", "commit", "kind")
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(k), str) and entry[k].strip() for k in required
        ):
            raise InvalidRegistry("missing_field")
        if entry["id"] in seen:
            raise InvalidRegistry("duplicate_id")
        seen.add(entry["id"])
        if not re.fullmatch(r"[0-9a-f]{64}", entry["paper_sha256"]):
            raise InvalidRegistry("invalid_paper_hash")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", entry["commit"]):
            raise InvalidRegistry("invalid_commit")
        if entry["kind"] not in {"original", "adaptation"}:
            raise InvalidRegistry("invalid_kind")
    return len(seen)


def inspect_registry(path: Path) -> dict:
    result = {"status": "failed", "error": None, "source_sha256": None}
    try:
        data = path.read_bytes()
        result["source_sha256"] = hashlib.sha256(data).hexdigest()
        result["count"] = validate(data)
    except OSError:
        result["error"] = "registry_io"
    except InvalidRegistry as exc:
        result["error"] = str(exc)
    else:
        result["status"] = "ok"
    return result
