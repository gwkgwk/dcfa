import pytest

from dcfa.program_flow import analyze


def run(root, code, files=None):
    (root / "SKILL.md").write_text("synthetic")
    for path, content in (files or {}).items():
        dest = root / path
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(content)
    (root / "main.py").write_text(code)
    return analyze(root, "main.py")


@pytest.mark.parametrize(
    "code",
    [
        "import pkg as p\na=p.emit\nb=p.emit\na('v')",
        "from pkg import emit as a, emit as b\nb('v')",
    ],
)
def test_member_identity_and_edge_rules(tmp_path, code):
    r = run(tmp_path, code)
    assert not r["issues"]
    (module,) = [n for n in r["nodes"] if n["kind"] == "module"]
    (api,) = [n for n in r["nodes"] if n["kind"] == "api"]
    (result,) = [n for n in r["nodes"] if n["kind"] == "result"]
    edges = {(e["source"], e["target"], e["kind"]) for e in r["edges"]}
    for kind in ("owns", "data_flow"):
        assert (module["id"], api["id"], kind) in edges
        assert (api["id"], result["id"], kind) in edges
    assert module["resolution"] == "unverified_external"


@pytest.mark.parametrize("method", ["h.read()", "reader()"])
def test_receiver_and_flow_path(tmp_path, method):
    r = run(
        tmp_path, f"import svc\nh=open('p')\nreader=h.read\nx={method}\nsvc.send(x)\nsvc.other('q')"
    )
    nodes = r["nodes"]
    (start,) = [n["id"] for n in nodes if n["name"] == "'p'"]
    reachable = {start}
    edges = [(e["source"], e["target"]) for e in r["edges"] if e["kind"] == "data_flow"]
    for _ in nodes:
        reachable.update(b for a, b in edges if a in reachable)
    assert {n["name"] for n in nodes if n["id"] in reachable and n["kind"] == "result"} == {
        "read",
        "send",
    }
    (handle,) = [n["id"] for n in nodes if n["kind"] == "file_handle"]
    (result,) = [n["id"] for n in nodes if n["kind"] == "result" and n["name"] == "read"]
    assert (handle, result) in edges


def test_package_and_library(tmp_path):
    r = run(tmp_path, "import abcde", {"abcde/__init__.py": ""})
    assert r["issues"][0]["reason"] == "unsupported_local_package"
    r = run(tmp_path, "import json")
    assert r["nodes"][0]["resolution"] == "stdlib_name_unverified"


@pytest.mark.parametrize(
    "code, reason",
    [
        ("def f(n): return open(n)\nf('v')", "unresolved_free_open"),
        ("def f(n): return f(n)\nf('v')", "unresolved_self_reference"),
        ("def f(g): return g(g)\nf(f)", "recursive_call"),
    ],
)
def test_scoped_uncertainty(tmp_path, code, reason):
    assert run(tmp_path, code)["issues"][0]["reason"] == reason


def test_docstring_definitions_and_initialization(tmp_path):
    code = "from h import p as alias\ndef local(x): return alias(x)\ny=alias('a')"
    r = run(tmp_path, code, {"h.py": "'doc'\ndef p(x): return x"})
    assert not r["issues"]
    assert {"local", "alias"} <= {b["name"] for b in r["bindings"] if b["role"] == "definition"}
    assert run(tmp_path, code, {"h.py": "x=1\ndef p(x): return x"})["status"] == "partial"


@pytest.mark.parametrize("noop", ["pass", "..."])
def test_scope_and_noop(tmp_path, noop):
    r = run(tmp_path, f"def unused(): return missing()\ndef called(): {noop}\ncalled()")
    assert r["status"] == "complete_in_subset"
    assert [f["name"] for f in r["unvisited_functions"]] == ["unused"]
    assert all(n["name"] != "Ellipsis" for n in r["nodes"])


def test_read_block(tmp_path):
    r = run(tmp_path, "x=1", {"other.py": " " * 40000})
    assert r["entry_analysis"] == "not_started"
    assert "byte_limit" in {i["reason"] for i in r["issues"]}
