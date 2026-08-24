"""Integration tests for the complete reference ecology preset."""

from __future__ import annotations

from evo_engine.genetics import MAXIMUM_AGE
from evo_engine.presets import (
    ReferenceEcology,
    ReferenceEcologyConfig,
    ReferenceTraitValues,
    build_reference_ecology,
)


def _world_snapshot(ecology: ReferenceEcology) -> tuple[object, ...]:
    world = ecology.simulation.state.world
    organisms = tuple(
        (
            organism_id,
            organism.age,
            organism.energy,
            organism.body_mass,
            organism.x,
            organism.y,
            organism.genetic_phenotype.trait_values,
        )
        for organism_id, organism in world.organisms.items()
    )
    carcasses = tuple(
        (
            carcass_id,
            carcass.x,
            carcass.y,
            carcass.resource_units,
        )
        for carcass_id, carcass in world.carcasses.items()
    )

    return (
        ecology.simulation.state.step_index,
        organisms,
        carcasses,
        tuple(sorted(world.resources.items())),
    )


def test_reference_ecology_runs_multiple_complete_timesteps() -> None:
    """Test all reference stages compose without cross-process failures."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            max_steps=8,
            seed=11,
        )
    )

    ecology.engine.run(ecology.simulation)

    assert ecology.simulation.state.step_index == 8
    assert ecology.simulation.genetic_architecture.trait(MAXIMUM_AGE)


def test_reference_ecology_is_reproducible_for_same_seed_and_configuration() -> None:
    """Test the complete stochastic ecology is deterministic under a fixed seed."""
    config = ReferenceEcologyConfig(
        max_steps=10,
        seed=23,
    )
    first = build_reference_ecology(config)
    second = build_reference_ecology(config)

    first.engine.run(first.simulation)
    second.engine.run(second.simulation)

    assert _world_snapshot(first) == _world_snapshot(second)


def test_reference_ecology_performs_sexual_reproduction_at_boundary() -> None:
    """Test the integrated reference can create age-zero sexually inherited young."""
    config = ReferenceEcologyConfig(
        width=2,
        height=1,
        initial_population=2,
        initial_energy=20,
        max_steps=1,
        seed=7,
        mutation_probability_ppm=0,
        traits=ReferenceTraitValues(
            adult_body_mass=8,
            max_speed=0,
            sensory_range=0,
            energy_conservation_threshold=0,
            energy_reserve=0,
            maturity_age=0,
            reproduction_energy_threshold=0,
            offspring_energy=2,
            maximum_age=10,
        ),
        resource_generation_amount=1,
        resource_deposits_per_step=1,
        metabolic_coefficient=0,
        locomotion_coefficient=0,
        growth_amount_per_step=0,
        predation_radius=0,
        mating_radius=1,
    )
    ecology = build_reference_ecology(config)

    ecology.engine.run(ecology.simulation)

    organisms = tuple(ecology.simulation.state.world.organisms.values())
    newborns = tuple(organism for organism in organisms if organism.age == 0)
    parents = tuple(organism for organism in organisms if organism.age == 1)

    assert len(organisms) == 3
    assert len(parents) == 2
    assert len(newborns) == 1
    assert newborns[0].energy == 4
    assert newborns[0].body_mass == 2


def test_reference_ecology_mutation_creates_bounded_offspring_variation() -> None:
    """Test integrated sexual inheritance uses the configured mutation machinery."""
    config = ReferenceEcologyConfig(
        width=2,
        height=1,
        initial_population=2,
        initial_energy=30,
        max_steps=1,
        seed=13,
        mutation_probability_ppm=1_000_000,
        mutation_max_change=1,
        traits=ReferenceTraitValues(
            adult_body_mass=8,
            max_speed=0,
            sensory_range=2,
            energy_conservation_threshold=10,
            energy_reserve=0,
            maturity_age=0,
            reproduction_energy_threshold=0,
            offspring_energy=2,
            maximum_age=10,
        ),
        resource_generation_amount=1,
        resource_deposits_per_step=1,
        metabolic_coefficient=0,
        locomotion_coefficient=0,
        growth_amount_per_step=0,
        mating_radius=1,
    )
    ecology = build_reference_ecology(config)
    founder_values = config.traits.as_mapping()

    ecology.engine.run(ecology.simulation)

    newborn = next(
        organism
        for organism in ecology.simulation.state.world.organisms.values()
        if organism.age == 0
    )
    mutated_alleles = tuple(
        allele
        for chromosome in newborn.genome.chromosomes
        for allele in chromosome.alleles
        if allele.value != founder_values[allele.locus_name]
    )

    assert mutated_alleles

    for trait_name, value in newborn.genetic_phenotype.trait_values:
        ecology.simulation.genetic_architecture.locus(trait_name).domain.validate(value)
