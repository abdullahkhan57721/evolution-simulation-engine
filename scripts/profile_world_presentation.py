#!/usr/bin/env python3
"""Measure interactive world preparation and Plotly rendering on real histories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
from time import perf_counter

import attrs

from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch
from evo_engine.engine import Simulation
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED
from evo_engine.observation import SpatialObservation, SpatialRecorder
from evo_engine.presets import (
    ReferenceEcologyConfig,
    build_balanced_reference_trait_world,
    build_reference_ecology,
)
from evo_engine.ui.world_presentation import build_world_presentation
from evo_engine.ui.world_renderer import world_presentation_figure


def main() -> None:
    """Measure B1- and B2-representative committed histories without gating speed."""
    args = _parse_args()
    results = (
        _measure_history("b1-patchy-resources", _patchy_history(), repeats=args.repeats),
        _measure_history("b2-speed-tradeoff", _speed_tradeoff_history(), repeats=args.repeats),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for result in results:
        print(f"\n=== {result['scenario']} ===")
        print(f"committed frames:          {result['frames']}")
        print(f"max active organisms:      {result['max_active_organisms']}")
        print(f"max resource deposits:     {result['max_resource_deposits']}")
        print(f"prep median / frame (ms):  {result['prep_median_ms_per_frame']:.4f}")
        print(f"Plotly median / frame (ms): {result['plotly_median_ms_per_frame']:.4f}")
    print(f"\nbenchmark JSON: {output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure UI-only world-presentation preparation and Plotly figure building "
            "for deterministic B1/B2 representative histories. No performance "
            "threshold is enforced."
        )
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--output",
        default="outputs/performance/world-presentation-benchmark.json",
    )
    return parser.parse_args()


def _patchy_history() -> tuple[SpatialObservation, ...]:
    config = ReferenceEcologyConfig(
        width=16,
        height=16,
        initial_population=20,
        max_steps=30,
        seed=61,
        resource_deposits_per_step=16,
        resource_placement_model=PatchyResourcePlacement(
            patches=(
                ResourcePatch(center_x=3, center_y=12, radius=2, weight=1),
                ResourcePatch(center_x=12, center_y=3, radius=2, weight=2),
            )
        ),
    )
    recorder = SpatialRecorder()
    ecology = build_reference_ecology(config, additional_observers=(recorder,))
    ecology.engine.run(ecology.simulation)
    return recorder.observations


def _speed_tradeoff_history() -> tuple[SpatialObservation, ...]:
    config = ReferenceEcologyConfig(
        initial_population=20,
        max_steps=30,
        seed=67,
        mutation_probability_ppm=0,
    )
    recorder = SpatialRecorder()
    ecology = build_reference_ecology(config, additional_observers=(recorder,))
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    world = build_balanced_reference_trait_world(
        architecture,
        trait_name=MAX_SPEED,
        variant_values=(1, 4),
        config=config,
    )
    simulation = Simulation(
        initial_domain_state=world,
        seed=config.seed,
        context=ecology.simulation.context,
    )
    ecology.engine.run(simulation)
    return recorder.observations


def _measure_history(
    scenario: str,
    history: tuple[SpatialObservation, ...],
    *,
    repeats: int,
) -> dict[str, int | float | str]:
    if repeats < 1:
        raise ValueError("repeats must be at least 1.")
    if not history:
        raise ValueError("history must contain at least one committed frame.")

    presentations = tuple(
        build_world_presentation(
            history,
            step_index=frame.step_index,
            show_trails=True,
            trail_length=8,
        )
        for frame in history
    )
    prep_durations = tuple(
        _time_presentation_pass(history) for _ in range(repeats)
    )
    plotly_durations = tuple(
        _time_plotly_pass(presentations) for _ in range(repeats)
    )
    frame_count = len(history)
    return {
        "scenario": scenario,
        "frames": frame_count,
        "max_active_organisms": max(len(frame.organisms) for frame in history),
        "max_resource_deposits": max(len(frame.resources) for frame in history),
        "repeats": repeats,
        "prep_median_ms_per_frame": 1000.0 * median(prep_durations) / frame_count,
        "plotly_median_ms_per_frame": 1000.0 * median(plotly_durations) / frame_count,
    }


def _time_presentation_pass(history: tuple[SpatialObservation, ...]) -> float:
    started = perf_counter()
    for frame in history:
        build_world_presentation(
            history,
            step_index=frame.step_index,
            show_trails=True,
            trail_length=8,
        )
    return perf_counter() - started


def _time_plotly_pass(presentations: tuple[object, ...]) -> float:
    started = perf_counter()
    for presentation in presentations:
        figure = world_presentation_figure(presentation)  # type: ignore[arg-type]
        figure.to_plotly_json()
    return perf_counter() - started


if __name__ == "__main__":
    main()
