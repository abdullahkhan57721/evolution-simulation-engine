"""Temporary M4 evidence probe; never merge this file."""

from __future__ import annotations

from collections import defaultdict

import attrs

from evo_engine.experiments import run_reference_replicates
from evo_engine.presets import ReferenceEcologyConfig

SEEDS = (7, 19, 42, 73, 101, 211)


def _base_config() -> ReferenceEcologyConfig:
    baseline = ReferenceEcologyConfig()
    traits = attrs.evolve(
        baseline.traits,
        reproduction_energy_threshold=12,
        offspring_energy=6,
        maturity_age=2,
        maximum_age=45,
    )
    return attrs.evolve(
        baseline,
        traits=traits,
        initial_population=30,
        initial_energy=60,
        max_steps=40,
        mutation_probability_ppm=50_000,
        mutation_max_change=1,
    )


def _candidate_configs() -> dict[str, ReferenceEcologyConfig]:
    base = _base_config()
    return {
        "balanced": attrs.evolve(
            base,
            resource_generation_amount=10,
            resource_deposits_per_step=10,
        ),
        "scarce": attrs.evolve(
            base,
            resource_generation_amount=4,
            resource_deposits_per_step=4,
        ),
        "patchy": attrs.evolve(
            base,
            resource_generation_amount=16,
            resource_deposits_per_step=2,
        ),
        "abundant": attrs.evolve(
            base,
            resource_generation_amount=12,
            resource_deposits_per_step=14,
        ),
        "predation": attrs.evolve(
            base,
            resource_generation_amount=10,
            resource_deposits_per_step=10,
            predation_radius=1,
        ),
    }


def _mean_trait(observation, name: str) -> float | None:
    return observation.trait(name).summary.mean


def test_m4_probe() -> None:
    lines: list[str] = ["M4_PROBE_V3_TRAIT_SHIFTS"]
    for name, config in _candidate_configs().items():
        result = run_reference_replicates(config, seeds=SEEDS)
        trait_deltas: dict[str, list[float]] = defaultdict(list)
        populations: list[int] = []
        births: list[int] = []
        trajectories: list[str] = []

        for replicate in result.replicates:
            start = replicate.population_history[0]
            end = replicate.population_history[-1]
            populations.append(replicate.final_population_size)
            births.append(replicate.total_births)
            trajectories.append(
                "/".join(
                    str(observation.population_size)
                    for observation in replicate.population_history
                    if observation.step_index in (0, 10, 20, 30, 40)
                )
            )
            for start_trait in start.traits:
                trait_name = start_trait.trait_name
                start_mean = _mean_trait(start, trait_name)
                end_mean = _mean_trait(end, trait_name)
                if start_mean is not None and end_mean is not None:
                    trait_deltas[trait_name].append(end_mean - start_mean)

        lines.append(
            f"ENV {name} final_pop_mean={sum(populations)/len(populations):.2f} "
            f"range={min(populations)}-{max(populations)} "
            f"births_mean={sum(births)/len(births):.2f}"
        )
        lines.append("  trajectories=" + ",".join(trajectories))
        ranked = sorted(
            trait_deltas.items(),
            key=lambda item: abs(sum(item[1]) / len(item[1])),
            reverse=True,
        )[:12]
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
