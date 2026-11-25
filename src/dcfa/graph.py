"""Evidence-constrained graph projection of one p03.2 summary."""

import ast
import json
from collections import defaultdict
from copy import deepcopy

from . import scs

TYPES = {
    "effects": "effect",
    "context_exposure": "context",
    "trust_boundaries": "trust_boundary",
}
RELATIONS = {
    "input_port": "reads",
    "output_port": "produces",
    "effect": "may_cause",
    "context": "exposes",
    "trust_boundary": "crosses-boundary",
}


def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)


def payload(claim):
    return {key: value for key, value in claim.items() if key != "evidence"}


def instruction_facts(snippet):
    """Replay the same P03 grammar, on exactly one anchored line."""
    facts = {key: [] for key in scs.GROUPS}
    if "\n" not in snippet:
        material = scs.Material("", snippet, facts, lambda *_: None)
        material.document(frontmatter=False)
    return {group: [payload(claim) for claim in claims] for group, claims in facts.items()}


def nested_operands(snippet, records):
    """Return direct call/argument pairs only after a full per-line reconciliation."""
    if len(snippet) > 2048 or "\n" in snippet:
        return None
    source = snippet.strip()
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        return None
    calls = sorted(
        (n for n in ast.walk(tree) if isinstance(n, ast.Call)),
        key=lambda n: (n.lineno, n.col_offset, n.end_lineno, n.end_col_offset),
    )
    if len(calls) != len(records):
        return None
    locations = {}
    for call, (ref, claim) in zip(calls, records, strict=True):
        target = call.func
        names = []
        while isinstance(target, ast.Attribute):
            names.append(target.attr)
            target = target.value
        args = [ast.get_source_segment(source, arg) for arg in (*call.args, *call.keywords)]
        if (
            not isinstance(target, ast.Name)
            or ".".join([target.id, *reversed(names)]) != claim["name"]
            or args != claim["parameters"]
        ):
            return None
        locations[call] = ref
    pairs = []
    for parent in calls:
        values = [*parent.args, *(kw.value for kw in parent.keywords if kw.arg is not None)]
        # Expanded keyword mappings have a different binding contract.
        if any(kw.arg is None for kw in parent.keywords):
            continue
        for i, value in enumerate(values):
            if value in locations:
                pairs.append((locations[value], locations[parent] + f"/arg{i}"))
    return pairs


