"""Temporary M4 evidence probe; never merge this file."""

from __future__ import annotations

import attrs

from evo_engine.experiments import run_reference_replicates
from evo_engine.presets import ReferenceEcologyConfig

SEEDS = (7, 19, 42, 73, 101, 211)


def _with_life_history(
    baseline: ReferenceEcologyConfig,
    *,
    reproduction_energy_threshold: int,
    offspring_energy: int,
    maturity_age: int,
    maximum_age: int,
) -> ReferenceEcologyConfig:
    return attrs.evolve(
        baseline,
        traits=attrs.evolve(
            baseline.traits,
            reproduction_energy_threshold=reproduction_energy_threshold,
            offspring_energy=offspring_energy,
            maturity_age=maturity_age,
            maximum_age=maximum_age,
        ),
    )


def _candidate_configs() -> dict[str, ReferenceEcologyConfig]:
    baseline = ReferenceEcologyConfig()
    gentle = _with_life_history(
        baseline,
        reproduction_energy_threshold=15,
        offspring_energy=6,
        maturity_age=3,
        maximum_age=40,
    )
    fertile = _with_life_history(
        baseline,
        reproduction_energy_threshold=12,
        offspring_energy=6,
        maturity_age=2,
        maximum_age=45,
    )
    common = dict(
        initial_population=30,
        max_steps=80,
        mutation_probability_ppm=50_000,
        mutation_max_change=1,
        resource_generation_amount=10,
        resource_deposits_per_step=10,
    )
    return {
        "gentle_e40": attrs.evolve(gentle, **common, initial_energy=40),
        "gentle_e60": attrs.evolve(gentle, **common, initial_energy=60),
        "fertile_e40": attrs.evolve(fertile, **common, initial_energy=40),
        "fertile_e60": attrs.evolve(fertile, **common, initial_energy=60),
    }


def test_m4_probe() -> None:
    lines: list[str] = ["M4_PROBE_V2_VIABILITY"]
    for name, config in _candidate_configs().items():
        result = run_reference_replicates(config, seeds=SEEDS)
        final_pops: list[int] = []
        births: list[int] = []
        deaths: list[int] = []
        extinctions = 0
        trajectories: list[str] = []

        for replicate in result.replicates:
            final_pops.append(replicate.final_population_size)
            births.append(replicate.total_births)
            deaths.append(replicate.total_deaths)
            if replicate.final_population_size == 0:
                extinctions += 1
            checkpoints = tuple(
                observation.population_size
                for observation in replicate.population_history
                if observation.step_index in (0, 20, 40, 60, 80)
            )
            trajectories.append("/".join(str(value) for value in checkpoints))

        lines.append(
            f"ENV {name} ext={extinctions}/{len(SEEDS)} "
            f"final_pop_mean={sum(final_pops) / len(final_pops):.2f} "
            f"births_mean={sum(births) / len(births):.2f} "
            f"deaths_mean={sum(deaths) / len(deaths):.2f}"
        )
        lines.append("  trajectories=" + ",".join(trajectories))

    raise AssertionError("\n".join(lines))
