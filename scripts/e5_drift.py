#!/usr/bin/env python3
"""Run transparent E5 discovery or confirmation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import attrs

from evo_engine.experiments.e5_drift import (
    E5_CONFIRMATION_SEEDS,
    E5_DISCOVERY_SEEDS,
    E5_FOUNDER_COUNTS,
    E5_WEAK_PAIR,
    E5_WEAK_PAIR_ALTERNATIVE,
    compare_e5_weak_to_neutral,
    run_e5_seed_set,
    summarize_e5_regime,
)

E5RunMode = Literal["discovery", "confirmation"]
E5PairName = Literal["3-4", "3-2"]


def _pair(name: E5PairName) -> tuple[int, int]:
    return E5_WEAK_PAIR if name == "3-4" else E5_WEAK_PAIR_ALTERNATIVE


def run(mode: E5RunMode, *, weak_pair: E5PairName = "3-4") -> dict[str, Any]:
    """Run the declared E5 population-size matrix using one weak pair."""
    seeds = E5_DISCOVERY_SEEDS if mode == "discovery" else E5_CONFIRMATION_SEEDS
    role = mode
    pair = _pair(weak_pair)
    regimes: dict[str, Any] = {}
    for founder_count in E5_FOUNDER_COUNTS:
        neutral_outcomes = run_e5_seed_set(
            mode="neutral",
            founder_count=founder_count,
            seeds=seeds,
            run_role=role,
            weak_pair=pair,
        )
        weak_outcomes = run_e5_seed_set(
            mode="weak_selection",
            founder_count=founder_count,
            seeds=seeds,
            run_role=role,
            weak_pair=pair,
        )
        neutral_summary = summarize_e5_regime(neutral_outcomes)
        weak_summary = summarize_e5_regime(weak_outcomes)
        comparison = compare_e5_weak_to_neutral(neutral_summary, weak_summary)
        regimes[str(founder_count)] = {
            "neutral": {
                "summary": attrs.asdict(neutral_summary),
                "replicates": [attrs.asdict(value) for value in neutral_outcomes],
            },
            "weak_selection": {
                "summary": attrs.asdict(weak_summary),
                "replicates": [attrs.asdict(value) for value in weak_outcomes],
            },
            "weak_vs_neutral": attrs.asdict(comparison),
        }
    return {
        "analysis_kind": mode,
        "replicate_unit": "simulation run",
        "founder_counts": list(E5_FOUNDER_COUNTS),
        "seeds": list(seeds),
        "weak_pair": list(pair),
        "regimes": regimes,
    }


def _format(value: float | None) -> str:
    return "undefined" if value is None else f"{value:.4f}"


def _print_summary(payload: dict[str, Any]) -> None:
    print(
        f"E5 {payload['analysis_kind']} evidence "
        f"weak_pair={tuple(payload['weak_pair'])}"
    )
    for founder_count in payload["founder_counts"]:
        regime = payload["regimes"][str(founder_count)]
        neutral = regime["neutral"]["summary"]
        weak = regime["weak_selection"]["summary"]
        comparison = regime["weak_vs_neutral"]
        print(f"founders={founder_count}")
        print(
            "  neutral "
            f"mean_delta_A={_format(neutral['mean_group_a_frequency_change'])} "
            f"sd_delta_A={_format(neutral['stddev_group_a_frequency_change'])} "
            f"A_loss={neutral['group_a_loss_proportion']:.3f} "
            f"B_loss={neutral['group_b_loss_proportion']:.3f} "
            f"fixation={neutral['any_fixation_proportion']:.3f} "
            f"extinction={neutral['extinction_proportion']:.3f}"
        )
        print(
            "  weak "
            f"mean_delta_A={_format(weak['mean_group_a_frequency_change'])} "
            f"A_increase={_format(weak['group_a_increase_proportion'])} "
            f"A_decrease={_format(weak['group_a_decrease_proportion'])} "
            f"A_loss={weak['group_a_loss_proportion']:.3f} "
            f"fixation={weak['any_fixation_proportion']:.3f} "
            f"extinction={weak['extinction_proportion']:.3f} "
            f"signal_to_neutral_sd={_format(comparison['signal_to_neutral_sd'])}"
        )
        for arm in ("neutral", "weak_selection"):
            print(f"    {arm} replicate endpoints")
            for replicate in regime[arm]["replicates"]:
                final = replicate["trajectory"][-1]
                print(
                    f"      seed={replicate['provenance']['seed']} "
                    f"phase={replicate['treatment']['assignment_phase']} "
                    f"counts={final['counts']} "
                    f"frequencies={final['frequencies']} "
                    f"fixation_step={replicate['fixation']['observed_step_index']} "
                    f"winner={replicate['fixation_winner']} "
                    f"extinction_step={replicate['extinction']['observed_step_index']}"
                )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("discovery", "confirmation"),
        required=True,
    )
    parser.add_argument(
        "--weak-pair",
        choices=("3-4", "3-2"),
        default="3-4",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = run(args.mode, weak_pair=args.weak_pair)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _print_summary(payload)


if __name__ == "__main__":
    main()
