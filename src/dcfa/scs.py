"""Single-skill, evidence-bearing summary of static declarations and Python syntax."""

import ast
import json
import re
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

import fastjsonschema
import yaml
from yaml.nodes import MappingNode, ScalarNode

from .skill_reader import scan

GROUPS = ("ports", "effects", "operations", "context_exposure", "trust_boundaries")
TYPES = {"text": "Text", "url": "URL", "code": "Code", "command": "Command"}
PORT_ATTRS = ("sensitivity", "trust_origin", "exposure_scope", "consumability")
FLAGS = ("preserves_sensitivity", "crosses_boundary", "requires_authorization")


@lru_cache(maxsize=1)
def _validator():
    schema = json.loads(files("dcfa").joinpath("scs.schema.json").read_text(encoding="utf-8"))
    return fastjsonschema.compile(schema)


def validate(summary):
    """Raise fastjsonschema.JsonSchemaValueException on an invalid SCS."""
    _validator()(summary)


class Material:
    def __init__(self, path, text, summary, issue):
        self.path = path
        self.lines = text.split("\n")
        self.summary = summary
        self.issue = issue

    def add(self, group, fields, start, end, method):
        if group == "operations":
            fields["kind"] = "call_expression" if method == "python_ast" else "instruction_action"
        snippet = "\n".join(self.lines[start - 1 : end])
        if not snippet.strip() or len(snippet) > 2048:
            self.issue("missing_evidence", "snippet_unavailable_or_too_long", self.path, start)
            return
        evidence = dict(
            path=self.path,
            start_line=start,
            end_line=end,
            snippet=snippet,
            method=method,
            confidence=0.5 if method == "instruction" else 1.0,
        )
        self.summary[group].append({**fields, "evidence": evidence})

    def port(self, direction, data_type, attrs, start, end, method):
        self.add(
            "ports",
            {
                "direction": direction,
                "data_type": data_type,
                "transfer_source": attrs.get("transfer_source"),
                **{k: attrs.get(k) for k in PORT_ATTRS},
            },
            start,
            end,
            method,
        )

    def metadata(self, lines, offset):
        # Compose nodes only. Reject anchors, aliases and explicit tags before composition.
        source = "\n".join(lines)
        try:
            for token in yaml.scan(source, Loader=yaml.BaseLoader):
                if isinstance(token, (yaml.AnchorToken, yaml.AliasToken, yaml.TagToken)):
                    self.issue(
                        "parse_failure",
                        "unsupported_yaml_reference",
                        self.path,
                        offset + token.start_mark.line + 1,
                    )
                    return
            node = yaml.compose(source, Loader=yaml.BaseLoader)
        except (yaml.YAMLError, RecursionError) as exc:
            mark = getattr(exc, "problem_mark", None)
            self.issue(
                "parse_failure", "invalid_yaml", self.path, offset + (mark.line if mark else 0) + 1
            )
            return
        if not isinstance(node, MappingNode):
            self.issue("parse_failure", "expected_mapping", self.path, offset + 1)
            return
        keys = [k.value for k, _ in node.value if isinstance(k, ScalarNode)]
        if len(keys) != len(node.value) or len(set(keys)) != len(keys):
            self.issue("parse_failure", "ambiguous_yaml_keys", self.path, offset + 1)
            return
        for key, value in node.value:
            name = key.value
            start = offset + key.start_mark.line + 1
            end = offset + value.end_mark.line + bool(value.end_mark.column)
            end = max(start, end)
            attrs = {}
            if isinstance(value, MappingNode):
                for k, v in value.value:
                    if not (
                        isinstance(k, ScalarNode)
                        and isinstance(v, ScalarNode)
                        and k.value not in attrs
                        and v.value.strip()
                    ):
                        self.issue("parse_failure", "ambiguous_declaration", self.path, start)
                        break
                    attrs[k.value] = v.value
                    if name == "trust_boundary" and k.value not in {"source", "destination"}:
                        self.issue(
                            "unknown",
                            "unsupported_boundary_attribute",
                            self.path,
                            offset + k.start_mark.line + 1,
                        )
                else:
                    self.declaration(name, attrs, None, start, end)
                continue
            scalar = value.value.strip() if isinstance(value, ScalarNode) else None
            self.declaration(name, attrs, scalar, start, end)

    def declaration(self, name, attrs, scalar, start, end):
        if name in {"input", "output"}:
            dtype = scalar or attrs.get("data_type")
            if not dtype:
                self.issue("unknown", "incomplete_port_declaration", self.path, start)
                return
            canonical = TYPES.get(dtype.lower())
            if canonical is None:
                self.issue("unknown", "unknown_data_type", self.path, start)
            self.port(
                name,
                canonical or dtype,
                {k: attrs.get(k) for k in PORT_ATTRS},
                start,
                end,
                "frontmatter",
            )
            if attrs.keys() - {"data_type", *PORT_ATTRS}:
                self.issue("unknown", "unsupported_port_attribute", self.path, start)
        elif name == "effect" and (scalar or attrs.get("name")):
            flags = {k: {"true": True, "false": False}.get(attrs.get(k)) for k in FLAGS}
            self.add(
                "effects", {"name": scalar or attrs["name"], **flags}, start, end, "frontmatter"
            )
            if any(k in attrs and flags[k] is None for k in FLAGS) or attrs.keys() - {
                "name",
                *FLAGS,
            }:
                self.issue("unknown", "unsupported_effect_attribute", self.path, start)
        elif name == "context_exposure" and scalar:
            self.add("context_exposure", {"scope": scalar}, start, end, "frontmatter")
        elif name == "trust_boundary" and attrs.get("source") and attrs.get("destination"):
            self.add(
                "trust_boundaries",
                {k: attrs[k] for k in ("source", "destination")},
                start,
                end,
                "frontmatter",
            )
        elif name not in {"name", "version"}:
            self.issue("unknown", "uninterpreted_metadata", self.path, start)

    def document(self, frontmatter=True):
        offset = 0
        if frontmatter and self.lines[0].rstrip() == "---":
            closing = next(
                (
                    i
                    for i, line in enumerate(self.lines[1:], 1)
                    if line.strip() == "---" and not line.startswith((" ", "\t"))
                ),
                None,
            )
            if closing is None:
                self.issue("parse_failure", "unclosed_frontmatter", self.path, 1)
                return
            self.metadata(self.lines[1:closing], 1)
            offset = closing + 1
        fenced = None
        opening_line = None
        for number, line in enumerate(self.lines[offset:], offset + 1):
            stripped = line.strip()
            if line.expandtabs(4).startswith("    "):
                if stripped and not fenced:
                    self.issue("unknown", "embedded_example", self.path, number)
                continue
            fence = re.match(r"^(`{3,}|~{3,})", stripped)
            if fence:
                if fenced is None:
                    fenced = fence[1]
                    opening_line = number
                    self.issue("unknown", "embedded_example", self.path, number)
                elif stripped.startswith(fenced) and not stripped.strip(fenced[0]):
                    fenced = None
                continue
            if fenced or not stripped:
                continue
            stripped = re.sub(r"^#{1,6}(?:[ \t]+|$)", "", stripped)
            if stripped != line.strip():
                stripped = re.sub(r"[ \t]+#+$", "", stripped)
            transfer = re.fullmatch(
                r"(?:[-*] )?(send|write) (text|url|code|command) from "
                r"(local|workspace) to (external|persistent state)"
                r"( after explicit authorization)?\.?",
                stripped,
                re.I,
            )
            if transfer:
                verb, dtype, origin, destination, gate = transfer.groups()
                origin, destination = origin.lower(), destination.lower()
                self.port(
                    "output",
                    TYPES[dtype.lower()],
                    {"exposure_scope": destination, "transfer_source": origin},
                    number,
                    number,
                    "instruction",
                )
                self.add(
                    "operations",
                    {"name": verb.lower(), "parameters": None},
                    number,
                    number,
                    "instruction",
                )
                self.add(
                    "effects",
                    {
                        "name": verb.lower(),
                        "crosses_boundary": True,
                        "preserves_sensitivity": None,
                        "requires_authorization": True if gate else None,
                    },
                    number,
                    number,
                    "instruction",
                )
                self.add("context_exposure", {"scope": destination}, number, number, "instruction")
                self.add(
                    "trust_boundaries",
                    {"source": origin, "destination": destination},
                    number,
                    number,
                    "instruction",
                )
                continue
            match = re.fullmatch(
                r"(?:[-*] )?(Read|Accept|Return|Emit) (text|url|code|command)\.?", stripped, re.I
            )
            if match:
                verb, dtype = match[1].lower(), TYPES[match[2].lower()]
                self.port(
                    "input" if verb in {"read", "accept"} else "output",
                    dtype,
                    {},
                    number,
                    number,
                    "instruction",
                )
                self.add(
                    "operations", {"name": verb, "parameters": None}, number, number, "instruction"
                )
            else:
                self.issue("unknown", "uninterpreted_instruction", self.path, number)
        if fenced:
            self.issue("unknown", "unclosed_fence", self.path, opening_line)

    def python(self, text):
        # A bounded token count also limits the native parser's stack exposure.
        import io
        import tokenize

        try:
            for index, _ in enumerate(tokenize.generate_tokens(io.StringIO(text).readline)):
                if index >= 500:
                    self.issue("unknown", "python_token_limit", self.path)
                    return
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError, tokenize.TokenError) as exc:
            self.issue("parse_failure", "invalid_python", self.path, getattr(exc, "lineno", None))
            return
        calls = (n for n in ast.walk(tree) if isinstance(n, ast.Call))
        for call in sorted(
            calls, key=lambda n: (n.lineno, n.col_offset, n.end_lineno, n.end_col_offset)
        ):
            target = call.func
            parts = []
            while isinstance(target, ast.Attribute):
                parts.append(target.attr)
                target = target.value
            if not isinstance(target, ast.Name):
                self.issue("unknown", "dynamic_call_target", self.path, call.lineno)
                continue
            name = ".".join(reversed([*parts, target.id]))
            args = [ast.get_source_segment(text, arg) for arg in (*call.args, *call.keywords)]
            self.add(
                "operations",
                {"name": name, "parameters": args},
                call.lineno,
                call.end_lineno,
                "python_ast",
            )
        self.issue("unknown", "runtime_semantics_unresolved", self.path)


