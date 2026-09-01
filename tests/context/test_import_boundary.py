"""Architecture guard for the simulation-context foundation."""

from __future__ import annotations

import ast
from pathlib import Path


def test_context_does_not_depend_on_other_evo_engine_modules() -> None:
    """Test context remains a self-contained domain-neutral foundation."""
    path = Path("src/evo_engine/context.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []

    for node in ast.walk(tree):
        for module in _imported_modules(node):
            if module == "evo_engine" or module.startswith("evo_engine."):
                violations.append(f"{path}: imports {module}")

    assert violations == []


def _imported_modules(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return (node.module,)
    return ()
