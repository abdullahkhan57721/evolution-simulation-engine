"""Render a fixed-seed cinematic replay of the complete reference ecology."""

from __future__ import annotations

import argparse
from pathlib import Path

from evo_engine.cinematic import (
    build_portfolio_animation_timeline,
    render_portfolio_animation,
)
from evo_engine.genetics import GROWTH_RATE
from evo_engine.observation import SpatialRecorder
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def main() -> None:
    """Run the deterministic reference ecology, then render committed results."""
    arguments = _parse_arguments()
    config = ReferenceEcologyConfig(
        width=12,
        height=12,
        initial_population=20,
        max_steps=arguments.max_steps,
        seed=42,
    )
    spatial_recorder = SpatialRecorder()
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial_recorder,),
    )

    ecology.engine.run(ecology.simulation)

    timeline = build_portfolio_animation_timeline(
        spatial_history=spatial_recorder.observations,
        population_history=ecology.recorder.observations,
        trait_name=GROWTH_RATE,
    )
    output_path = render_portfolio_animation(
        timeline,
        arguments.output,
        quality=arguments.quality,
    )
    print(f"Rendered deterministic portfolio animation: {output_path}")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the fixed-seed reference ecology to completion and render its "
            "committed observations with the optional Manim cinematic path."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/portfolio-animation.mp4"),
        help="Destination .mp4 or .gif path.",
    )
    parser.add_argument(
        "--quality",
        choices=("low", "medium", "high"),
        default="medium",
        help="Manim render quality preset.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=30,
        help="Number of deterministic reference-ecology steps to record.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
