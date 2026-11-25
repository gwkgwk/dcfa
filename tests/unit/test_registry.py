import json

import pytest

from dcfa.registry import InvalidRegistry, inspect_registry, validate

ENTRY = {
    "id": "synthetic",
    "paper": "synthetic paper identifier",
    "paper_version": "synthetic v1",
    "paper_sha256": "a" * 64,
    "repository": "synthetic repository",
    "commit": "b" * 40,
    "kind": "original",
}


def manifest(*entries):
    return json.dumps({"schema_version": 1, "sources": entries}).encode()


def test_valid():
    assert validate(manifest(ENTRY)) == 1


@pytest.mark.parametrize(
    "data",
    [
        b"null",
        b"broken",
        b"\xff",
        manifest({}),
        manifest(ENTRY, ENTRY),
        manifest(ENTRY | {"kind": "new"}),
        manifest(ENTRY | {"commit": "main"}),
        manifest(ENTRY | {"paper_sha256": "short"}),
    ],
)
def test_invalid(data):
    with pytest.raises(InvalidRegistry):
        validate(data)


def test_missing(tmp_path):
    assert inspect_registry(tmp_path / "missing")["error"] == "registry_io"
