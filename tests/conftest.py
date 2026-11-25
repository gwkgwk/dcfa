from pathlib import Path

import pytest

SYNTHETIC = Path(__file__).resolve().parent / "fixtures" / "synthetic"
REGISTERED = frozenset({"empty-registry.json"})


@pytest.fixture
def synthetic_bytes():
    def read(name):
        if name not in REGISTERED:
            raise ValueError("unregistered fixture")
        path = SYNTHETIC / name
        if path.resolve() != path:
            raise ValueError("redirected fixture")
        return path.read_bytes()

    return read
