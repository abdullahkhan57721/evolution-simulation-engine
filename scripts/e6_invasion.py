#!/usr/bin/env python3
"""Run transparent E6 discovery or independent confirmation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import attrs

from evo_engine.experiments.e6_invasion import (
    E6_CONFIRMATION_SEEDS,
    E6_DISCOVERY_SEEDS,
    E6_RECIPROCAL_PAIRS,
    compare_e6_matched_invasion,
    run_e6_seed_set,
    summarize_e6_arm,
)

E6RunMode = Literal["discovery", "confirmation"]


def run(mode: E6RunMode) -> dict[str, Any]:
    """Run both reciprocal E6 invasion pairs on the declared seed set."""
    seeds = E6_DISCOVERY_SEEDS if mode == "discovery" else E6_CONFIRMATION_SEEDS
    resident_results: dict[str, Any] = {}
    for resident_speed, mutant_speed in E6_RECIPROCAL_PAIRS:
        pairs = run_e6_seed_set(
            resident_speed=resident_speed,
            mutant_speed=mutant_speed,
            seeds=seeds,
            run_role=mode,
        )
        neutral_outcomes = tuple(pair.neutral for pair in pairs)
        mutant_outcomes = tuple(pair.mutant for pair in pairs)
        neutral_summary = summarize_e6_arm(neutral_outcomes)
        mutant_summary = summarize_e6_arm(mutant_outcomes)
        comparison = compare_e6_matched_invasion(neutral_summary, mutant_summary)
        resident_results[str(resident_speed)] = {
            "mutant_speed": mutant_speed,
            "neutral": {
                "summary": attrs.asdict(neutral_summary),
                "replicates": [attrs.asdict(value) for value in neutral_outcomes],
            },
            "mutant": {
                "summary": attrs.asdict(mutant_summary),
                "replicates": [attrs.asdict(value) for value in mutant_outcomes],
            },
            "matched_comparison": attrs.asdict(comparison),
        }
    return {
        "analysis_kind": mode,
        "replicate_unit": "seed-level resident burn-in with paired neutral/mutant arms",
        "seeds": list(seeds),
        "reciprocal_pairs": [list(pair) for pair in E6_RECIPROCAL_PAIRS],
        "resident_backgrounds": resident_results,
    }


def _format(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.4f}"


def _print_summary(payload: dict[str, Any]) -> None:
    print(f"E6 {payload['analysis_kind']} evidence")
    for resident_speed, result in payload["resident_backgrounds"].items():
        mutant_speed = result["mutant_speed"]
        neutral = result["neutral"]["summary"]
        mutant = result["mutant"]["summary"]
        comparison = result["matched_comparison"]
        print(f"resident={resident_speed} mutant={mutant_speed}")
        print(
            "  neutral "
            f"mean_delta_rare={_format(neutral['mean_rare_frequency_change'])} "
            f"expand={neutral['rare_expansion_proportion']:.3f} "
            f"loss={neutral['rare_loss_proportion']:.3f} "
            f"births={neutral['mean_rare_birth_count']:.3f}"
        )
        print(
            "  mutant  "
            f"mean_delta_rare={_format(mutant['mean_rare_frequency_change'])} "
            f"expand={mutant['rare_expansion_proportion']:.3f} "
            f"loss={mutant['rare_loss_proportion']:.3f} "
            f"births={mutant['mean_rare_birth_count']:.3f}"
        )
        print(
            "  paired  "
            f"mean_contrast={_format(comparison['mean_paired_frequency_contrast'])} "
            f"positive={_format(comparison['positive_pair_proportion'])} "
            f"negative={_format(comparison['negative_pair_proportion'])}"
        )
        for arm in ("neutral", "mutant"):
            print(f"    {arm} replicate endpoints")
            for replicate in result[arm]["replicates"]:
                final = replicate["trajectory"][-1]
                print(
                    f"      seed={replicate['provenance']['seed']} "
                    f"checkpoint_pop={replicate['burn_in_checkpoint']['population_size']} "
                    f"initial_rare={replicate['intervention']['initial_rare_frequency']:.4f} "
                    f"final_counts={final['counts']} "
                    f"final_freq={final['frequencies']} "
                    f"expand_step={replicate['rare_expansion']['observed_step_index']} "
                    f"loss_step={replicate['rare_loss']['observed_step_index']}"
                )


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
