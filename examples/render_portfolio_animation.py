"""Render the fixed-seed flagship evolutionary demonstration."""

from __future__ import annotations

import argparse
from pathlib import Path

from evo_engine.cinematic import (
    build_portfolio_animation_timeline,
    render_portfolio_animation,
)
from evo_engine.genetics import MAX_INTAKE_RATE
from evo_engine.observation import SpatialRecorder
from evo_engine.presets import (
    FLAGSHIP_MAX_INTAKE_SEED,
    build_flagship_max_intake_ecology,
    build_flagship_max_intake_specification,
)


def main() -> None:
    """Run the deterministic flagship ecology, then render committed results."""
    arguments = _parse_arguments()
    specification = build_flagship_max_intake_specification(
        seed=FLAGSHIP_MAX_INTAKE_SEED,
        max_steps=arguments.max_steps,
    )
    spatial_recorder = SpatialRecorder()
    ecology = build_flagship_max_intake_ecology(
        specification,
        additional_observers=(spatial_recorder,),
    )

    ecology.engine.run(ecology.simulation)

    timeline = build_portfolio_animation_timeline(
        spatial_history=spatial_recorder.observations,
        population_history=ecology.recorder.observations,
        trait_name=MAX_INTAKE_RATE,
    )
    output_path = render_portfolio_animation(
        timeline,
        arguments.output,
        quality=arguments.quality,
    )
    print(f"Rendered deterministic flagship animation: {output_path}")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the fixed-seed flagship max-intake demonstration to completion "
            "and render its committed observations with the optional Manim path."
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
        default=40,
        help="Number of deterministic flagship steps to record.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
