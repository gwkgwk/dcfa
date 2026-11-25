import json

from dcfa.runs import record


def test_unique_complete_records(tmp_path):
    result = {"status": "failed", "error": "registry_io", "source_sha256": None}
    paths = [record(tmp_path, result) for _ in range(2)]
    assert paths[0] != paths[1]
    for path in paths:
        data = json.loads(path.read_text())
        assert data["run_id"] == path.parent.name
        assert data["stage"] == "P00"
        assert data["result"] == result
        assert list(path.parent.iterdir()) == [path]