def extract(root: Path) -> dict:
    summary = {
        "schema_version": "p03.2",
        "status": "complete",
        "files": [],
        **{k: [] for k in GROUPS},
        "diagnostics": [],
    }

    inventory = {}

    def issue(state, reason, path, line=None):
        summary["diagnostics"].append(dict(state=state, reason=reason, path=path, line=line))
        if path in inventory:
            if reason == "inventory_only":
                inventory[path]["processing"] = "inventory_only"
            elif state == "parse_failure":
                inventory[path]["processing"] = "parse_failed"

    has_document = False
    for path, kind, text in scan(root, issue):
        if text is None:
            entry = {"path": path, "role": kind, "processing": "unread"}
            inventory[path] = entry
            summary["files"].append(entry)
            continue
        inventory[path]["processing"] = "processed"
        material = Material(path, text.replace("\r\n", "\n").replace("\r", "\n"), summary, issue)
        if kind == "skill_document":
            has_document = True
            material.document()
        elif kind == "metadata":
            material.metadata(material.lines, 0)
        else:
            material.python("\n".join(material.lines))
    for group in GROUPS:
        if not summary[group]:
            issue("missing_evidence", "no_claim_" + group, ".")
    if not has_document:
        summary["status"] = "failed"
    elif any(d["state"] == "read_failure" for d in summary["diagnostics"]):
        summary["status"] = "partial_read"
    elif summary["diagnostics"]:
        summary["status"] = "partial"
    validate(summary)
    return summary
