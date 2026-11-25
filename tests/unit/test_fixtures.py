import pytest


def test_registered(synthetic_bytes):
    assert b'"sources": []' in synthetic_bytes("empty-registry.json")


@pytest.mark.parametrize("name", ["../outside", "unknown.json", "C:/external.json"])
def test_unregistered(synthetic_bytes, name):
    with pytest.raises(ValueError):
        synthetic_bytes(name)
