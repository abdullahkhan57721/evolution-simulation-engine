#!/usr/bin/env python3
"""Benchmark and profile deterministic reference-ecology scenarios."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import attrs

from evo_engine.experiments.performance import (
    REFERENCE_CORE_BASELINE,
    REFERENCE_OBSERVED_BASELINE,
    ReferenceBenchmarkResult,
    ReferencePerformanceScenario,
    benchmark_reference_scenario,
    profile_reference_scenario,
)

_SCENARIOS = {
    "core": REFERENCE_CORE_BASELINE,
    "observed": REFERENCE_OBSERVED_BASELINE,
}


def main() -> None:
    """Run requested reference benchmarks and write profiler artifacts."""
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = (
        tuple(_SCENARIOS.values())
        if args.scenario == "all"
        else (_SCENARIOS[args.scenario],)
    )
    for scenario in scenarios:
        _measure_scenario(
            scenario,
            output_dir=output_dir,
            repeats=args.repeats,
            warmups=args.warmups,
            top_functions=args.top,
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure SimulationEngine.run() for fixed reference scenarios and "
            "emit benchmark JSON plus cumulative-time cProfile reports."
        )
    )
    parser.add_argument(
        "--scenario",
        choices=("core", "observed", "all"),
        default="all",
        help="Reference scenario to measure (default: all).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Measured wall-clock repeats per scenario (default: 3).",
    )
    parser.add_argument(
        "--warmups",
        type=int,
        default=1,
        help="Unmeasured warmup runs per scenario (default: 1).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Maximum cumulative-time profiler rows (default: 25).",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/performance",
        help="Directory for benchmark/profile artifacts.",
    )
    return parser.parse_args()


def _measure_scenario(
    scenario: ReferencePerformanceScenario,
    *,
    output_dir: Path,
    repeats: int,
    warmups: int,
    top_functions: int,
) -> None:
    benchmark = benchmark_reference_scenario(
        scenario,
        repeats=repeats,
        warmups=warmups,
    )
    stats_path = output_dir / f"{scenario.name}.prof"
    profile = profile_reference_scenario(
        scenario,
        top_functions=top_functions,
        stats_path=str(stats_path),
    )
    benchmark_path = output_dir / f"{scenario.name}-benchmark.json"
    profile_path = output_dir / f"{scenario.name}-profile.txt"
    benchmark_path.write_text(
        json.dumps(
            _benchmark_payload(scenario, benchmark),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    profile_path.write_text(profile.report, encoding="utf-8")

    print(f"\n=== {scenario.name} ===")
    print(f"observed:                {scenario.observed}")
    print(f"completed steps:         {benchmark.outcome.completed_steps}")
    print(f"median seconds:          {benchmark.median_seconds:.6f}")
    print(f"median seconds / step:   {benchmark.median_seconds_per_step:.6f}")
    print(
        f"min / max seconds:       {benchmark.minimum_seconds:.6f} / {benchmark.maximum_seconds:.6f}"
    )
    print(profile.report)
    print(f"benchmark JSON:          {benchmark_path}")
    print(f"profile text:            {profile_path}")
    print(f"raw pstats:              {stats_path}")


def _benchmark_payload(
    scenario: ReferencePerformanceScenario,
    result: ReferenceBenchmarkResult,
) -> dict[str, object]:
    return {
        "scenario": scenario.name,
        "observed": scenario.observed,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "config": attrs.asdict(scenario.config),
        "repeats": result.repeats,
        "warmups": result.warmups,
        "durations_seconds": result.durations_seconds,
        "minimum_seconds": result.minimum_seconds,
        "median_seconds": result.median_seconds,
        "mean_seconds": result.mean_seconds,
        "maximum_seconds": result.maximum_seconds,
        "median_seconds_per_step": result.median_seconds_per_step,
        "outcome": attrs.asdict(result.outcome),
    }


if __name__ == "__main__":
    main()
