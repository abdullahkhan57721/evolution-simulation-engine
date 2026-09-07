"""Architecture guards for the Workbench dependency direction."""

from __future__ import annotations

import ast
from pathlib import Path


def test_lower_engine_and_domain_packages_do_not_import_workbench() -> None:
    """Keep Workbench as an authoring layer above every existing lower package."""
    package_root = Path(__file__).resolve().parents[2] / "src" / "evo_engine"
    leaks: list[str] = []

    for path in package_root.rglob("*.py"):
        if "workbench" in path.relative_to(package_root).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = (alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported = (node.module,)
            else:
                continue
            if any(name.startswith("evo_engine.workbench") for name in imported):
                leaks.append(str(path.relative_to(package_root)))

    assert leaks == []
