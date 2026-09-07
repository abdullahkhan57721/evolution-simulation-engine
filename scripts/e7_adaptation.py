#!/usr/bin/env python3
"""Run transparent E7 discovery or frozen independent confirmation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import attrs

from evo_engine.experiments.e7_adaptation import (
    E7_CONFIRMATION_SEEDS,
    E7_DISCOVERY_SEEDS,
    E7_STARTING_SPEEDS,
    E7ReplicateOutcome,
    E7StartingConditionSummary,
    build_e7_treatment,
    e7_distribution_overlap,
    run_e7_seed_set,
    summarize_e7_starting_condition,
)

E7RunMode = Literal["discovery", "confirmation"]
E7_REQUIRED_RUN_COUNT = 18
E7_REFERENCE_OCCUPANCY_THRESHOLD = 0.50
E7_DISTRIBUTION_OVERLAP_THRESHOLD = 0.50
E7_BOUNDARY_OCCUPANCY_MAXIMUM = 0.10


def run(mode: E7RunMode) -> dict[str, Any]:
    """Run all predeclared E7 starting conditions on the selected seed set."""
    seeds = E7_DISCOVERY_SEEDS if mode == "discovery" else E7_CONFIRMATION_SEEDS
    outcomes_by_start: dict[int, tuple[E7ReplicateOutcome, ...]] = {}
    summaries: dict[int, E7StartingConditionSummary] = {}
    starting_conditions: dict[str, Any] = {}

    for starting_speed in E7_STARTING_SPEEDS:
        treatment = build_e7_treatment(starting_speed=starting_speed)
        outcomes = run_e7_seed_set(
            treatment,
            seeds=seeds,
            run_role=mode,
        )
        summary = summarize_e7_starting_condition(outcomes)
        outcomes_by_start[starting_speed] = outcomes
        summaries[starting_speed] = summary
        starting_conditions[str(starting_speed)] = {
            "summary": attrs.asdict(summary),
            "replicates": [attrs.asdict(outcome) for outcome in outcomes],
        }

    overlaps = _pairwise_overlaps(summaries)
    payload: dict[str, Any] = {
        "analysis_kind": mode,
        "replicate_unit": "one independent simulation run/seed",
        "seeds": list(seeds),
        "starting_speeds": list(E7_STARTING_SPEEDS),
        "starting_conditions": starting_conditions,
        "endpoint_distribution_overlaps": overlaps,
    }
    if mode == "confirmation":
        payload["confirmation_evaluation"] = _evaluate_confirmation(
            outcomes_by_start,
            overlaps=overlaps,
        )
    return payload


def _pairwise_overlaps(
    summaries: dict[int, E7StartingConditionSummary],
) -> dict[str, float | None]:
    overlaps: dict[str, float | None] = {}
    for left_index, left_speed in enumerate(E7_STARTING_SPEEDS):
        for right_speed in E7_STARTING_SPEEDS[left_index + 1 :]:
            overlaps[f"{left_speed}-{right_speed}"] = e7_distribution_overlap(
                summaries[left_speed],
                summaries[right_speed],
            )
    return overlaps


def _evaluate_confirmation(
    outcomes_by_start: dict[int, tuple[E7ReplicateOutcome, ...]],
    *,
    overlaps: dict[str, float | None],
) -> dict[str, Any]:
    """Apply the criteria frozen on Issue #176 before confirmation execution."""
    results: dict[str, Any] = {}
    all_start_criteria_pass = True
    for starting_speed in E7_STARTING_SPEEDS:
        outcomes = outcomes_by_start[starting_speed]
        observed_seeds = tuple(outcome.provenance.seed for outcome in outcomes)
        if observed_seeds != E7_CONFIRMATION_SEEDS:
            raise ValueError(
                "confirmation evaluation requires the exact predeclared E7 seed set."
            )
        nonextinct_count = sum(
            outcome.final_distribution.population_size > 0 for outcome in outcomes
        )
        directional_count = sum(
            _passes_directional_endpoint(outcome, starting_speed=starting_speed)
            for outcome in outcomes
        )
        reference_count = sum(
            _passes_reference_occupancy(outcome) for outcome in outcomes
        )
        boundary_count = sum(
            _passes_boundary_diagnostic(outcome) for outcome in outcomes
        )
        criterion_passes = {
            "directional_or_bounded_location": directional_count
            >= E7_REQUIRED_RUN_COUNT,
            "majority_reference_region": reference_count >= E7_REQUIRED_RUN_COUNT,
            "boundary_diagnostic": boundary_count >= E7_REQUIRED_RUN_COUNT,
            "nonextinction": nonextinct_count >= E7_REQUIRED_RUN_COUNT,
        }
        all_start_criteria_pass = all_start_criteria_pass and all(
            criterion_passes.values()
        )
        results[str(starting_speed)] = {
            "replicate_count": len(outcomes),
            "nonextinct_count": nonextinct_count,
            "directional_or_bounded_location_count": directional_count,
            "majority_reference_region_count": reference_count,
            "boundary_diagnostic_count": boundary_count,
            "criteria_passed": criterion_passes,
        }

    overlap_passes = {
        pair: value is not None and value >= E7_DISTRIBUTION_OVERLAP_THRESHOLD
        for pair, value in overlaps.items()
    }
    cross_start_similarity_passed = all(overlap_passes.values())
    return {
        "frozen_thresholds": {
            "required_runs": E7_REQUIRED_RUN_COUNT,
            "reference_region_occupancy_minimum": E7_REFERENCE_OCCUPANCY_THRESHOLD,
            "pairwise_distribution_overlap_minimum": E7_DISTRIBUTION_OVERLAP_THRESHOLD,
            "boundary_occupancy_maximum": E7_BOUNDARY_OCCUPANCY_MAXIMUM,
        },
        "starting_conditions": results,
        "pairwise_overlap_passed": overlap_passes,
        "cross_start_similarity_passed": cross_start_similarity_passed,
        "converged": all_start_criteria_pass and cross_start_similarity_passed,
    }


