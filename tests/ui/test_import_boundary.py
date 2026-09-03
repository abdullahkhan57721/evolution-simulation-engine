"""Architecture guards for the optional portfolio UI package."""

from __future__ import annotations

import ast
from pathlib import Path


def test_production_packages_do_not_depend_on_ui() -> None:
    """Test the UI remains a top-level consumer of production packages."""
    package_root = Path("src/evo_engine")
    violations: list[str] = []

    for path in sorted(package_root.rglob("*.py")):
        if "ui" in path.relative_to(package_root).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if module == "evo_engine.ui" or module.startswith("evo_engine.ui."):
                    violations.append(f"{path}: imports {module}")

    assert violations == []


def _imported_modules(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return (node.module,)
    return ()
