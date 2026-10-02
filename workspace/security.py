"""Shared containment checks for read-only project access."""
from pathlib import Path


def contained_file(root: Path, relative: str) -> Path:
    candidate = root / relative
    try:
        candidate.relative_to(root)
        resolved = candidate.resolve()
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Path is outside project root") from exc
    for part in (candidate, *candidate.parents):
        if part == root:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise ValueError("Linked project paths are not allowed")
    if not resolved.is_file():
        raise ValueError("Path is not a regular project file")
    return resolved
