"""Finite mathematical checks for P11 prose, independent of all DCFA modules."""

from itertools import product
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"
SPEC = (DOCS / "algorithm_spec.md").read_text(encoding="utf-8-sig")
PROBLEM = (DOCS / "research_problem.md").read_text(encoding="utf-8-sig")


def test_gate_claim_and_exact_examples():
    assert "整体标签为「引入」" in PROBLEM
    rows = {line for line in SPEC.splitlines() if line.startswith("|")}
    for label, old, new in (
        ("引入", "∅", "{b}"),
        ("消除", "{a}", "∅"),
        ("范围扩大", "{a}", "{a,b}"),
        ("范围缩小", "{a,b}", "{b}"),
        ("混合", "{a}", "{b}"),
        ("保持", "{a}", "{a}"),
    ):
        assert any(
            line.startswith(f"|{label}|") and line.endswith(f"|{old}|{new}|") for line in rows
        )


def test_comparison_preconditions():
    assert "解释族为空时返回证据冲突，不计算界" in SPEC
    assert "逐键观察等价证书" in SPEC
    assert "部分界不能唯一决定整体标签" in SPEC


def test_finite_bounds_against_all_completions():
    # Independent concrete worlds over three context atoms; bit positions denote membership.
    sets = range(8)
    intervals = [
        (low, high, [w for w in sets if low & w == low and w & high == w])
        for low, high in product(sets, repeat=2)
        if low & high == low
    ]
    for (l1, u1, old), (l2, u2, new) in product(intervals, repeat=2):
        for op, bounds in (
            (lambda x, y: y & ~x, (l2 & ~u1, u2 & ~l1)),
            (lambda x, y: x & ~y, (l1 & ~u2, u1 & ~l2)),
            (lambda x, y: x & y, (l1 & l2, u1 & u2)),
        ):
            lower, upper = 7, 0
            for x, y in product(old, new):
                actual = op(x, y)
                lower &= actual
                upper |= actual
            assert (lower, upper) == bounds


def test_exact_relations_partition_and_uncertain_gate():
    def labels(x, y):
        cases = {
            "引入": x == 0 and y != 0,
            "消除": x != 0 and y == 0,
            "范围扩大": x != 0 and x != y and x & y == x,
            "范围缩小": y != 0 and x != y and x & y == y,
            "混合": bool(x & ~y) and bool(y & ~x),
            "保持": x == y,
        }
        return {name for name, applies in cases.items() if applies}

    for x, y in product(range(8), repeat=2):
        assert len(labels(x, y)) == 1
    assert labels(0, 2) == {"引入"}
    assert labels(1, 3) == {"范围扩大"}
    assert labels(3, 1) == {"范围缩小"}
    assert labels(2, 0) == {"消除"}
    assert labels(0, 0) == labels(2, 2) == {"保持"}
    assert labels(1, 2) == {"混合"}
    assert set.union(*(labels(x, 2) for x in range(4))) == {"引入", "混合", "保持", "范围缩小"}
