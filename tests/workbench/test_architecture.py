"""Architecture guards for the Workbench dependency direction."""

from __future__ import annotations

from ast import Import, ImportFrom, parse, walk
from pathlib import Path

_DOWNSTREAM_PRESENTATION_PACKAGES = frozenset({"cinematic", "ui"})


def test_lower_engine_and_science_packages_do_not_import_workbench() -> None:
    """Keep Workbench above modeled/scientific code but below presentation consumers."""
    package_root = Path(__file__).resolve().parents[2] / "src" / "evo_engine"
    leaks: list[str] = []

    for path in package_root.rglob("*.py"):
        relative = path.relative_to(package_root)
        if "workbench" in relative.parts:
            continue
        if relative.parts and relative.parts[0] in _DOWNSTREAM_PRESENTATION_PACKAGES:
            continue
        for imported_name in _imports(path):
            if imported_name.startswith("evo_engine.workbench"):
                leaks.append(str(relative))
                break

    assert leaks == []


def test_workbench_does_not_import_renderer_packages() -> None:
    """Keep renderer/frontend responsibilities downstream of Workbench science."""
    package_root = Path(__file__).resolve().parents[2] / "src" / "evo_engine"
    workbench_root = package_root / "workbench"
    leaks: list[tuple[str, str]] = []

    for path in workbench_root.rglob("*.py"):
        for imported_name in _imports(path):
            if imported_name.startswith(("evo_engine.ui", "evo_engine.cinematic")):
                leaks.append((str(path.relative_to(package_root)), imported_name))

    assert leaks == []


def test_model_and_science_packages_do_not_import_renderers() -> None:
    """Prevent UI/cinematic implementations from becoming scientific dependencies."""
    package_root = Path(__file__).resolve().parents[2] / "src" / "evo_engine"
    leaks: list[tuple[str, str]] = []

    for path in package_root.rglob("*.py"):
        relative = path.relative_to(package_root)
        if relative.parts and relative.parts[0] in _DOWNSTREAM_PRESENTATION_PACKAGES:
            continue
        for imported_name in _imports(path):
            if imported_name.startswith(("evo_engine.ui", "evo_engine.cinematic")):
                leaks.append((str(relative), imported_name))

    assert leaks == []


def _imports(path: Path) -> tuple[str, ...]:
    tree = parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: list[str] = []
    for node in walk(tree):
        if isinstance(node, Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ImportFrom) and node.module is not None:
            imported.append(node.module)
    return tuple(imported)
