"""Architecture guards for the committed telemetry package."""

from __future__ import annotations

import ast
from pathlib import Path

_FORBIDDEN_DOMAIN_PREFIXES = (
    "evo_engine.behavior",
    "evo_engine.biology",
    "evo_engine.characteristics",
    "evo_engine.development",
    "evo_engine.energetics",
    "evo_engine.evolution",
    "evo_engine.feeding",
    "evo_engine.genetics",
    "evo_engine.growth",
    "evo_engine.life_history",
    "evo_engine.observation",
    "evo_engine.predation",
    "evo_engine.presets",
    "evo_engine.processes",
    "evo_engine.reproduction",
    "evo_engine.resolvers",
    "evo_engine.spatial",
    "evo_engine.world",
)
_FORBIDDEN_BIOLOGICAL_PROTOCOL_NAMES = {
    "MortalityEvent",
    "ParentageEvent",
}


def test_telemetry_does_not_import_modeled_domains() -> None:
    """Test committed telemetry remains an upstream domain-neutral package."""
    telemetry_root = Path("src/evo_engine/telemetry")
    violations: list[str] = []

    for path in sorted(telemetry_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            imported_modules = _imported_modules(node)
            for module in imported_modules:
                if module.startswith(_FORBIDDEN_DOMAIN_PREFIXES):
                    violations.append(f"{path}: imports {module}")

    assert violations == []


def test_telemetry_declares_no_biological_event_protocols() -> None:
    """Test biological event interpretation contracts live outside telemetry."""
    telemetry_root = Path("src/evo_engine/telemetry")
    declared_names: set[str] = set()

    for path in sorted(telemetry_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        declared_names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        )

    assert declared_names.isdisjoint(_FORBIDDEN_BIOLOGICAL_PROTOCOL_NAMES)


def _imported_modules(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return (node.module,)
    return ()
