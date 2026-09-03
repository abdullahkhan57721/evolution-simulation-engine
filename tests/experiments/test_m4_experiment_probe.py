"""Temporary M4 evidence probe; never merge this file."""

from __future__ import annotations

import attrs

from evo_engine.genetics import GENETIC_ARCHITECTURE, SENSORY_RANGE, Chromosome, Genome
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology
from evo_engine.presets.reference_ecology.mating_types import reference_founder_mating_type
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
    )


def _homozygous_variant(founder: Genome, architecture, value: int) -> Genome:
    variant_allele = architecture.locus(SENSORY_RANGE).create_allele(value)
    chromosomes = []
    for chromosome in founder.chromosomes:
        alleles = tuple(
            variant_allele if allele.locus_name == SENSORY_RANGE else allele
            for allele in chromosome.alleles
        )
        chromosomes.append(Chromosome(name=chromosome.name, alleles=alleles))
    return Genome(chromosomes=tuple(chromosomes))


def _replace_founders(ecology) -> None:
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    old_world = ecology.simulation.state.domain_state
    founder = old_world.organisms[0].genome
    low_genome = _homozygous_variant(founder, architecture, 2)
    high_genome = _homozygous_variant(founder, architecture, 8)
    world = WorldState(width=ecology.config.width, height=ecology.config.height)
    for index in range(ecology.config.initial_population):
        genome = high_genome if index % 4 in (1, 2) else low_genome
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


def _run(config: ReferenceEcologyConfig) -> tuple[int, int, float, float, str]:
    ecology = build_reference_ecology(config)
    _replace_founders(ecology)
    ecology.engine.run(ecology.simulation)
    start = ecology.recorder.observations[0].trait(SENSORY_RANGE).summary.mean
    end = ecology.recorder.observations[-1].trait(SENSORY_RANGE).summary.mean
    assert start is not None and end is not None
    high_frequency = ecology.genetic_recorder.observations[-1].locus(SENSORY_RANGE).allele_frequency(8)
    births = sum(event.process_name == "Reproduction" for event in ecology.event_recorder.events)

    population_by_step = {obs.step_index: obs for obs in ecology.recorder.observations}
    genetics_by_step = {obs.step_index: obs for obs in ecology.genetic_recorder.observations}
    checkpoints = []
    for step in (1, 10, 20, 30, 40):
        pop = population_by_step[step]
        genetics = genetics_by_step[step]
        mean = pop.trait(SENSORY_RANGE).summary.mean
        freq = genetics.locus(SENSORY_RANGE).allele_frequency(8)
        checkpoints.append(f"{step}:pop{pop.population_size}:mean{mean:.3f}:high{freq:.3f}")
    return len(ecology.simulation.state.domain_state.organisms), births, end - start, high_frequency, ";".join(checkpoints)


def test_m4_probe() -> None:
    base = _base_config()
    candidates = {
        "limited_patchy_64": attrs.evolve(
            base,
            resource_generation_amount=16,
            resource_deposits_per_step=4,
        ),
        "diffuse_equal_64": attrs.evolve(
            base,
            resource_generation_amount=4,
            resource_deposits_per_step=16,
        ),
        "abundant_patchy_160": attrs.evolve(
            base,
            resource_generation_amount=40,
            resource_deposits_per_step=4,
        ),
    }
    lines = ["M4_PROBE_V5_SENSORY_CONTROLS"]
    for name, config in candidates.items():
        results = [_run(attrs.evolve(config, seed=seed)) for seed in SEEDS]
        populations = [item[0] for item in results]
        births = [item[1] for item in results]
        deltas = [item[2] for item in results]
        high_frequencies = [item[3] for item in results]
        lines.append(
            f"{name} pop_mean={sum(populations)/len(populations):.2f} "
            f"births_mean={sum(births)/len(births):.2f} "
            f"trait_delta_avg={sum(deltas)/len(deltas):+.3f} "
            f"high_freq_avg={sum(high_frequencies)/len(high_frequencies):.3f}"
        )
        lines.append("  final_pop=" + ",".join(str(value) for value in populations))
        lines.append("  trait_delta=" + ",".join(f"{value:+.3f}" for value in deltas))
        lines.append("  high_freq=" + ",".join(f"{value:.3f}" for value in high_frequencies))
        lines.append("  seed42=" + results[2][4] + f";births={results[2][1]}")

    raise AssertionError("\n".join(lines))