def _passes_directional_endpoint(
    outcome: E7ReplicateOutcome,
    *,
    starting_speed: int,
) -> bool:
    median = outcome.final_distribution.median_speed
    if median is None:
        return False
    if starting_speed == 1:
        return median >= 2
    if starting_speed == 3:
        return 2 <= median <= 4
    if starting_speed == 7:
        return median <= 4
    raise ValueError("starting_speed must be one of the frozen E7 starting speeds.")


def _passes_reference_occupancy(outcome: E7ReplicateOutcome) -> bool:
    frequency = outcome.final_distribution.reference_region_frequency
    return frequency is not None and frequency >= E7_REFERENCE_OCCUPANCY_THRESHOLD


def _passes_boundary_diagnostic(outcome: E7ReplicateOutcome) -> bool:
    frequency = outcome.final_distribution.boundary_frequency
    return frequency is not None and frequency <= E7_BOUNDARY_OCCUPANCY_MAXIMUM


def _format(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.4f}"


def _print_summary(payload: dict[str, Any]) -> None:
    print(f"E7 {payload['analysis_kind']} evidence")
    for starting_speed in payload["starting_speeds"]:
        result = payload["starting_conditions"][str(starting_speed)]
        summary = result["summary"]
        print(
            f"start={starting_speed} "
            f"defined={summary['defined_endpoint_count']}/"
            f"{summary['replicate_count']} "
            f"mean_endpoint_speed={_format(summary['mean_final_mean_speed'])} "
            f"mean_reference_region={_format(summary['mean_reference_region_frequency'])} "
            f"mean_boundary={_format(summary['mean_boundary_frequency'])} "
            f"mean_realized_mutations={summary['mean_realized_mutation_count']:.3f}"
        )
        for replicate in result["replicates"]:
            final = replicate["trait_trajectory"][-1]
            nonzero = [
                [speed, count] for speed, count in enumerate(final["counts"]) if count
            ]
            print(
                f"  seed={replicate['provenance']['seed']} "
                f"pop={final['population_size']} "
                f"mean={_format(_mean_from_counts(final['counts']))} "
                f"region={_format(_region_frequency(final['counts']))} "
                f"mutations={sum(item['count'] for item in replicate['mutation_transitions'] if item['parent_speed'] != item['offspring_speed'])} "
                f"counts={nonzero}"
            )
    print(f"endpoint overlaps={payload['endpoint_distribution_overlaps']}")
    if "confirmation_evaluation" in payload:
        evaluation = payload["confirmation_evaluation"]
        for starting_speed in payload["starting_speeds"]:
            result = evaluation["starting_conditions"][str(starting_speed)]
            print(
                f"criteria start={starting_speed} "
                f"directional={result['directional_or_bounded_location_count']}/24 "
                f"reference={result['majority_reference_region_count']}/24 "
                f"boundary={result['boundary_diagnostic_count']}/24 "
                f"nonextinct={result['nonextinct_count']}/24"
            )
        print(
            "frozen convergence criteria passed="
            f"{evaluation['converged']}"
        )


def _mean_from_counts(counts: list[int]) -> float | None:
    population_size = sum(counts)
    if population_size == 0:
        return None
    return sum(speed * count for speed, count in enumerate(counts)) / population_size


def _region_frequency(counts: list[int]) -> float | None:
    population_size = sum(counts)
    if population_size == 0:
        return None
    return sum(counts[speed] for speed in (2, 3, 4)) / population_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("discovery", "confirmation"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = run(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _print_summary(payload)


if __name__ == "__main__":
    main()
