"""Architecture guard for domain-neutral preference-order resolution."""

from __future__ import annotations

import ast
from pathlib import Path

_FORBIDDEN_DOMAIN_PREFIXES = (
    "evo_engine.behavior",
    "evo_engine.biology",
    "evo_engine.characteristics",
    "evo_engine.development",
    "evo_engine.energetics",
    "evo_engine.feeding",
    "evo_engine.genetics",
    "evo_engine.growth",
    "evo_engine.life_history",
    "evo_engine.observation",
    "evo_engine.predation",
    "evo_engine.presets",
    "evo_engine.processes",
    "evo_engine.reproduction",
    "evo_engine.spatial",
    "evo_engine.world",
)


def test_generic_preference_resolution_imports_no_modeled_domain() -> None:
    """Test the shared conflict algorithm stays independent of modeled domains."""
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "evo_engine"
        / "resolvers"
        / "_preference_order.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imports = _imported_modules(tree)

    forbidden = tuple(
        imported
        for imported in imports
        if imported.startswith(_FORBIDDEN_DOMAIN_PREFIXES)
    )
    assert forbidden == ()


def _imported_modules(tree: ast.AST) -> tuple[str, ...]:
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)
