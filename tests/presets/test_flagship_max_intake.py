"""Tests for the v0.1 flagship max-intake evolutionary demonstration."""

from __future__ import annotations

from collections import Counter

from evo_engine.genetics import MAX_INTAKE_RATE
from evo_engine.presets import (
    FLAGSHIP_HIGH_MAX_INTAKE_RATE,
    FLAGSHIP_LOW_MAX_INTAKE_RATE,
    FLAGSHIP_MAX_INTAKE_SEED,
    build_flagship_max_intake_ecology,
    build_flagship_max_intake_specification,
)


def test_flagship_specification_uses_evidence_backed_canonical_values() -> None:
    """Test the named flagship spec retains the measured M4 regime."""
    specification = build_flagship_max_intake_specification()
    config = specification.reference_config

    assert config.seed == FLAGSHIP_MAX_INTAKE_SEED == 41
    assert config.max_steps == 40
    assert config.width == 12
    assert config.height == 12
    assert config.initial_population == 20
    assert config.initial_energy == 30
    assert config.resource_generation_amount == 6
    assert config.resource_deposits_per_step == 32
    assert config.mating_radius == 1
    assert config.mutation_probability_ppm == 0
    assert config.traits.attack_strength == 0
    assert config.traits.defense == 1
    assert specification.low_max_intake_rate == FLAGSHIP_LOW_MAX_INTAKE_RATE == 2
    assert specification.high_max_intake_rate == FLAGSHIP_HIGH_MAX_INTAKE_RATE == 8


def test_flagship_founders_are_homozygous_and_balanced_across_mating_types() -> None:
    """Test standing intake variation is not confounded with reproductive identity."""
    ecology = build_flagship_max_intake_ecology()
    organisms = tuple(ecology.simulation.state.domain_state.organisms.values())

    allele_pairs = tuple(
        tuple(allele.value for allele in organism.genome.alleles_at(MAX_INTAKE_RATE))
        for organism in organisms
    )
    mating_type_and_intake = Counter(
        (
            organism.mating_type,
            organism.genetic_phenotype.int_value(MAX_INTAKE_RATE),
        )
        for organism in organisms
    )

    assert len(organisms) == 20
    assert Counter(allele_pairs) == {(2, 2): 10, (8, 8): 10}
    assert set(mating_type_and_intake.values()) == {5}
    assert {intake for _, intake in mating_type_and_intake} == {2, 8}
    assert len({mating_type for mating_type, _ in mating_type_and_intake}) == 2


def test_flagship_fixed_seed_construction_is_deterministic() -> None:
    """Test the canonical founder world contains no hidden initialization draws."""
    first = build_flagship_max_intake_ecology()
    second = build_flagship_max_intake_ecology()

    first_world = first.simulation.state.domain_state
    second_world = second.simulation.state.domain_state

    assert first_world == second_world
    assert first.simulation.context == second.simulation.context
