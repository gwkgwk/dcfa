import json

import pytest
from fastjsonschema import JsonSchemaValueException as ValidationError

from dcfa.cli import main
from dcfa.scs import extract, validate


def test_demo_evidence_and_unknowns(scs_demo):
    result = extract(scs_demo)
    assert result["status"] == "partial"
    assert result["ports"][0]["sensitivity"] == "Private"
    assert result["ports"][1]["sensitivity"] is None
    assert result["effects"][0]["requires_authorization"] is True
    assert result["trust_boundaries"][0]["destination"] == "persistent state"
    assert result["context_exposure"][0]["scope"] == "workspace"
    for group in ("ports", "effects", "operations", "trust_boundaries", "context_exposure"):
        for claim in result[group]:
            ev = claim["evidence"]
            lines = (scs_demo / ev["path"]).read_text(encoding="utf-8").splitlines()
            assert ev["snippet"] == "\n".join(lines[ev["start_line"] - 1 : ev["end_line"]])
    assert {op["name"] for op in result["operations"]} == {"accept", "return", "value.strip"}
    assert any(d["reason"] == "uninterpreted_instruction" for d in result["diagnostics"])


@pytest.mark.parametrize(
    "source,reason",
    [
        ("---\ninput: [\n---", "invalid_yaml"),
        ("---\ninput: &x hello\n---", "unsupported_yaml_reference"),
        ("---\ninput: Text\ninput: URL\n---", "ambiguous_yaml_keys"),
        ("---\nname: x", "unclosed_frontmatter"),
    ],
)
def test_parse_failure(tmp_path, source, reason):
    (tmp_path / "SKILL.md").write_text(source)
    result = extract(tmp_path)
    assert result["status"] != "complete"
    assert any(
        d["reason"] == reason and d["state"] == "parse_failure" for d in result["diagnostics"]
    )


def test_code_is_static(tmp_path):
    (tmp_path / "SKILL.md").write_text("Do not return text.")
    (tmp_path / "meta.yml").write_text("output: URL")
    (tmp_path / "broken.py").write_text("def broken(")
    (tmp_path / "sample.py").write_text("raise RuntimeError('synthetic')\nf(x, y=4)")
    result = extract(tmp_path)
    assert len(result["ports"]) == 1
    assert result["ports"][0]["evidence"]["path"] == "meta.yml"
    assert result["operations"][-1]["parameters"] == ["x", "y=4"]
    assert any(d["reason"] == "invalid_python" for d in result["diagnostics"])


def test_required_document_and_schema(tmp_path):
    result = extract(tmp_path)
    assert result["status"] == "failed"
    result["ports"] = [{"direction": "input"}]
    with pytest.raises(ValidationError):
        validate(result)


def test_cli(capsys, scs_demo):
    assert main(["scs", str(scs_demo)]) == 1
    assert json.loads(capsys.readouterr().out) == extract(scs_demo)


def test_transfer_instruction(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        "Send text from local to external after explicit authorization."
    )
    result = extract(tmp_path)
    assert result["status"] == "complete"
    assert result["effects"][0]["requires_authorization"] is True
    assert result["ports"][0]["trust_origin"] is None
