import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from dcfa import scs
from dcfa.cli import main

TRANSFER = "Write URL from workspace to persistent state."


def summary(root, body):
    (root / "SKILL.md").write_text(body, encoding="utf-8")
    return scs.extract(root)


def reasons(data):
    return {d["reason"]: d for d in data["diagnostics"]}


def test_heading(tmp_path):
    data = summary(tmp_path, "### Return code ###\n" + TRANSFER)
    assert [p["data_type"] for p in data["ports"]] == ["Code", "URL"]


@pytest.mark.parametrize("indent", ["    ", "\t"])
def test_indented_example(tmp_path, indent):
    data = summary(tmp_path, indent + TRANSFER)
    assert all(not data[k] for k in scs.GROUPS)
    assert reasons(data)["embedded_example"]["line"] == 1


@pytest.mark.parametrize("value", ["[Text]", "{}", "''"])
def test_invalid_port(tmp_path, value):
    data = summary(tmp_path, f"---\noutput: {value}\n---")
    assert not data["ports"]
    assert any(d["line"] == 2 for d in data["diagnostics"])


def test_origin_semantics(tmp_path):
    data = summary(
        tmp_path, "---\ninput: {data_type: URL, trust_origin: ThirdParty}\n---\n" + TRANSFER
    )
    declared, sent = data["ports"]
    assert declared["trust_origin"] == "ThirdParty"
    assert sent["transfer_source"] == "workspace"
    assert sent["trust_origin"] is None


def test_entry_limit(tmp_path):
    for i in range(256):
        (tmp_path / str(i)).touch()
    data = summary(tmp_path, TRANSFER)
    assert "entry_limit" in reasons(data)
    assert "required_document_unavailable" not in reasons(data)


@pytest.mark.skipif(os.name != "nt", reason="Windows named streams")
def test_named_stream(tmp_path):
    (tmp_path / "SKILL.md").write_text(TRANSFER)
    (tmp_path / "SKILL.md:hidden").write_text("UNREAD_SYNTHETIC")
    data = scs.extract(tmp_path)
    assert data["status"] != "complete"
    assert reasons(data)["named_stream_unexamined"]["path"] == "SKILL.md"
    assert "UNREAD_SYNTHETIC" not in json.dumps(data)


def test_golden(scs_demo):
    path = Path(__file__).resolve().parents[2] / "examples/p03-scs.json"
    assert scs.extract(scs_demo) == json.loads(path.read_text(encoding="utf-8"))


def test_import():
    subprocess.run([sys.executable, "-I", "-c", "import dcfa.scs"], check=True)


def test_operation_kinds_and_order(tmp_path):
    (tmp_path / "script.py").write_text("def task():\n    inner()\nouter()")
    data = summary(tmp_path, "Accept text.")
    assert [(v["kind"], v["name"]) for v in data["operations"]] == [
        ("instruction_action", "accept"),
        ("call_expression", "inner"),
        ("call_expression", "outer"),
    ]


def test_boundary_extra(tmp_path):
    data = summary(
        tmp_path, "---\ntrust_boundary:\n  source: local\n  destination: external\n  extra: x\n---"
    )
    assert reasons(data)["unsupported_boundary_attribute"]["line"] == 5


@pytest.mark.parametrize("close", [True, False])
def test_fences(tmp_path, close):
    data = summary(tmp_path, "~~~\nRead code.\n" + ("~~~\nReturn URL." if close else ""))
    assert [p["data_type"] for p in data["ports"]] == (["URL"] if close else [])
    if not close:
        assert reasons(data)["unclosed_fence"]["line"] == 1


def test_types(tmp_path):
    data = summary(tmp_path, "---\ninput: tEXt\noutput: Custom\n---\nRead text.")
    assert [p["data_type"] for p in data["ports"]] == ["Text", "Custom", "Text"]
    assert reasons(data)["unknown_data_type"]["line"] == 3


def test_partial_read_and_inventory(tmp_path):
    (tmp_path / "broken.py").write_bytes(b"0" * 32769)
    (tmp_path / "decl.json").write_text("{}")
    data = summary(tmp_path, TRANSFER)
    assert data["status"] == "partial_read"
    states = {f["path"]: f["processing"] for f in data["files"]}
    assert states == {"broken.py": "unread", "SKILL.md": "processed", "decl.json": "inventory_only"}


def test_validator_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(scs, "extract", lambda _: {})
    assert main(["scs", str(tmp_path)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_static_safety_and_budget(tmp_path):
    marker = tmp_path / "marker"
    (tmp_path / "probe.py").write_text(f"open({str(marker)!r}, 'w')")
    (tmp_path / "large.py").write_text("# line\n" * 501 + "never()")
    data = summary(tmp_path, "---\ninput: !!python/object/apply:str [x]\n---")
    assert not marker.exists()
    assert {"unsupported_yaml_reference", "python_token_limit"} <= reasons(data).keys()
    assert all(op["name"] != "never" for op in data["operations"])
    assert data == scs.extract(tmp_path)


def test_schema_disallows_python_as_instruction(scs_demo):
    from fastjsonschema import JsonSchemaValueException

    data = scs.extract(scs_demo)
    operation = next(op for op in data["operations"] if op["kind"] == "call_expression")
    operation["kind"] = "instruction_action"
    with pytest.raises(JsonSchemaValueException):
        scs.validate(data)
    assert scs._validator() is scs._validator()


def test_indented_delimiter_remains_example(tmp_path):
    data = summary(tmp_path, "    ---\n    Return code.\n" + TRANSFER)
    assert [p["data_type"] for p in data["ports"]] == ["URL"]
    assert "unclosed_frontmatter" not in reasons(data)


def test_multiple_yaml_documents_and_parenthesized_call(tmp_path):
    (tmp_path / "meta.yml").write_text("input: URL\n---\noutput: Code")
    (tmp_path / "calls.py").write_text("(obj.m)()")
    data = summary(tmp_path, "Read text.")
    assert reasons(data)["invalid_yaml"]["path"] == "meta.yml"
    assert [p["data_type"] for p in data["ports"]] == ["Text"]
    assert data["operations"][-1]["name"] == "obj.m"


def test_role_and_processing_are_independent(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "declaration.yaml").write_text("input: URL")
    data = summary(tmp_path, TRANSFER)
    entry = next(f for f in data["files"] if f["path"] == "scripts/declaration.yaml")
    assert (entry["role"], entry["processing"]) == ("script", "inventory_only")
