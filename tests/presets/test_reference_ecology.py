"""Tests for the complete reference ecology preset."""

from __future__ import annotations

import pytest

from evo_engine.engine import MaxSteps, SequentialStepCoordinator
from evo_engine.genetics import (
    ADULT_BODY_MASS,
    ASSIMILATION_EFFICIENCY,
    ATTACK_STRENGTH,
    CHOOSINESS,
    DEFENSE,
    ENERGY_CONSERVATION_THRESHOLD,
    ENERGY_RESERVE,
    GROWTH_RATE,
    LOCOMOTION_COST_COEFFICIENT,
    MATE_SEARCH_RANGE,
    MATING_SIGNAL,
    MATURITY_AGE,
    MAX_INTAKE_RATE,
    MAX_SPEED,
    MAXIMUM_AGE,
    METABOLIC_COST_COEFFICIENT,
    OFFSPRING_ENERGY,
    REPRODUCTION_ENERGY_THRESHOLD,
    SENSORY_ACCURACY,
    SENSORY_RANGE,
)
from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceTraitValues,
    build_reference_ecology,
    build_reference_genetic_architecture,
    build_reference_world,
)

EXPECTED_REFERENCE_TRAITS = frozenset(
    {
        ADULT_BODY_MASS,
        GROWTH_RATE,
        MAX_SPEED,
        LOCOMOTION_COST_COEFFICIENT,
        SENSORY_RANGE,
        SENSORY_ACCURACY,
        MAX_INTAKE_RATE,
        ASSIMILATION_EFFICIENCY,
        METABOLIC_COST_COEFFICIENT,
        ENERGY_CONSERVATION_THRESHOLD,
        ENERGY_RESERVE,
        ATTACK_STRENGTH,
        DEFENSE,
        MATE_SEARCH_RANGE,
        CHOOSINESS,
        MATING_SIGNAL,
        MATURITY_AGE,
        REPRODUCTION_ENERGY_THRESHOLD,
        OFFSPRING_ENERGY,
        MAXIMUM_AGE,
    }
)


def test_reference_config_rejects_more_founders_than_world_cells() -> None:
    """Test deterministic distinct-cell founder placement remains possible."""
    with pytest.raises(ValueError, match="initial_population"):
        ReferenceEcologyConfig(
            width=2,
            height=2,
            initial_population=5,
        )


def test_reference_config_rejects_newborn_fraction_above_one() -> None:
    """Test newborn mass cannot exceed its adult target by configuration."""
    with pytest.raises(ValueError, match="newborn_mass_numerator"):
        ReferenceEcologyConfig(
            newborn_mass_numerator=2,
            newborn_mass_denominator=1,
        )


def test_reference_architecture_contains_exactly_required_traits() -> None:
    """Test the reference genome models the intended evolvable strategy knobs."""
    architecture = build_reference_genetic_architecture()

    assert frozenset(architecture.trait_names) == EXPECTED_REFERENCE_TRAITS
    assert {locus.chromosome_name for locus in architecture.loci} == {"reference"}


def test_reference_world_uses_homozygous_founders_in_distinct_cells() -> None:
    """Test founder initialization is transparent and deterministic."""
    config = ReferenceEcologyConfig(
        width=4,
        height=3,
        initial_population=6,
        initial_energy=25,
    )
    architecture = build_reference_genetic_architecture(config)
    world = build_reference_world(
        architecture,
        config,
    )

    organisms = tuple(world.organisms.values())

    assert len(organisms) == 6
    assert [(organism.x, organism.y) for organism in organisms] == [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 0),
        (0, 1),
        (1, 1),
    ]
    assert all(organism.energy == 25 for organism in organisms)
    assert all(len(organism.genome.chromosomes) == 2 for organism in organisms)
    assert all(
        organism.genetic_phenotype.int_value(ADULT_BODY_MASS)
        == config.traits.adult_body_mass
        for organism in organisms
    )
    assert all(
        organism.genetic_phenotype.int_value(GROWTH_RATE) == config.traits.growth_rate
        for organism in organisms
    )
    assert all(
        organism.genetic_phenotype.int_value(METABOLIC_COST_COEFFICIENT)
        == config.traits.metabolic_cost_coefficient
        for organism in organisms
    )
    assert all(
        organism.genetic_phenotype.int_value(LOCOMOTION_COST_COEFFICIENT)
        == config.traits.locomotion_cost_coefficient
        for organism in organisms
    )


