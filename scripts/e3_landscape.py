#!/usr/bin/env python3
"""Run transparent E3 discovery, confirmation, or mechanism sensitivity evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import attrs

from evo_engine.experiments.e3_performance import (
    E3_CONFIRMATION_SEEDS,
    E3_DISCOVERY_SEEDS,
    E3_SENSITIVITY_SEEDS,
    E3_SPEED_GRID,
    E3ReplicateOutcome,
    build_e3_treatment,
    run_e3_replicates,
    summarize_e3_treatment,
    validate_e3_cost_sensitivity_integrity,
    validate_e3_environment_treatment_integrity,
    validate_e3_speed_treatment_integrity,
)

E3RunMode = Literal["discovery", "confirmation", "sensitivity"]


def _outcome_payload(outcome: E3ReplicateOutcome) -> dict[str, Any]:
    """Return one replicate as transparent JSON-compatible evidence."""
    return attrs.asdict(outcome)


def _run_environment(
    *,
    environment: Literal["local_resource", "separated_corridor"],
    seeds: tuple[int, ...],
    role: Literal["discovery", "confirmation"],
    locomotion_cost_coefficient: int = 1,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    baseline = build_e3_treatment(
        max_speed=E3_SPEED_GRID[0],
        environment=environment,
        locomotion_cost_coefficient=locomotion_cost_coefficient,
    )
    for max_speed in E3_SPEED_GRID:
        treatment = build_e3_treatment(
            max_speed=max_speed,
            environment=environment,
            locomotion_cost_coefficient=locomotion_cost_coefficient,
        )
        validate_e3_speed_treatment_integrity(baseline, treatment)
        outcomes = run_e3_replicates(treatment, seeds=seeds, run_role=role)
        summary = summarize_e3_treatment(outcomes)
        results.append(
            {
                "max_speed": max_speed,
                "summary": attrs.asdict(summary),
                "replicates": [_outcome_payload(outcome) for outcome in outcomes],
            }
        )
    return results


def _run_canonical(mode: Literal["discovery", "confirmation"]) -> dict[str, Any]:
    seeds = E3_DISCOVERY_SEEDS if mode == "discovery" else E3_CONFIRMATION_SEEDS
    local = _run_environment(
        environment="local_resource",
        seeds=seeds,
        role=mode,
    )
    corridor = _run_environment(
        environment="separated_corridor",
        seeds=seeds,
        role=mode,
    )
    for max_speed in E3_SPEED_GRID:
        validate_e3_environment_treatment_integrity(
            build_e3_treatment(max_speed=max_speed, environment="local_resource"),
            build_e3_treatment(
                max_speed=max_speed,
                environment="separated_corridor",
            ),
        )
    return {
        "analysis_kind": mode,
        "replicate_unit": "simulation run",
        "speed_grid": list(E3_SPEED_GRID),
        "seeds": list(seeds),
        "local_resource": local,
        "separated_corridor": corridor,
    }


def _run_sensitivity() -> dict[str, Any]:
    canonical: list[dict[str, Any]] = []
    zero_cost: list[dict[str, Any]] = []
    for max_speed in E3_SPEED_GRID:
        control = build_e3_treatment(
            max_speed=max_speed,
            environment="separated_corridor",
        )
        sensitivity = build_e3_treatment(
            max_speed=max_speed,
            environment="separated_corridor",
            locomotion_cost_coefficient=0,
        )
        validate_e3_cost_sensitivity_integrity(control, sensitivity)
        control_outcomes = run_e3_replicates(
            control,
            seeds=E3_SENSITIVITY_SEEDS,
            run_role=None,
        )
        sensitivity_outcomes = run_e3_replicates(
            sensitivity,
            seeds=E3_SENSITIVITY_SEEDS,
            run_role=None,
        )
        canonical.append(
            {
                "max_speed": max_speed,
                "summary": attrs.asdict(summarize_e3_treatment(control_outcomes)),
                "replicates": [
                    _outcome_payload(outcome) for outcome in control_outcomes
                ],
            }
        )
        zero_cost.append(
            {
                "max_speed": max_speed,
                "summary": attrs.asdict(summarize_e3_treatment(sensitivity_outcomes)),
                "replicates": [
                    _outcome_payload(outcome) for outcome in sensitivity_outcomes
                ],
            }
        )
    return {
        "analysis_kind": "mechanism_sensitivity",
        "replicate_unit": "simulation run",
        "declared_difference": "locomotion cost coefficient 1 -> 0",
        "speed_grid": list(E3_SPEED_GRID),
        "seeds": list(E3_SENSITIVITY_SEEDS),
        "canonical_corridor": canonical,
        "zero_cost_corridor": zero_cost,
    }


def run(mode: E3RunMode) -> dict[str, Any]:
    """Run one explicitly labeled E3 evidence phase."""
    if mode == "sensitivity":
        return _run_sensitivity()
    return _run_canonical(mode)


def _print_summary(payload: dict[str, Any]) -> None:
    print(f"E3 {payload['analysis_kind']} evidence")
    if payload["analysis_kind"] == "mechanism_sensitivity":
        groups = ("canonical_corridor", "zero_cost_corridor")
    else:
        groups = ("local_resource", "separated_corridor")
    for group in groups:
        print(group)
        for entry in payload[group]:
            summary = entry["summary"]
            print(
                f"  speed={entry['max_speed']:>2} "
                f"mean_births={summary['mean_cumulative_birth_count']:.3f} "
                f"births={summary['birth_counts']} "
                f"mean_consumed={summary['mean_total_resource_consumed']:.3f} "
                f"mean_move={summary['mean_total_realized_distance']:.3f} "
                f"mean_move_energy="
                f"{summary['mean_total_locomotion_energy_expenditure']:.3f} "
                f"extinctions={summary['extinction_count']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("discovery", "confirmation", "sensitivity"),
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
