from dcfa.program_flow import analyze


def snapshot(root, source):
    (root / "SKILL.md").write_text("synthetic")
    (root / "main.py").write_text(source)
    return analyze(root, "main.py")


def test_local_arguments_returns_alias_and_overwrite(tmp_path):
    (tmp_path / "helper.py").write_text("def pick(first, second):\n return second\n")
    result = snapshot(
        tmp_path,
        "from helper import pick\nimport tools\na='old'\na='new'\n"
        "x=pick('unused',a)\ny=pick(a,'other')\ntools.send(x)\ntools.send(y)",
    )
    assert not result["issues"]
    nodes = result["nodes"]
    flows = [
        (nodes[e["source"]]["name"], nodes[e["target"]]["line"])
        for e in result["edges"]
        if e["kind"] == "data_flow" and nodes[e["source"]]["kind"] == "literal"
    ]
    assert flows == [("'new'", 7), ("'other'", 8)]
    assert any(n["file"] == "helper.py" for n in nodes)


def test_file_and_independent_external_call(tmp_path):
    result = snapshot(tmp_path, "import api\nf=open('demo')\nx=f.read()\napi.emit(x)")
    assert not result["issues"]
    nodes = result["nodes"]
    assert any(
        nodes[e["source"]]["domain"] == "file" and nodes[e["target"]]["domain"] == "import:api"
        for e in result["edges"]
    )


def test_unknown_and_syntax(tmp_path):
    for source, reason in [
        ("f()", "unresolved_Name"),
        ("x =", "parse_failure"),
        ("while True: pass", "unsupported_While"),
    ]:
        result = snapshot(tmp_path, source)
        assert result["status"] == "partial"
        assert result["issues"][0]["reason"] == reason