def build_graph(summary, bindings=None):
    scs.validate(summary)
    summary = deepcopy(summary)
    bindings = [] if bindings is None else deepcopy(bindings)
    if not isinstance(bindings, list):
        raise ValueError("bindings must be a list")
    tools = {}
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict) or set(binding) != {
            "operation",
            "callee",
            "tool",
            "basis",
        }:
            raise ValueError("invalid binding fields")
        slot = binding["operation"]
        if type(slot) is not int or not 0 <= slot < len(summary["operations"]) or slot in tools:
            raise ValueError("invalid or duplicate operation index")
        op = summary["operations"][slot]
        if (
            op["kind"] != "call_expression"
            or op["name"] != binding["callee"]
            or not all(
                isinstance(binding[k], str) and binding[k].strip() for k in ("tool", "basis")
            )
        ):
            raise ValueError("binding lacks support for the specified call")
        tools[slot] = (index, binding)

    nodes = []
    edges = []
    gaps = []
    groups = defaultdict(list)
    call_lines = defaultdict(list)
    kinds = {}
    refs = {}
    paths = set()

    def edge(src, relation, dst, certainty):
        edges.append(
            dict(
                source=src,
                relation=relation,
                target=dst,
                certainty=certainty,
                evidence=list(dict.fromkeys([refs[src], refs[dst]])),
            )
        )

    def node(key, kind, label, ref, parent="skill"):
        refs[key] = ref
        kinds[key] = kind
        nodes.append(dict(id=key, kind=kind, label=label, evidence=ref))
        if parent:
            edge(parent, "contains", key, "static")
        return key

    def gap(subject, reason, ref):
        gaps.append(dict(subject=subject, reason=reason, evidence=ref))

    node("skill", "skill", "Skill", "/scs", None)
    for index, entry in enumerate(summary["files"]):
        ref = f"/scs/files/{index}"
        if entry["path"] in paths:
            raise ValueError("duplicate inventory path")
        paths.add(entry["path"])
        node(ref, "resource" if entry["role"] == "resource" else "file", entry["path"], ref)
        if entry["role"] == "resource":
            gap(ref, "resource_usage_unresolved", ref)

    for group in scs.GROUPS:
        for index, claim in enumerate(summary[group]):
            ref = f"/scs/{group}/{index}"
            ev = claim["evidence"]
            if ev["path"] not in paths or ev["end_line"] < ev["start_line"]:
                raise ValueError("untraceable SCS claim")
            if group == "ports":
                kind = claim["direction"] + "_port"
                label = claim["data_type"] or "unknown type"
            elif group == "operations":
                kind, label = claim["kind"], claim["name"]
            else:
                kind = TYPES[group]
                label = (
                    claim.get("name")
                    or claim.get("scope")
                    or (claim["source"] + " → " + claim["destination"])
                )
            node(ref, kind, label, ref)
            if ev["method"] == "instruction":
                anchor = (ev["path"], ev["start_line"], ev["end_line"], ev["snippet"])
                groups[anchor].append((group, ref, payload(claim)))
            elif kind != "call_expression":
                gap(ref, "semantic_link_unresolved", ref)

            if kind == "instruction_action":
                text = node(ref + "/text", "instruction", ev["snippet"], ref + "/evidence")
                edge(text, "describes", ref, "possible")
            elif kind == "call_expression":
                call_lines[(ev["path"], ev["start_line"], ev["end_line"], ev["snippet"])].append(
                    (ref, claim)
                )
                operands = [
                    (f"arg{n}", arg, f"{ref}/parameters/{n}")
                    for n, arg in enumerate(claim["parameters"] or [])
                ]
                if "." in label:
                    operands.append(("receiver", label.rsplit(".", 1)[0], ref + "/name"))
                for slot_name, expr, basis in operands:
                    operand = node(ref + "/" + slot_name, "data_expression", expr, basis, ref)
                    edge(operand, "operand", ref, "static")
                if index in tools:
                    pos, binding = tools[index]
                    tool = node(ref + "/tool", "tool", binding["tool"], f"/bindings/{pos}")
                    edge(ref, "may_invoke", tool, "possible")
                else:
                    gap(ref, "tool_binding_unresolved", ref)

    for (_, start, end, snippet), records in call_lines.items():
        pairs = nested_operands(snippet, records) if start == end else None
        if pairs is None:
            for ref, _ in records:
                gap(ref, "local_value_flow_unresolved", ref)
        else:
            for producer, operand in pairs:
                edge(producer, "result_to_operand", operand, "possible")

    for (_, start, end, snippet), members in groups.items():
        facts = instruction_facts(snippet) if start == end else {}
        actions = [
            ref
            for group, ref, fact in members
            if group == "operations" and fact in facts.get(group, [])
        ]
        for group, ref, fact in members:
            if len(actions) != 1 or fact not in facts.get(group, []):
                gap(ref, "instruction_role_unresolved", ref)
                continue
            if group == "operations":
                continue
            action = actions[0]
            if kinds[ref] == "input_port":
                edge(ref, "reads", action, "possible")
            else:
                edge(action, RELATIONS[kinds[ref]], ref, "possible")

    for index, diagnostic in enumerate(summary["diagnostics"]):
        gap("skill", diagnostic["reason"], f"/scs/diagnostics/{index}")
    return dict(
        schema_version="p04.1",
        scs=summary,
        bindings=bindings,
        nodes=nodes,
        edges=edges,
        unknowns=gaps,
        runtime_observation="none",
    )


def validate_graph(graph):
    """Check a closed projection, including endpoint types, evidence and missing edges."""
    if not isinstance(graph, dict) or not {"scs", "bindings"} <= graph.keys():
        raise ValueError("missing graph inputs")
    expected = build_graph(graph["scs"], graph["bindings"])
    if canonical(expected) != canonical(graph):
        raise ValueError("graph differs from its evidence-constrained projection")


def graph_json(graph):
    validate_graph(graph)
    return json.dumps(graph, indent=2, ensure_ascii=True, allow_nan=False)


def graph_dot(graph):
    validate_graph(graph)
    ids = {n["id"]: f"n{i}" for i, n in enumerate(graph["nodes"])}
    lines = ["digraph Skill {", "  rankdir=LR;"]
    for node in graph["nodes"]:
        label = json.dumps(node["kind"] + "\n" + node["label"], ensure_ascii=False)
        lines.append(f"  {ids[node['id']]} [label={label}];")
    for edge in graph["edges"]:
        style = "dashed" if edge["certainty"] == "possible" else "solid"
        lines.append(
            f"  {ids[edge['source']]} -> {ids[edge['target']]} "
            f'[label="{edge["relation"]}", style={style}];'
        )
    for i, gap in enumerate(graph["unknowns"]):
        label = json.dumps("unknown: " + gap["reason"], ensure_ascii=False)
        lines.append(f"  u{i} [label={label}, shape=note];")
        lines.append(f"  {ids[gap['subject']]} -> u{i} [style=dotted, arrowhead=none];")
    return "\n".join([*lines, "}"])
