"""Bounded static object-flow interpretation of a straight-line Python entry."""

import argparse
import ast
import json
import sys
from pathlib import Path, PurePosixPath

from .skill_reader import scan


class Incomplete(Exception):
    """Stop interpretation at an unsupported operation."""


class Analyzer:
    def __init__(self, sources, issues):
        self.sources = sources
        self.issues = issues
        self.nodes = []
        self.edges = []
        self.bindings = []
        self.functions = {}
        self.stack = []
        self.modules = {}
        self.members = {}
        self.receivers = {}
        self.visited = set()

    def stop(self, path, node, reason):
        self.issues.append({"file": path, "line": getattr(node, "lineno", None), "reason": reason})
        raise Incomplete

    def obj(self, path, node, kind, name, domain="local"):
        if len(self.nodes) >= 4096:
            self.stop(path, node, "object_limit")
        ident = len(self.nodes)
        self.nodes.append(
            dict(id=ident, file=path, line=node.lineno, kind=kind, name=name, domain=domain)
        )
        return ident

    def edge(self, path, node, source, target, kind):
        self.edges.append(
            dict(source=source, target=target, kind=kind, file=path, line=node.lineno)
        )

    def member(self, path, node, owner, name):
        key = (owner, name)
        if key not in self.members:
            obj = self.nodes[owner]
            child = self.obj(path, node, "api", name, obj["domain"])
            self.members[key] = child
            self.edge(path, node, owner, child, "owns")
            self.edge(path, node, owner, child, "data_flow")
            if obj["kind"] == "file_handle":
                self.receivers[child] = owner
        return self.members[key]

    def define(self, path, node, env, name, value):
        env[name] = value
        self.bindings.append(
            dict(file=path, line=node.lineno, name=name, role="definition", object=value)
        )

    def parse(self, path):
        try:
            return ast.parse(self.sources[path]).body
        except (ValueError, SyntaxError, RecursionError) as exc:
            self.issues.append(
                dict(file=path, line=getattr(exc, "lineno", None), reason="parse_failure")
            )
            raise Incomplete from exc

    def function(self, path, node):
        args = node.args
        if (
            node.decorator_list
            or args.defaults
            or args.vararg
            or args.kwarg
            or args.kwonlyargs
            or node.returns
            or any(a.annotation for a in args.posonlyargs + args.args)
            or getattr(node, "type_params", [])
        ):
            self.stop(path, node, "unsupported_signature")
        ident = self.obj(path, node, "function", node.name)
        self.functions[ident] = (path, node)
        return ident

    def expr(self, path, node, env):
        if isinstance(node, ast.Constant):
            return self.obj(path, node, "literal", repr(node.value))
        if isinstance(node, ast.Name):
            if node.id in env:
                self.bindings.append(
                    dict(file=path, line=node.lineno, name=node.id, role="use", object=env[node.id])
                )
                return env[node.id]
            if self.stack and node.id == self.functions[self.stack[-1]][1].name:
                self.stop(path, node, "unresolved_self_reference")
            if node.id == "open" and self.stack:
                self.stop(path, node, "unresolved_free_open")
            if node.id == "open":
                return self.obj(path, node, "api", "open", "file")
        if isinstance(node, ast.Attribute):
            owner = self.expr(path, node.value, env)
            obj = self.nodes[owner]
            if obj["kind"] == "module" or (
                obj["kind"] == "file_handle" and node.attr in {"read", "write", "close"}
            ):
                return self.member(path, node, owner, node.attr)
        if isinstance(node, ast.Call) and not node.keywords:
            fn = self.expr(path, node.func, env)
            args = [self.expr(path, arg, env) for arg in node.args]
            if fn in self.functions:
                file, definition = self.functions[fn]
                params = definition.args.posonlyargs + definition.args.args
                if fn in self.stack:
                    self.stop(path, node, "recursive_call")
                if len(self.stack) >= 24 or len(params) != len(args):
                    self.stop(path, node, "unsupported_call")
                self.visited.add(fn)
                self.stack.append(fn)
                try:
                    local = dict(zip([p.arg for p in params], args, strict=True))
                    for p in params:
                        self.bindings.append(
                            dict(
                                file=file,
                                line=p.lineno,
                                name=p.arg,
                                role="parameter",
                                object=local[p.arg],
                                caller=path,
                                call_line=node.lineno,
                            )
                        )
                    result = self.block(file, definition.body, local)
                finally:
                    self.stack.pop()
                if result is None:
                    result = self.obj(path, node, "literal", "None")
                return result
            obj = self.nodes[fn]
            if obj["kind"] == "api":
                handle = obj["domain"] == "file" and obj["name"] == "open"
                result = self.obj(
                    path, node, "file_handle" if handle else "result", obj["name"], obj["domain"]
                )
                self.edge(path, node, fn, result, "owns")
                if fn in self.receivers:
                    args.append(self.receivers[fn])
                for source in dict.fromkeys(args + [fn]):
                    self.edge(path, node, source, result, "data_flow")
                return result
        self.stop(path, node, "unresolved_" + type(node).__name__)

    def block(self, path, body, env):
        for node in body:
            if isinstance(node, ast.FunctionDef):
                self.define(path, node, env, node.name, self.function(path, node))
            elif isinstance(node, ast.Assign) and all(
                isinstance(t, ast.Name) for t in node.targets
            ):
                value = self.expr(path, node.value, env)
                for target in node.targets:
                    self.define(path, target, env, target.id, value)
            elif isinstance(node, ast.Pass) or (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and node.value.value is Ellipsis
            ):
                continue
            elif isinstance(node, ast.Expr):
                self.expr(path, node.value, env)
            elif isinstance(node, ast.Return) and self.stack:
                return self.expr(path, node.value, env) if node.value else None
            elif isinstance(node, (ast.ImportFrom, ast.Import)):
                for alias in node.names:
                    module = node.module if isinstance(node, ast.ImportFrom) else alias.name
                    if (
                        not module
                        or "." in module
                        or getattr(node, "level", 0)
                        or alias.name == "*"
                    ):
                        self.stop(path, node, "unsupported_import")
                    sibling = str(PurePosixPath(path).with_name(module + ".py"))
                    package = PurePosixPath(path).with_name(module) / "__init__.py"
                    if package.as_posix() in self.sources:
                        self.stop(path, node, "unsupported_local_package")
                    if sibling in self.sources:
                        defs = self.parse(sibling)
                        if (
                            defs
                            and isinstance(defs[0], ast.Expr)
                            and isinstance(defs[0].value, ast.Constant)
                            and isinstance(defs[0].value.value, str)
                        ):
                            defs = defs[1:]
                        if not isinstance(node, ast.ImportFrom) or not all(
                            isinstance(d, ast.FunctionDef) for d in defs
                        ):
                            self.stop(path, node, "unsupported_module_initialization")
                        matches = [d for d in defs if d.name == alias.name]
                        if len(matches) != 1:
                            self.stop(path, node, "unresolved_import")
                        value = self.function(sibling, matches[0])
                    else:
                        if module not in self.modules:
                            root = self.obj(path, node, "module", module, "import:" + module)
                            self.nodes[root]["resolution"] = (
                                "stdlib_name_unverified"
                                if module in sys.stdlib_module_names
                                else "unverified_external"
                            )
                            self.modules[module] = root
                        value = self.modules[module]
                        if isinstance(node, ast.ImportFrom):
                            value = self.member(path, alias, value, alias.name)
                    self.define(path, alias, env, alias.asname or alias.name, value)
            else:
                self.stop(path, node, "unsupported_" + type(node).__name__)
        return None


