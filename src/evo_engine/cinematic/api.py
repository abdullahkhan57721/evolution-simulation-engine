"""Public entry point for optional Manim cinematic rendering."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Literal, Protocol, cast

from evo_engine.cinematic.timeline import PortfolioAnimationTimeline

AnimationQuality = Literal["low", "medium", "high"]


class _ManimRendererModule(Protocol):
    def render_timeline_with_manim(
        self,
        timeline: PortfolioAnimationTimeline,
        output_path: Path,
        *,
        quality: AnimationQuality,
    ) -> Path: ...


def render_portfolio_animation(
    timeline: PortfolioAnimationTimeline,
    output_path: str | Path,
    *,
    quality: AnimationQuality = "medium",
) -> Path:
    """Render one completed cinematic timeline to MP4 or GIF with Manim.

    Manim is imported lazily so simulation, observation, and deterministic
    timeline preparation remain usable without the optional animation dependency.

    Args:
        timeline: Completed renderer-owned timeline built from committed records.
        output_path: Destination ending in ``.mp4`` or ``.gif``.
        quality: Render preset: ``"low"``, ``"medium"``, or ``"high"``.

    Returns:
        Resolved path to the rendered output file.

    Raises:
        TypeError: If ``timeline`` is not a ``PortfolioAnimationTimeline``.
        ValueError: If output format or quality is unsupported.
        RuntimeError: If the optional Manim dependency is not installed.
    """
    if not isinstance(timeline, PortfolioAnimationTimeline):
        raise TypeError("timeline must be a PortfolioAnimationTimeline.")
    if quality not in ("low", "medium", "high"):
        raise ValueError("quality must be 'low', 'medium', or 'high'.")

    destination = Path(output_path).expanduser()
    if destination.suffix.lower() not in (".mp4", ".gif"):
        raise ValueError("output_path must end in .mp4 or .gif.")
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        renderer = cast(
            _ManimRendererModule,
            import_module("evo_engine.cinematic._manim"),
        )
    except ModuleNotFoundError as exc:
        if exc.name == "manim" or (
            exc.name is not None and exc.name.startswith("manim.")
        ):
            raise RuntimeError(
                "Manim is an optional dependency. Install it with "
                "`python -m pip install -r requirements-animation.txt` before "
                "rendering portfolio animations."
            ) from exc
        raise

    return renderer.render_timeline_with_manim(
        timeline,
        destination,
        quality=quality,
    )
