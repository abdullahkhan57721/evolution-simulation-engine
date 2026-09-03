"""Temporary M4 evidence probe; never merge this file."""

from __future__ import annotations

import attrs

from evo_engine.genetics import (
    ASSIMILATION_EFFICIENCY,
    GENETIC_ARCHITECTURE,
    METABOLIC_COST_COEFFICIENT,
    SENSORY_RANGE,
    Chromosome,
    Genome,
)
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology
from evo_engine.presets.reference_ecology.mating_types import (
    reference_founder_mating_type,
)
from evo_engine.world import Organism, WorldState

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
        mutation_probability_ppm=0,
        mutation_max_change=1,
        resource_generation_amount=8,
        resource_deposits_per_step=8,
    )


def _homozygous_variant(founder: Genome, architecture, trait_name: str, value: int) -> Genome:
    variant_allele = architecture.locus(trait_name).create_allele(value)
    chromosomes = []
    for chromosome in founder.chromosomes:
        alleles = tuple(
            variant_allele if allele.locus_name == trait_name else allele
            for allele in chromosome.alleles
        )
        chromosomes.append(Chromosome(name=chromosome.name, alleles=alleles))
    return Genome(chromosomes=tuple(chromosomes))


def _replace_founders(ecology, trait_name: str, low: int, high: int) -> None:
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    old_world = ecology.simulation.state.domain_state
    founder = old_world.organisms[0].genome
    low_genome = _homozygous_variant(founder, architecture, trait_name, low)
    high_genome = _homozygous_variant(founder, architecture, trait_name, high)
    world = WorldState(width=ecology.config.width, height=ecology.config.height)
    for index in range(ecology.config.initial_population):
        genome = low_genome if index % 2 == 0 else high_genome
        world.add_organism(
            Organism.from_genome(
                genetic_architecture=architecture,
                genome=genome,
                age=0,
                energy=ecology.config.initial_energy,
                mating_type=reference_founder_mating_type(index),
                x=index % ecology.config.width,
                y=index // ecology.config.width,
            )
        )
    ecology.simulation.state.domain_state = world


def _run_candidate(
    config: ReferenceEcologyConfig,
    *,
    trait_name: str,
    low: int,
    high: int,
) -> tuple[int, float, float, int]:
    ecology = build_reference_ecology(config)
    _replace_founders(ecology, trait_name, low, high)
    ecology.engine.run(ecology.simulation)
    start = ecology.recorder.observations[0].trait(trait_name).summary.mean
    end = ecology.recorder.observations[-1].trait(trait_name).summary.mean
    assert start is not None and end is not None
    final_genetics = ecology.genetic_recorder.observations[-1].locus(trait_name)
    return (
        len(ecology.simulation.state.domain_state.organisms),
        end - start,
        final_genetics.allele_frequency(high),
        sum(
            event.process_name == "Reproduction"
            for event in ecology.event_recorder.events
        ),
    )


def test_m4_probe() -> None:
    base = _base_config()
    candidates = {
        "sensory_patchy": (
            attrs.evolve(
                base,
                resource_generation_amount=16,
                resource_deposits_per_step=4,
            ),
            SENSORY_RANGE,
            2,
            8,
        ),
        "assimilation_limited": (
            attrs.evolve(
                base,
                resource_generation_amount=8,
                resource_deposits_per_step=8,
            ),
            ASSIMILATION_EFFICIENCY,
            50,
            100,
        ),
        "metabolic_limited": (
            attrs.evolve(
                base,
                resource_generation_amount=8,
                resource_deposits_per_step=8,
            ),
            METABOLIC_COST_COEFFICIENT,
            15,
            45,
        ),
    }
    lines = ["M4_PROBE_V4_FOUNDER_VARIATION"]
    for name, (config, trait_name, low, high) in candidates.items():
        results = [
            _run_candidate(
                attrs.evolve(config, seed=seed),
                trait_name=trait_name,
                low=low,
                high=high,
            )
            for seed in SEEDS
        ]
        populations = [item[0] for item in results]
        deltas = [item[1] for item in results]
        high_frequencies = [item[2] for item in results]
        births = [item[3] for item in results]
        lines.append(
            f"{name} trait={trait_name} {low}/{high} "
            f"pop_mean={sum(populations)/len(populations):.2f} "
            f"births_mean={sum(births)/len(births):.2f}"
        )
        lines.append(
            "  mean_delta="
            + ",".join(f"{value:+.3f}" for value in deltas)
            + f" avg={sum(deltas)/len(deltas):+.3f}"
        )
        lines.append(
            "  high_allele_freq="
            + ",".join(f"{value:.3f}" for value in high_frequencies)
            + f" avg={sum(high_frequencies)/len(high_frequencies):.3f}"
        )
        lines.append("  final_pop=" + ",".join(str(value) for value in populations))

    # Intentional failure exposes the bounded experimental readout in CI.
    raise AssertionError("\n".join(lines))