def analyze(directory, entry):
    issues = []

    def issue(category, reason, file):
        if reason != "inventory_only":
            issues.append(dict(file=file, line=None, reason=reason))

    sources = {}
    for file, kind, text in scan(directory, issue):
        if kind == "script" and file.endswith(".py"):
            sources[file] = text if text is not None else ""
    analysis = Analyzer(sources, issues)
    entry_analysis = "not_started"
    if entry not in sources:
        issues.append(dict(file=entry, line=None, reason="missing_or_unsupported_entry"))
    elif not issues:
        try:
            entry_analysis = "incomplete"
            analysis.block(entry, analysis.parse(entry), {})
            entry_analysis = "finished"
        except Incomplete:
            pass
        except RecursionError:
            issue("limit", "recursion_limit", entry)
    return dict(
        status="partial" if issues else "complete_in_subset",
        entry=entry,
        entry_analysis=entry_analysis,
        unvisited_functions=[
            dict(file=file, line=node.lineno, name=node.name, object=i)
            for i, (file, node) in analysis.functions.items()
            if i not in analysis.visited
        ],
        nodes=analysis.nodes,
        edges=analysis.edges,
        bindings=analysis.bindings,
        issues=issues,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("entry")
    args = parser.parse_args()
    output = analyze(args.directory, args.entry)
    print(json.dumps(output, indent=2))
    raise SystemExit(int(bool(output["issues"])))
