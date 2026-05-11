from __future__ import annotations

from pathlib import Path


class SourcePathError(FileNotFoundError):
    """Raised when a manifest source URI cannot be resolved locally."""


def resolve_source_path(repo_root: str | Path, source_uri: str) -> Path:
    source_path = Path(source_uri)
    if source_path.is_absolute():
        return source_path
    return Path(repo_root) / source_path


def resolve_existing_source_path(repo_root: str | Path, source_uri: str) -> Path:
    resolved_path = resolve_source_path(repo_root, source_uri)
    if not resolved_path.exists():
        raise SourcePathError(f"Manifest source does not exist: {resolved_path}")
    return resolved_path

