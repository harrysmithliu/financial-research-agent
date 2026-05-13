from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_ingestion_and_storage_do_not_import_api_runtime() -> None:
    imported_modules = {
        imported_module
        for package_name in ("ingestion", "storage")
        for imported_module in _iter_imported_modules(REPO_ROOT / package_name)
    }

    assert "fastapi" not in imported_modules
    assert "api.main" not in imported_modules


def _iter_imported_modules(package_path: Path) -> set[str]:
    imported_modules = set()
    for file_path in package_path.rglob("*.py"):
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
    return imported_modules

