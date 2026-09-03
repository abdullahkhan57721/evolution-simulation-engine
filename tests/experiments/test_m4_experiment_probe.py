"""Temporary M4 evidence probe; never merge this file."""

from __future__ import annotations

from collections import defaultdict

import attrs

from evo_engine.experiments import run_reference_replicates
from evo_engine.presets import ReferenceEcologyConfig


SEEDS = (7, 19, 42, 73, 101, 211)


def _trait_mean(observation, trait_name: str) -> float | None:
    for trait in observation.traits:
        if trait.trait_name == trait_name:
            return trait.summary.mean
    raise KeyError(trait_name)


def _candidate_configs() -> dict[str, ReferenceEcologyConfig]:
    baseline = ReferenceEcologyConfig()
    common = dict(
        initial_population=30,
        max_steps=120,
        mutation_probability_ppm=100_000,
        mutation_max_change=1,
    )
    return {
        "baseline": attrs.evolve(baseline, **common),
        "scarce": attrs.evolve(
            baseline,
            **common,
            resource_generation_amount=3,
            resource_deposits_per_step=3,
        ),
        "patchy": attrs.evolve(
            baseline,
            **common,
            resource_generation_amount=12,
            resource_deposits_per_step=2,
        ),
        "abundant": attrs.evolve(
            baseline,
            **common,
            resource_generation_amount=10,
            resource_deposits_per_step=12,
        ),
        "predation": attrs.evolve(
            baseline,
            **common,
            predation_radius=1,
        ),
    }


def test_m4_probe() -> None:
    lines: list[str] = ["M4_PROBE_V1"]
    for name, config in _candidate_configs().items():
        result = run_reference_replicates(config, seeds=SEEDS)
        deltas: dict[str, list[float]] = defaultdict(list)
        final_pops: list[int] = []
        births: list[int] = []
        extinctions = 0

        for replicate in result.replicates:
            start = replicate.population_history[0]
            end = replicate.population_history[-1]
            final_pops.append(replicate.final_population_size)
            births.append(replicate.total_births)
            if replicate.final_population_size == 0:
                extinctions += 1
            for start_trait in start.traits:
                trait_name = start_trait.trait_name
                start_mean = _trait_mean(start, trait_name)
                end_mean = _trait_mean(end, trait_name)
                if start_mean is not None and end_mean is not None:
                    deltas[trait_name].append(end_mean - start_mean)

        ranked = sorted(
            deltas.items(),
            key=lambda item: abs(sum(item[1]) / len(item[1])) if item[1] else 0.0,
            reverse=True,
        )[:8]
        lines.append(
            f"ENV {name} ext={extinctions}/{len(SEEDS)} "
            f"final_pop_mean={sum(final_pops)/len(final_pops):.2f} "
            f"births_mean={sum(births)/len(births):.2f}"
        )
        for trait_name, values in ranked:
            mean_delta = sum(values) / len(values)
            positive = sum(value > 0 for value in values)
            negative = sum(value < 0 for value in values)
            lines.append(
                f"  {trait_name}: delta={mean_delta:+.3f} "
                f"sign=+{positive}/-{negative} values="
                + ",".join(f"{value:+.2f}" for value in values)
            )

    raise AssertionError("\n".join(lines))
