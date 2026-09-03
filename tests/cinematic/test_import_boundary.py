"""Architecture and optional-dependency guards for cinematic presentation."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

import evo_engine.cinematic.api as cinematic_api
from evo_engine.cinematic import (
    PortfolioAnimationTimeline,
    render_portfolio_animation,
)


def test_importing_cinematic_does_not_import_manim() -> None:
    """Test ordinary cinematic preparation remains usable without loading Manim."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; import evo_engine.cinematic; "
                "assert 'manim' not in sys.modules"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_missing_manim_has_actionable_render_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test rendering explains how to install the optional dependency."""

    def missing_renderer(name: str) -> object:
        assert name == "evo_engine.cinematic._manim"
        raise ModuleNotFoundError("No module named 'manim'", name="manim")

    monkeypatch.setattr(cinematic_api, "import_module", missing_renderer)

    with pytest.raises(RuntimeError, match="requirements-animation.txt"):
        render_portfolio_animation(
            PortfolioAnimationTimeline(trait_name="growth_rate"),
            tmp_path / "animation.mp4",
            quality="low",
        )


def test_production_packages_do_not_depend_on_cinematic() -> None:
    """Test cinematic presentation remains a top-level package consumer."""
    package_root = Path("src/evo_engine")
    violations: list[str] = []

    for path in sorted(package_root.rglob("*.py")):
        if "cinematic" in path.relative_to(package_root).parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if module == "evo_engine.cinematic" or module.startswith(
                    "evo_engine.cinematic."
                ):
                    violations.append(f"{path}: imports {module}")

    assert violations == []


def test_manim_import_is_isolated_to_optional_renderer_module() -> None:
    """Test Manim cannot leak into preparation or lower production packages."""
    package_root = Path("src/evo_engine")
    allowed = package_root / "cinematic" / "_manim.py"
    violations: list[str] = []

    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module in _imported_modules(node):
                if (module == "manim" or module.startswith("manim.")) and path != allowed:
                    violations.append(f"{path}: imports {module}")

    assert violations == []


def _imported_modules(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Import):
        return tuple(alias.name for alias in node.names)
    if isinstance(node, ast.ImportFrom) and node.module is not None:
        return (node.module,)
    return ()
