#!/usr/bin/env python3
"""Run transparent E4 discovery, confirmation, or founder-order sanity evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import attrs

from evo_engine.experiments.e4_selection import (
    E4_CONFIRMATION_SEEDS,
    E4_DISCOVERY_SEEDS,
    E4_FOCAL_SPEEDS,
    E4_LABEL_SANITY_SEEDS,
    E4_REVERSED_FOUNDER_ORDER,
    build_e4_treatment,
    founder_order_for_replicate,
    run_e4_replicate,
    run_e4_seed_set,
    summarize_e4_environment,
    validate_e4_environment_treatment_integrity,
    validate_e4_founder_order_integrity,
)

E4RunMode = Literal["discovery", "confirmation", "sanity"]


def _outcome_payload(outcome: object) -> dict[str, Any]:
    """Return one attrs replicate as transparent JSON-compatible evidence."""
    return attrs.asdict(outcome)


def _run_canonical(mode: Literal["discovery", "confirmation"]) -> dict[str, Any]:
    seeds = E4_DISCOVERY_SEEDS if mode == "discovery" else E4_CONFIRMATION_SEEDS
    role = mode
    local = run_e4_seed_set(
        environment="local_resource",
        seeds=seeds,
        run_role=role,
    )
    corridor = run_e4_seed_set(
        environment="separated_corridor",
        seeds=seeds,
        run_role=role,
    )
    for index, seed in enumerate(seeds):
        order = founder_order_for_replicate(index)
        validate_e4_environment_treatment_integrity(
            build_e4_treatment(
                environment="local_resource",
                founder_speed_order=order,
            ),
            build_e4_treatment(
                environment="separated_corridor",
                founder_speed_order=order,
            ),
        )
        if local[index].provenance.seed != seed or corridor[index].provenance.seed != seed:
            raise RuntimeError("E4 paired environment evidence lost declared seed order.")

    local_summary = summarize_e4_environment(local)
    corridor_summary = summarize_e4_environment(corridor)
    return {
        "analysis_kind": mode,
        "replicate_unit": "simulation run",
        "focal_speeds": list(E4_FOCAL_SPEEDS),
        "seeds": list(seeds),
        "local_resource": {
            "summary": attrs.asdict(local_summary),
            "replicates": [_outcome_payload(outcome) for outcome in local],
        },
        "separated_corridor": {
            "summary": attrs.asdict(corridor_summary),
            "replicates": [_outcome_payload(outcome) for outcome in corridor],
        },
    }


def _run_sanity() -> dict[str, Any]:
    canonical = []
    reversed_order = []
    for seed in E4_LABEL_SANITY_SEEDS:
        canonical_treatment = build_e4_treatment(
            environment="separated_corridor",
            founder_speed_order=E4_FOCAL_SPEEDS,
        )
        reversed_treatment = build_e4_treatment(
            environment="separated_corridor",
            founder_speed_order=E4_REVERSED_FOUNDER_ORDER,
        )
        validate_e4_founder_order_integrity(canonical_treatment, reversed_treatment)
        canonical.append(
            run_e4_replicate(canonical_treatment, seed=seed, run_role=None)
        )
        reversed_order.append(
            run_e4_replicate(reversed_treatment, seed=seed, run_role=None)
        )
    return {
        "analysis_kind": "founder_order_sanity",
        "replicate_unit": "simulation run",
        "environment": "separated_corridor",
        "declared_difference": "founder speed-to-ID order only",
        "seeds": list(E4_LABEL_SANITY_SEEDS),
        "canonical_order": {
            "summary": attrs.asdict(summarize_e4_environment(canonical)),
            "replicates": [_outcome_payload(outcome) for outcome in canonical],
        },
        "reversed_order": {
            "summary": attrs.asdict(summarize_e4_environment(reversed_order)),
            "replicates": [_outcome_payload(outcome) for outcome in reversed_order],
        },
    }


def run(mode: E4RunMode) -> dict[str, Any]:
    """Run one explicitly labeled E4 evidence phase."""
    if mode == "sanity":
        return _run_sanity()
    return _run_canonical(mode)


def _format_frequency(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.3f}"


def _print_summary(payload: dict[str, Any]) -> None:
    print(f"E4 {payload['analysis_kind']} evidence")
    if payload["analysis_kind"] == "founder_order_sanity":
        groups = ("canonical_order", "reversed_order")
    else:
        groups = ("local_resource", "separated_corridor")
    for group in groups:
        print(group)
        summary = payload[group]["summary"]
        final_values = summary["mean_final_frequencies"]
        changes = summary["mean_frequency_changes"]
        births = summary["mean_births_by_speed"]
        resources = summary["mean_resources_by_speed"]
        movement = summary["mean_realized_distance_by_speed"]
        energy = summary["mean_locomotion_energy_by_speed"]
        for index, speed in enumerate(E4_FOCAL_SPEEDS):
            print(
                f"  speed={speed} "
                f"mean_final_frequency={_format_frequency(final_values[index])} "
                f"mean_delta={_format_frequency(changes[index])} "
                f"mean_births={births[index]:.3f} "
                f"mean_resources={resources[index]:.3f} "
                f"mean_move={movement[index]:.3f} "
                f"mean_move_energy={energy[index]:.3f}"
            )
        print(
            f"  defined_endpoints={summary['defined_endpoint_count']}/"
            f"{summary['replicate_count']} extinctions={summary['extinction_count']}"
        )
        for replicate in payload[group]["replicates"]:
            final = replicate["focal_trajectory"][-1]
            print(
                f"    seed={replicate['provenance']['seed']} "
                f"order={replicate['treatment']['founder_speed_order']} "
                f"final_counts={final['counts']} "
                f"final_frequencies={final['frequencies']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("discovery", "confirmation", "sanity"),
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
