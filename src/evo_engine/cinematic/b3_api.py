"""Public lazy-rendering entry point for the B3 flagship cinematic."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

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
        renderer = cast(
            _B3ManimRendererModule,
            import_module("evo_engine.cinematic._b3_manim"),
        )
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

    return renderer.render_b3_flagship_with_manim(
        plan,
        destination,
        quality=quality,
    )


__all__ = ["render_b3_flagship_cinematic"]
