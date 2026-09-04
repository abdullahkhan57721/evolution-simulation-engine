"""Render a short B1/B2 science-aware cinematic proof from committed evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from evo_engine.cinematic import (
    build_portfolio_animation_timeline,
    render_portfolio_animation,
)
from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import IndividualGeneticTraitRecorder, SpatialRecorder
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.presets.reference_ecology.config import (
    REFERENCE_TRAIT_DOMAINS,
    ReferenceEcologyConfig,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology


def main() -> None:
    """Run a tiny patchy reference ecology, then render committed focal evidence."""
    arguments = _parse_arguments()
    config = ReferenceEcologyConfig(
        width=6,
        height=6,
        initial_population=4,
        max_steps=2,
        seed=17,
        resource_deposits_per_step=2,
        resource_placement_model=PatchyResourcePlacement(
            patches=(
                ResourcePatch(center_x=1, center_y=1, radius=1),
                ResourcePatch(center_x=4, center_y=4, radius=1),
            )
        ),
    )
    spatial_recorder = SpatialRecorder()
    trait_recorder = IndividualGeneticTraitRecorder(trait_names=(MAX_SPEED,))
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial_recorder, trait_recorder),
    )
    ecology.engine.run(ecology.simulation)

    lower_bound, upper_bound = REFERENCE_TRAIT_DOMAINS[MAX_SPEED]
    timeline = build_portfolio_animation_timeline(
        spatial_history=spatial_recorder.observations,
        population_history=ecology.recorder.observations,
        trait_name=MAX_SPEED,
        individual_trait_history=trait_recorder.observations,
        event_history=ecology.event_recorder.steps,
        focal_encoding=ContinuousTraitEncoding(
            trait_name=MAX_SPEED,
            label="Maximum speed",
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ),
    )
    output_path = render_portfolio_animation(
        timeline,
        arguments.output,
        quality=arguments.quality,
    )
    print(f"Rendered science-aware cinematic smoke: {output_path}")


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny B1 patchy / B2 max-speed reference ecology and render "
            "only its committed scientific evidence."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/science-aware-cinematic-smoke.mp4"),
        help="Destination .mp4 or .gif path.",
    )
    parser.add_argument(
        "--quality",
        choices=("low", "medium", "high"),
        default="low",
        help="Manim render quality preset.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
