#!/usr/bin/env python3
"""Benchmark and profile domain-neutral simulation-kernel scenarios."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import attrs

from evo_engine.experiments.kernel_performance import (
    KERNEL_CORE_BASELINE,
    KERNEL_JOURNALED_BASELINE,
    KernelBenchmarkResult,
    KernelPerformanceScenario,
    benchmark_kernel_scenario,
    profile_kernel_scenario,
)

_SCENARIOS = {
    "core": KERNEL_CORE_BASELINE,
    "journaled": KERNEL_JOURNALED_BASELINE,
}


def main() -> None:
    """Run requested kernel benchmarks and write profiler artifacts."""
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
        description="Measure domain-neutral simulation-kernel orchestration overhead."
    )
    parser.add_argument(
        "--scenario",
        choices=("core", "journaled", "all"),
        default="all",
        help="Kernel scenario to measure (default: all).",
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
    scenario: KernelPerformanceScenario,
    *,
    output_dir: Path,
    repeats: int,
    warmups: int,
    top_functions: int,
) -> None:
    benchmark = benchmark_kernel_scenario(
        scenario,
        repeats=repeats,
        warmups=warmups,
    )
    stats_path = output_dir / f"{scenario.name}.prof"
    profile = profile_kernel_scenario(
        scenario,
        top_functions=top_functions,
        stats_path=str(stats_path),
    )
    benchmark_path = output_dir / f"{scenario.name}-benchmark.json"
    profile_path = output_dir / f"{scenario.name}-profile.txt"
    benchmark_path.write_text(
        json.dumps(_benchmark_payload(scenario, benchmark), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    profile_path.write_text(profile.report, encoding="utf-8")

    print(f"\n=== {scenario.name} ===")
    print(f"journaled:               {scenario.journaled}")
    print(f"completed steps:         {benchmark.outcome.completed_steps}")
    print(f"applied events:          {benchmark.outcome.applied_events}")
    print(f"median seconds:          {benchmark.median_seconds:.6f}")
    print(f"median seconds / event:  {benchmark.median_seconds_per_event:.9f}")
    print(
        f"min / max seconds:       {benchmark.minimum_seconds:.6f} / "
        f"{benchmark.maximum_seconds:.6f}"
    )
    print(profile.report)
    print(f"benchmark JSON:          {benchmark_path}")
    print(f"profile text:            {profile_path}")
    print(f"raw pstats:              {stats_path}")


def _benchmark_payload(
    scenario: KernelPerformanceScenario,
    result: KernelBenchmarkResult,
) -> dict[str, object]:
    return {
        "scenario": scenario.name,
        "journaled": scenario.journaled,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "config": attrs.asdict(scenario),
        "repeats": result.repeats,
        "warmups": result.warmups,
        "durations_seconds": result.durations_seconds,
        "minimum_seconds": result.minimum_seconds,
        "median_seconds": result.median_seconds,
        "mean_seconds": result.mean_seconds,
        "maximum_seconds": result.maximum_seconds,
        "median_seconds_per_event": result.median_seconds_per_event,
        "outcome": attrs.asdict(result.outcome),
    }


if __name__ == "__main__":
    main()
