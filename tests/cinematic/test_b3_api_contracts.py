"""Additional contract tests for the B3 lazy rendering boundary."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import evo_engine.cinematic.b3_api as b3_api
from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan


def test_b3_render_rejects_wrong_plan_type(tmp_path: Path) -> None:
    """Rendering requires the concrete prepared B3 director value."""
    invalid_plan = cast(B3FlagshipDirectorPlan, object())

    with pytest.raises(TypeError, match="B3FlagshipDirectorPlan"):
        b3_api.render_b3_flagship_cinematic(
            invalid_plan,
            tmp_path / "b3.mp4",
            quality="low",
        )


def test_b3_render_rejects_unknown_quality(tmp_path: Path) -> None:
    """The public renderer accepts only the documented deterministic qualities."""
    plan = object.__new__(B3FlagshipDirectorPlan)
    invalid_quality = cast(AnimationQuality, "ultra")

    with pytest.raises(ValueError, match="quality must be"):
        b3_api.render_b3_flagship_cinematic(
            plan,
            tmp_path / "b3.mp4",
            quality=invalid_quality,
        )


def test_nested_manim_import_error_remains_actionable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Missing Manim submodules receive the same optional-dependency guidance."""

    def missing_renderer(name: str) -> object:
        assert name == "evo_engine.cinematic._b3_manim"
        raise ModuleNotFoundError(
            "No module named 'manim.camera'",
            name="manim.camera",
        )

    monkeypatch.setattr(b3_api, "import_module", missing_renderer)
    plan = object.__new__(B3FlagshipDirectorPlan)

    with pytest.raises(RuntimeError, match="requirements-animation.txt"):
        b3_api.render_b3_flagship_cinematic(
            plan,
            tmp_path / "b3.mp4",
            quality="low",
        )


def test_unrelated_renderer_import_error_is_not_reclassified(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Only missing Manim dependencies are translated into installation guidance."""

    def missing_renderer(name: str) -> object:
        assert name == "evo_engine.cinematic._b3_manim"
        raise ModuleNotFoundError("No module named 'other'", name="other")

    monkeypatch.setattr(b3_api, "import_module", missing_renderer)
    plan = object.__new__(B3FlagshipDirectorPlan)

    with pytest.raises(ModuleNotFoundError, match="other"):
        b3_api.render_b3_flagship_cinematic(
            plan,
            tmp_path / "b3.mp4",
            quality="low",
        )


def test_b3_render_delegates_to_lazy_renderer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A valid call resolves its destination and delegates without owning Manim."""
    plan = object.__new__(B3FlagshipDirectorPlan)
    captured: dict[str, object] = {}

    def render(
        received_plan: B3FlagshipDirectorPlan,
        output_path: Path,
        *,
        quality: AnimationQuality,
    ) -> Path:
        captured["plan"] = received_plan
        captured["path"] = output_path
        captured["quality"] = quality
        return output_path

    module = SimpleNamespace(render_b3_flagship_with_manim=render)
    monkeypatch.setattr(b3_api, "import_module", lambda _name: module)
    destination = tmp_path / "nested" / "b3.gif"

    result = b3_api.render_b3_flagship_cinematic(
        plan,
        destination,
        quality="high",
    )

    expected = destination.resolve()
    assert result == expected
    assert expected.parent.is_dir()
    assert captured == {
        "plan": plan,
        "path": expected,
        "quality": "high",
    }
