"""Public lazy-rendering entry point for the B3 flagship cinematic."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan


class _B3ManimRendererModule(Protocol):
    def render_b3_flagship_with_manim(
        self,
        plan: B3FlagshipDirectorPlan,
        output_path: Path,
        *,
        quality: AnimationQuality,
    ) -> Path: ...


def render_b3_flagship_cinematic(
    plan: B3FlagshipDirectorPlan,
    output_path: str | Path,
    *,
    quality: AnimationQuality = "medium",
) -> Path:
    """Render one prepared B3 flagship director plan with optional Manim.

    Manim remains a lazy optional dependency. The director plan itself contains only
    committed/derived scientific values and renderer-neutral explanatory selections.
    """
    if not isinstance(plan, B3FlagshipDirectorPlan):
        raise TypeError("plan must be a B3FlagshipDirectorPlan.")
    if quality not in ("low", "medium", "high"):
        raise ValueError("quality must be 'low', 'medium', or 'high'.")
    destination = Path(output_path).expanduser()
    if destination.suffix.lower() not in (".mp4", ".gif"):
        raise ValueError("output_path must end in .mp4 or .gif.")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        renderer_module = import_module("evo_engine.cinematic._b3_manim")
    except ModuleNotFoundError as exc:
        if exc.name == "manim" or (
            exc.name is not None and exc.name.startswith("manim.")
        ):
            raise RuntimeError(
                "Manim is an optional dependency. Install it with "
                "`python -m pip install -r requirements-animation.txt` before "
                "rendering the B3 flagship cinematic."
            ) from exc
        raise

    _install_moving_camera_overlay_compat(renderer_module)
    renderer = cast(_B3ManimRendererModule, renderer_module)
    return renderer.render_b3_flagship_with_manim(
        plan,
        destination,
        quality=quality,
    )


def _install_moving_camera_overlay_compat(renderer_module: Any) -> None:
    """Bridge the small Manim 0.21 moving-camera overlay API difference.

    ``MovingCameraScene`` in the repository's supported Manim 0.21 line does not
    expose ``add_fixed_in_frame_mobjects`` / ``remove_fixed_in_frame_mobjects``.
    The B3 scene uses those calls only for explanatory heading/annotation objects;
    on this renderer version they may safely remain ordinary scene mobjects while
    the camera performs its short focal move. Scientific glyph values and camera
    targets are unchanged.
    """
    scene_type = getattr(renderer_module, "_B3FlagshipScene", None)
    if scene_type is None or hasattr(scene_type, "add_fixed_in_frame_mobjects"):
        return

    def add_overlay(self: Any, *mobjects: object) -> None:
        self.add(*mobjects)

    def remove_overlay(self: Any, *mobjects: object) -> None:
        self.remove(*mobjects)

    scene_type.add_fixed_in_frame_mobjects = add_overlay
    scene_type.remove_fixed_in_frame_mobjects = remove_overlay


__all__ = ["render_b3_flagship_cinematic"]
