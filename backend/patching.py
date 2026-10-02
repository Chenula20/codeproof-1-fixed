"""Strict unified-diff application in memory. No shell or filesystem access."""
import re
from pathlib import PurePosixPath


def safe_path(value: str) -> str:
    if not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Invalid patch path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Patch path must be relative and contained")
    if any(p.startswith(".") for p in path.parts):
        raise ValueError("Hidden files cannot be patched")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if any(p.endswith((".", " ")) or p.split(".")[0].upper() in reserved for p in path.parts):
        raise ValueError("Ambiguous or reserved Windows path")
    return value


def apply_diff(files: dict[str, str], diff: str, allowed: list[str]) -> dict[str, str]:
    """Accept exact, existing-file hunks only; reject renames and fuzzy matches."""
    if len(diff) > 200_000:
        raise ValueError("Patch exceeds size limit")
    lines = diff.splitlines(keepends=True)
    result = dict(files)
    changed: set[str] = set()
    i = 0
    while i < len(lines):
        if lines[i].startswith(("diff --git ", "index ")) or not lines[i].strip():
            i += 1
            continue
        if not lines[i].startswith("--- a/") or i + 1 >= len(lines):
            raise ValueError("Expected a unified diff file header")
        old = safe_path(lines[i][6:].strip())
        i += 1
        if not lines[i].startswith("+++ b/"):
            raise ValueError("New files and deletions are not supported")
        new = safe_path(lines[i][6:].strip())
        if old != new or old not in allowed or old not in files or old in changed:
            raise ValueError("Patch target is not an approved snapshot file")
        original = files[old].splitlines(keepends=True)
        output: list[str] = []
        cursor = 0
        i += 1
        hunks = 0
        while i < len(lines) and lines[i].startswith("@@ "):
            header = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
            if not header:
                raise ValueError("Invalid hunk header")
            start, count, new_start, new_count = header.groups()
            old_count, added_count = int(count or 1), int(new_count or 1)
            offset = int(start) - (1 if old_count else 0)
            if offset < cursor or offset > len(original):
                raise ValueError("Overlapping or out-of-range hunk")
            output.extend(original[cursor:offset])
            cursor = offset
            if int(new_start) - (1 if added_count else 0) != len(output):
                raise ValueError("Invalid new-file offset")
            consumed = produced = 0
            i += 1
            while i < len(lines) and not lines[i].startswith(("@@ ", "--- a/", "diff --git ")):
                line = lines[i]
                if not line or line[0] not in " +-":
                    raise ValueError("Unsupported diff line (including no-newline markers)")
                content = line[1:]
                if line[0] in " -":
                    if cursor >= len(original) or original[cursor] != content:
                        raise ValueError("Patch context no longer matches snapshot")
                    consumed += 1
                    cursor += 1
                if line[0] in " +":
                    output.append(content)
                    produced += 1
                i += 1
                if consumed == old_count and produced == added_count:
                    break
            if consumed != old_count or produced != added_count:
                raise ValueError("Hunk line counts do not match")
            hunks += 1
        if not hunks:
            raise ValueError("Patch has no hunks")
        output.extend(original[cursor:])
        result[old] = "".join(output)
        changed.add(old)
    if not changed or all(result[p] == files[p] for p in changed):
        raise ValueError("Patch makes no changes")
    return result
