"""Inspect a caller-isolated, immutable local snapshot. Never import its contents."""

import os
import stat
from pathlib import Path

MAX_ENTRIES = 256
MAX_DEPTH = 12
MAX_FILE = 32 * 1024
MAX_TOTAL = 256 * 1024
SCRIPT_SUFFIXES = {".py", ".js", ".ts", ".sh", ".ps1", ".rb", ".bat", ".cmd"}


def role(path):
    if path == Path("SKILL.md"):
        return "skill_document"
    if "scripts" in path.parts[:-1] or path.suffix.lower() in SCRIPT_SUFFIXES:
        return "script"
    if {"resources", "assets", "templates"} & set(path.parts[:-1]):
        return "resource"
    if path.suffix.lower() in {".yaml", ".yml", ".json", ".toml"}:
        return "metadata"
    return "resource"


def redirected(info):
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def scan(root, issue):
    """Yield (relative path, role, optional text); report all skipped inputs."""
    root = Path(root)
    if (
        ".." in root.parts
        or root.drive.startswith("\\\\")
        or (os.name == "nt" and any(":" in part for part in root.parts if part != root.anchor))
    ):
        issue("read_failure", "unsafe_root", ".")
        return
    root = root.absolute()
    try:
        for parent in (*reversed(root.parents), root):
            info = parent.lstat()
            if redirected(info) or not stat.S_ISDIR(info.st_mode):
                issue("read_failure", "unsafe_root", ".")
                return
    except OSError:
        issue("read_failure", "unavailable_root", ".")
        return
    try:
        document = (root / "SKILL.md").lstat()
    except OSError:
        issue("read_failure", "document_unavailable", "SKILL.md")
        return
    if redirected(document) or not stat.S_ISREG(document.st_mode) or document.st_nlink != 1:
        issue("read_failure", "unsafe_entry", "SKILL.md")
        return
    pending = [Path(".")]

    def check_streams(path, rel):
        if os.name == "nt":
            from .windows_streams import has_named_stream

            try:
                if has_named_stream(path):
                    issue("unknown", "named_stream_unexamined", rel)
            except OSError:
                issue("read_failure", "stream_inventory_failed", rel)

    check_streams(root, ".")
    count = total = 0
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(root / directory) as entries:
                names = []
                for entry in entries:
                    count += 1
                    if count > MAX_ENTRIES:
                        issue("read_failure", "entry_limit", directory.as_posix())
                        return
                    names.append(entry.name)
        except OSError:
            issue("read_failure", "directory_io", directory.as_posix())
            continue
        for name in sorted(names):
            path = directory / name
            rel = path.as_posix()
            filename = root / path
            try:
                info = filename.lstat()
                if redirected(info):
                    issue("read_failure", "redirected_entry", rel)
                    continue
                if stat.S_ISDIR(info.st_mode):
                    check_streams(filename, rel)
                    if len(path.parts) < MAX_DEPTH:
                        pending.append(path)
                    else:
                        issue("read_failure", "depth_limit", rel)
                    continue
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    issue("read_failure", "unsafe_entry", rel)
                    continue
                kind = role(path)
                check_streams(filename, rel)
                # Only read the document, Python scripts and explicit YAML metadata.
                supported = (
                    kind == "skill_document"
                    or (kind == "script" and path.suffix.lower() == ".py")
                    or (kind == "metadata" and path.suffix.lower() in {".yaml", ".yml"})
                )
                yield rel, kind, None
                if not supported:
                    issue("unknown", "inventory_only", rel)
                    continue
                if info.st_size > MAX_FILE or total + info.st_size > MAX_TOTAL:
                    issue("read_failure", "byte_limit", rel)
                    continue
                with filename.open("rb") as stream:
                    data = stream.read(min(MAX_FILE, MAX_TOTAL - total) + 1)
                total += len(data)
                if len(data) != info.st_size:
                    issue("read_failure", "snapshot_changed", rel)
                    continue
                yield rel, kind, data.decode("utf-8-sig")
            except UnicodeDecodeError:
                issue("parse_failure", "invalid_utf8", rel)
            except OSError:
                issue("read_failure", "file_io", rel)