def test_reference_engine_uses_documented_standard_lifecycle_order() -> None:
    """Test the preset wires every major process into the lifecycle."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            max_steps=1,
        )
    )

    assert isinstance(ecology.engine.step_coordinator, SequentialStepCoordinator)

    process_names_by_stage = [
        tuple(type(process).__name__ for process in stage.processes)
        for stage in ecology.engine.step_coordinator.stages
    ]

    assert process_names_by_stage == [
        ("Starvation",),
        ("MaximumAgeMortality",),
        ("Metabolism",),
        ("Starvation",),
        ("ResourceGeneration", "Decomposition"),
        ("Movement",),
        ("Predation",),
        ("ResourceConsumption",),
        ("Growth",),
        ("Aging",),
        ("MaximumAgeMortality",),
        ("Reproduction",),
        ("Starvation",),
    ]


def test_reference_bundle_uses_one_resolved_configuration() -> None:
    """Test simulation and engine are built from the same supplied baseline."""
    config = ReferenceEcologyConfig(
        width=5,
        height=5,
        initial_population=4,
        max_steps=3,
        seed=17,
    )

    ecology = build_reference_ecology(config)

    assert ecology.config is config
    assert ecology.simulation.state.world.width == 5
    assert ecology.simulation.state.world.height == 5
    assert len(ecology.simulation.state.world.organisms) == 4
    assert isinstance(ecology.engine.stopping_condition, MaxSteps)
    assert ecology.engine.stopping_condition.max_steps == 3
    assert ecology.recorder in ecology.engine.observers
    assert ecology.event_recorder in ecology.engine.telemetry_observers


def test_reference_founder_values_are_customizable() -> None:
    """Test callers can replace reference trait baselines without rewiring."""
    traits = ReferenceTraitValues(
        adult_body_mass=12,
        growth_rate=2,
        max_speed=2,
        locomotion_cost_coefficient=35,
        sensory_range=7,
        sensory_accuracy=80,
        max_intake_rate=8,
        assimilation_efficiency=60,
        metabolic_cost_coefficient=45,
        energy_conservation_threshold=18,
        energy_reserve=6,
        attack_strength=11,
        defense=9,
        mate_search_range=6,
        choosiness=7,
        mating_signal=12,
        maturity_age=3,
        reproduction_energy_threshold=22,
        offspring_energy=5,
        maximum_age=40,
    )
    config = ReferenceEcologyConfig(
        initial_population=1,
        traits=traits,
    )
    ecology = build_reference_ecology(config)
    organism = next(iter(ecology.simulation.state.world.organisms.values()))

    assert organism.genetic_phenotype.int_value(ADULT_BODY_MASS) == 12
    assert organism.genetic_phenotype.int_value(GROWTH_RATE) == 2
    assert organism.genetic_phenotype.int_value(LOCOMOTION_COST_COEFFICIENT) == 35
    assert organism.genetic_phenotype.int_value(SENSORY_ACCURACY) == 80
    assert organism.genetic_phenotype.int_value(MAX_INTAKE_RATE) == 8
    assert organism.genetic_phenotype.int_value(ASSIMILATION_EFFICIENCY) == 60
    assert organism.genetic_phenotype.int_value(METABOLIC_COST_COEFFICIENT) == 45
    assert organism.genetic_phenotype.int_value(ATTACK_STRENGTH) == 11
    assert organism.genetic_phenotype.int_value(DEFENSE) == 9
    assert organism.genetic_phenotype.int_value(MATE_SEARCH_RANGE) == 6
    assert organism.genetic_phenotype.int_value(CHOOSINESS) == 7
    assert organism.genetic_phenotype.int_value(MATING_SIGNAL) == 12
    assert organism.developmental_profile.int_value(MAXIMUM_AGE) == 40
