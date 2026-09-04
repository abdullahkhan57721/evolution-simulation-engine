"""Tests for the B3-specific lazy cinematic render API."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import evo_engine.cinematic.b3_api as b3_api
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan


def test_missing_manim_has_actionable_b3_render_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test B3 rendering keeps Manim optional and reports installation guidance."""

    def missing_renderer(name: str) -> object:
        assert name == "evo_engine.cinematic._b3_manim"
        raise ModuleNotFoundError("No module named 'manim'", name="manim")

    monkeypatch.setattr(b3_api, "import_module", missing_renderer)
    plan = object.__new__(B3FlagshipDirectorPlan)

    with pytest.raises(RuntimeError, match="requirements-animation.txt"):
        b3_api.render_b3_flagship_cinematic(
            plan,
            tmp_path / "b3.mp4",
            quality="low",
        )


def test_b3_render_rejects_non_media_destination() -> None:
    """Test the B3 render entry point retains explicit media output semantics."""
    plan = object.__new__(B3FlagshipDirectorPlan)

    with pytest.raises(ValueError, match=".mp4 or .gif"):
        b3_api.render_b3_flagship_cinematic(plan, "b3.txt", quality="low")


def test_moving_camera_overlay_compat_uses_scene_add_remove() -> None:
    """Test supported Manim 0.21 scenes receive the narrow overlay bridge."""

    class FakeScene:
        def __init__(self) -> None:
            self.added: tuple[object, ...] = ()
            self.removed: tuple[object, ...] = ()

        def add(self, *mobjects: object) -> None:
            self.added = mobjects

        def remove(self, *mobjects: object) -> None:
            self.removed = mobjects

    module = SimpleNamespace(_B3FlagshipScene=FakeScene)
    b3_api._install_moving_camera_overlay_compat(module)

    scene = FakeScene()
    first = object()
    second = object()
    scene.add_fixed_in_frame_mobjects(first, second)  # type: ignore[attr-defined]
    scene.remove_fixed_in_frame_mobjects(first)  # type: ignore[attr-defined]

    assert scene.added == (first, second)
    assert scene.removed == (first,)


def test_overlay_compat_leaves_existing_renderer_api_unchanged() -> None:
    """Test the compatibility bridge does not replace a renderer-provided API."""

    class FakeScene:
        @staticmethod
        def add_fixed_in_frame_mobjects(*mobjects: object) -> str:
            return "native"

    original = FakeScene.add_fixed_in_frame_mobjects
    module = SimpleNamespace(_B3FlagshipScene=FakeScene)

    b3_api._install_moving_camera_overlay_compat(module)

    assert FakeScene.add_fixed_in_frame_mobjects is original
