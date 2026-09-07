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
    build_e7_treatment,
    e7_distribution_overlap,
    run_e7_seed_set,
    summarize_e7_starting_condition,
)

E7RunMode = Literal["discovery", "confirmation"]


def run(mode: E7RunMode) -> dict[str, Any]:
    """Run all predeclared E7 starting conditions on the selected seed set."""
    seeds = E7_DISCOVERY_SEEDS if mode == "discovery" else E7_CONFIRMATION_SEEDS
    summaries: dict[int, Any] = {}
    starting_conditions: dict[str, Any] = {}

    for starting_speed in E7_STARTING_SPEEDS:
        treatment = build_e7_treatment(starting_speed=starting_speed)
        outcomes = run_e7_seed_set(
            treatment,
            seeds=seeds,
            run_role=mode,
        )
        summary = summarize_e7_starting_condition(outcomes)
        summaries[starting_speed] = summary
        starting_conditions[str(starting_speed)] = {
            "summary": attrs.asdict(summary),
            "replicates": [attrs.asdict(outcome) for outcome in outcomes],
        }

    overlaps: dict[str, float | None] = {}
    for left_index, left_speed in enumerate(E7_STARTING_SPEEDS):
        for right_speed in E7_STARTING_SPEEDS[left_index + 1 :]:
            overlaps[f"{left_speed}-{right_speed}"] = e7_distribution_overlap(
                summaries[left_speed],
                summaries[right_speed],
            )

    return {
        "analysis_kind": mode,
        "replicate_unit": "one independent simulation run/seed",
        "seeds": list(seeds),
        "starting_speeds": list(E7_STARTING_SPEEDS),
        "starting_conditions": starting_conditions,
        "endpoint_distribution_overlaps": overlaps,
    }


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
