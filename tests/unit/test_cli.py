import json
import logging
from pathlib import Path

from dcfa.cli import main


def test_check(monkeypatch, tmp_path, synthetic_bytes, capsys, caplog):
    monkeypatch.chdir(tmp_path)
    Path("third_party").mkdir()
    Path("third_party/sources.json").write_bytes(synthetic_bytes("empty-registry.json"))
    with caplog.at_level(logging.INFO):
        assert main(["check-sources"]) == 0
    assert "check-sources ok" in caplog.text
    assert json.loads(capsys.readouterr().out)["count"] == 0


def test_failed_check_recorded(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["record-run"]) == 1
    output = json.loads(capsys.readouterr().out)
    assert json.loads(Path(output["record"]).read_text())["result"]["error"] == "registry_io"


def test_record_io(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    Path("runs").touch()
    assert main(["record-run"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "record_io"
