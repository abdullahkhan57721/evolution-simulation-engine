#!/usr/bin/env python3
"""Run the frozen B3 independent confirmation and write transparent evidence."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import attrs

from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunSummary,
    run_b3_flagship,
    run_b3_matched_pair,
    summarize_b3_run,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_COUNTERBALANCE_SEEDS,
    B3_DISCOVERY_SEEDS,
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_MAX_STEPS,
    B3_PRIMARY_STEP,
    B3_RESOURCE_DEPOSITS_PER_STEP,
    B3_RESOURCE_GENERATION_AMOUNT,
    build_b3_flagship_specification,
)


def _required_frequency(summary: B3RunSummary) -> float:
    value = summary.primary_high_speed_frequency
    if value is None:
        raise RuntimeError(
            f"{summary.environment} seed {summary.seed} is extinct at the "
            f"predeclared primary step {B3_PRIMARY_STEP}."
        )
    return value


def _mean(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate a B3 confirmation mean from no values.")
    return sum(values) / len(values)


def _run_sensitivity(seed: int) -> B3RunSummary:
    specification = build_b3_flagship_specification(
        seed=seed,
        environment="broad_patch",
    )
    return summarize_b3_run(run_b3_flagship(specification))


def _pair_payload(pair: B3MatchedPairSummary) -> dict[str, Any]:
    return {
        "seed": pair.seed,
        "founder_assignment": pair.founder_assignment,
        "primary_effect": pair.primary_effect,
        "control": attrs.asdict(pair.control),
        "treatment": attrs.asdict(pair.treatment),
    }


def _select_representative_seed(
    pairs: tuple[B3MatchedPairSummary, ...],
) -> tuple[int, float]:
    effects = [pair.primary_effect for pair in pairs]
    if any(effect is None for effect in effects):
        raise RuntimeError(
            "Representative selection requires non-extinct matched pairs at step 30."
        )
    numeric_effects = [float(effect) for effect in effects if effect is not None]
    median_effect = statistics.median(numeric_effects)
    eligible = [
        pair
        for pair in pairs
        if pair.primary_effect is not None
        and pair.control.primary_high_speed_frequency is not None
        and pair.treatment.primary_high_speed_frequency is not None
        and pair.treatment.mechanism_episodes
    ]
    if not eligible:
        raise RuntimeError(
            "No confirmation seed satisfies the predeclared representative-run rule."
        )
    selected = min(
        eligible,
        key=lambda pair: (abs(float(pair.primary_effect) - median_effect), pair.seed),
    )
    return selected.seed, median_effect


def _representative_episode_payload(pair: B3MatchedPairSummary) -> list[dict[str, Any]]:
    selected = []
    for speed in (B3_LOW_MAX_SPEED, B3_HIGH_MAX_SPEED):
        episode = next(
            (
                candidate
                for candidate in pair.treatment.mechanism_episodes
                if candidate.max_speed_capacity == speed
            ),
            None,
        )
        if episode is not None:
            selected.append(attrs.asdict(episode))
    if not selected:
        selected.append(attrs.asdict(pair.treatment.mechanism_episodes[0]))
    return selected


def _run_all_cases() -> tuple[
    tuple[B3MatchedPairSummary, ...],
    tuple[B3RunSummary, ...],
    tuple[B3MatchedPairSummary, ...],
]:
    pairs = tuple(run_b3_matched_pair(seed=seed) for seed in B3_CONFIRMATION_SEEDS)
    sensitivity = tuple(_run_sensitivity(seed) for seed in B3_CONFIRMATION_SEEDS)
    counterbalanced = tuple(
        run_b3_matched_pair(seed=seed, founder_assignment="swapped")
        for seed in B3_COUNTERBALANCE_SEEDS
    )
    return pairs, sensitivity, counterbalanced


def _aggregate_confirmation(
    pairs: tuple[B3MatchedPairSummary, ...],
    sensitivity: tuple[B3RunSummary, ...],
    counterbalanced: tuple[B3MatchedPairSummary, ...],
) -> dict[str, float | int]:
    control_frequencies = [_required_frequency(pair.control) for pair in pairs]
    treatment_frequencies = [_required_frequency(pair.treatment) for pair in pairs]
    broad_frequencies = [_required_frequency(run) for run in sensitivity]
    effects = [
        treatment - control
        for control, treatment in zip(
            control_frequencies,
            treatment_frequencies,
            strict=True,
        )
    ]
    return {
        "uniform_step_30_mean_high_speed_allele_frequency": _mean(
            control_frequencies
        ),
        "compact_step_30_mean_high_speed_allele_frequency": _mean(
            treatment_frequencies
        ),
        "broad_patch_step_30_mean_high_speed_allele_frequency": _mean(
            broad_frequencies
        ),
        "mean_compact_minus_uniform_effect": _mean(effects),
        "compact_greater_than_uniform_seed_count": sum(effect > 0 for effect in effects),
        "uniform_low_speed_founder_rrs_win_count": sum(
            pair.control.founder_reproductive_success.low_speed_mean
            > pair.control.founder_reproductive_success.high_speed_mean
            for pair in pairs
        ),
        "compact_high_speed_founder_rrs_win_count": sum(
            pair.treatment.founder_reproductive_success.high_speed_mean
            > pair.treatment.founder_reproductive_success.low_speed_mean
            for pair in pairs
        ),
        "counterbalance_compact_win_count": sum(
            pair.primary_effect is not None and pair.primary_effect > 0
            for pair in counterbalanced
        ),
    }


def _generation_is_matched(pair: B3MatchedPairSummary) -> bool:
    control = pair.control.resource_generation_audit
    treatment = pair.treatment.resource_generation_audit
    expected_count = B3_RESOURCE_DEPOSITS_PER_STEP * B3_MAX_STEPS
    expected_amount = expected_count * B3_RESOURCE_GENERATION_AMOUNT
    return (
        control.generation_event_count == expected_count
        and treatment.generation_event_count == expected_count
        and control.total_generated_amount == expected_amount
        and treatment.total_generated_amount == expected_amount
    )


def _predeclared_checks(
    pairs: tuple[B3MatchedPairSummary, ...],
    aggregate: dict[str, float | int],
) -> dict[str, bool]:
    control_mean = float(
        aggregate["uniform_step_30_mean_high_speed_allele_frequency"]
    )
    treatment_mean = float(
        aggregate["compact_step_30_mean_high_speed_allele_frequency"]
    )
    broad_mean = float(
        aggregate["broad_patch_step_30_mean_high_speed_allele_frequency"]
    )
    return {
        "all_primary_pairs_survive": all(
            pair.control.primary_high_speed_frequency is not None
            and pair.treatment.primary_high_speed_frequency is not None
            for pair in pairs
        ),
        "compact_beats_uniform_at_least_6_of_8": int(
            aggregate["compact_greater_than_uniform_seed_count"]
        )
        >= 6,
        "mean_compact_above_mean_uniform": treatment_mean > control_mean,
        "mean_crosses_founder_baseline_in_opposite_directions": (
            treatment_mean > 0.5 and control_mean < 0.5
        ),
        "uniform_founder_rrs_favors_low_at_least_6_of_8": int(
            aggregate["uniform_low_speed_founder_rrs_win_count"]
        )
        >= 6,
        "compact_founder_rrs_favors_high_at_least_6_of_8": int(
            aggregate["compact_high_speed_founder_rrs_win_count"]
        )
        >= 6,
        "renewable_generation_quantity_is_matched": all(
            _generation_is_matched(pair) for pair in pairs
        ),
        "compact_renewable_generation_stays_inside_compact_support": all(
            pair.treatment.resource_generation_audit.compact_support_fraction == 1.0
            for pair in pairs
        ),
        "uniform_renewable_generation_is_not_confined_to_compact_support": all(
            pair.control.resource_generation_audit.compact_support_fraction is not None
            and pair.control.resource_generation_audit.compact_support_fraction < 1.0
            for pair in pairs
        ),
        "broad_patch_weakens_compact_advantage_in_aggregate": broad_mean
        < treatment_mean,
        "swapped_founder_assignment_preserves_patch_advantage": int(
            aggregate["counterbalance_compact_win_count"]
        )
        == len(B3_COUNTERBALANCE_SEEDS),
    }


def _representative_selection(
    pairs: tuple[B3MatchedPairSummary, ...],
) -> dict[str, Any]:
    representative_seed, median_effect = _select_representative_seed(pairs)
    representative_pair = next(
        pair for pair in pairs if pair.seed == representative_seed
    )
    return {
        "median_paired_effect": median_effect,
        "selected_seed": representative_seed,
        "rule": (
            "closest paired effect to confirmation median among non-extinct "
            "pairs with a committed targeted-movement/resource-consumption "
            "episode; lower seed breaks exact ties"
        ),
        "treatment_episodes": _representative_episode_payload(representative_pair),
    }


def _confirmation_payload(
    *,
    pairs: tuple[B3MatchedPairSummary, ...],
    sensitivity: tuple[B3RunSummary, ...],
    counterbalanced: tuple[B3MatchedPairSummary, ...],
    aggregate: dict[str, float | int],
    checks: dict[str, bool],
) -> dict[str, Any]:
    return {
        "analysis_kind": "independent_confirmation",
        "frozen_before_confirmation": True,
        "focal_trait": "max_speed",
        "focal_trait_semantics": "genetic-phenotype maximum movement capacity",
        "low_speed_capacity": B3_LOW_MAX_SPEED,
        "high_speed_capacity": B3_HIGH_MAX_SPEED,
        "primary_step_index": B3_PRIMARY_STEP,
        "discovery_seeds": list(B3_DISCOVERY_SEEDS),
        "confirmation_seeds": list(B3_CONFIRMATION_SEEDS),
        "counterbalance_seeds": list(B3_COUNTERBALANCE_SEEDS),
        "design": "matched/blocked-by-seed; RNG streams may diverge after treatment",
        "replicate_unit": "simulation run",
        "resource_measurement_note": (
            "SpatialObservation resources describe total committed world resource "
            "state, including decomposition returns. Exact renewable-generation "
            "placement is audited separately from committed ResourceGeneration events."
        ),
        "confirmation_pairs": [_pair_payload(pair) for pair in pairs],
        "radius_2_sensitivity": [attrs.asdict(run) for run in sensitivity],
        "counterbalanced_pairs": [_pair_payload(pair) for pair in counterbalanced],
        "aggregate": aggregate,
        "predeclared_checks": checks,
        "representative_selection": _representative_selection(pairs),
    }


def run_confirmation() -> tuple[dict[str, Any], tuple[str, ...]]:
    """Run all frozen confirmation cases and evaluate the declared criteria."""
    if set(B3_DISCOVERY_SEEDS) & set(B3_CONFIRMATION_SEEDS):
        raise RuntimeError("B3 discovery and confirmation seed sets must be disjoint.")
    if not set(B3_COUNTERBALANCE_SEEDS) <= set(B3_CONFIRMATION_SEEDS):
        raise RuntimeError("B3 counterbalance seeds must be confirmation seeds.")

    pairs, sensitivity, counterbalanced = _run_all_cases()
    aggregate = _aggregate_confirmation(pairs, sensitivity, counterbalanced)
    checks = _predeclared_checks(pairs, aggregate)
    payload = _confirmation_payload(
        pairs=pairs,
        sensitivity=sensitivity,
        counterbalanced=counterbalanced,
        aggregate=aggregate,
        checks=checks,
    )
    failures = tuple(name for name, passed in checks.items() if not passed)
    return payload, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/b3-confirmation/b3-confirmation.json"),
    )
    args = parser.parse_args()

    payload, failures = run_confirmation()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    if failures:
        print("B3 independent confirmation failed predeclared checks:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("B3 independent confirmation passed every predeclared check.")


if __name__ == "__main__":
    main()
