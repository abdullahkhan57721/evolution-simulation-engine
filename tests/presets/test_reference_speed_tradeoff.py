"""Focused evidence for the reference max-speed performance tradeoff."""

from __future__ import annotations

import random
from collections import Counter

import attrs

from evo_engine.genetics import MAX_SPEED, SexualInheritance
from evo_engine.presets import (
    ReferenceEcologyConfig,
    build_balanced_reference_trait_world,
    build_reference_genetic_architecture,
)
from evo_engine.presets.reference_ecology.mating_types import REFERENCE_MATING_TYPES
from evo_engine.spatial.targeted_movement import StraightLineTowardTarget

LOW_SPEED = 1
HIGH_SPEED = 4


def _speed_alleles(organism) -> tuple[int, ...]:
    """Return the focal speed allele values carried by one founder."""
    return tuple(allele.value for allele in organism.genome.alleles_at(MAX_SPEED))


def _speed_world():
    """Build the deterministic B2 standing-variation fixture."""
    config = attrs.evolve(
        ReferenceEcologyConfig(),
        initial_population=20,
        mutation_probability_ppm=0,
    )
    architecture = build_reference_genetic_architecture(config)
    world = build_balanced_reference_trait_world(
        architecture,
        trait_name=MAX_SPEED,
        variant_values=(LOW_SPEED, HIGH_SPEED),
        config=config,
    )
    return config, architecture, world


def test_balanced_reference_trait_world_builds_reproducible_speed_variation() -> None:
    """Test founders are homozygous and balanced by speed and mating type."""
    _, _, world = _speed_world()

    counts: Counter[tuple[int, str]] = Counter()
    for organism in world.organisms.values():
        expressed_speed = organism.genetic_phenotype.int_value(MAX_SPEED)
        realized_speed = organism.developmental_profile.int_value(MAX_SPEED)

        assert _speed_alleles(organism) == (expressed_speed, expressed_speed)
        assert realized_speed == expressed_speed
        counts[(expressed_speed, organism.mating_type)] += 1

    assert len(world.organisms) == 20
    for mating_type in REFERENCE_MATING_TYPES:
        assert counts[(LOW_SPEED, mating_type)] == 5
        assert counts[(HIGH_SPEED, mating_type)] == 5


def test_balanced_reference_trait_world_is_deterministic() -> None:
    """Test standing-variation construction consumes no simulation randomness."""
    _, _, first = _speed_world()
    _, _, second = _speed_world()

    first_snapshot = tuple(
        (
            organism.id,
            organism.x,
            organism.y,
            organism.mating_type,
            _speed_alleles(organism),
        )
        for organism in first.organisms.values()
    )
    second_snapshot = tuple(
        (
            organism.id,
            organism.x,
            organism.y,
            organism.mating_type,
            _speed_alleles(organism),
        )
        for organism in second.organisms.values()
    )

    assert first_snapshot == second_snapshot


def test_reference_speed_variants_are_transmitted_by_existing_sexual_inheritance() -> None:
    """Test low and high speed alleles remain ordinary transmissible genetics."""
    _, architecture, world = _speed_world()
    founders = tuple(world.organisms.values())
    low_parent = next(
        organism
        for organism in founders
        if organism.genetic_phenotype.int_value(MAX_SPEED) == LOW_SPEED
    )
    high_parent = next(
        organism
        for organism in founders
        if organism.genetic_phenotype.int_value(MAX_SPEED) == HIGH_SPEED
    )

    offspring_genome = SexualInheritance().inherit(
        (low_parent.genome, high_parent.genome),
        genetic_architecture=architecture,
        rng=random.Random(17),
    )

    assert tuple(
        sorted(allele.value for allele in offspring_genome.alleles_at(MAX_SPEED))
    ) == (LOW_SPEED, HIGH_SPEED)
    assert architecture.express(offspring_genome).int_value(MAX_SPEED) == 3


def test_higher_realized_speed_reaches_farther_toward_same_target() -> None:
    """Test the focal phenotype supplies a direct deterministic movement benefit."""
    _, _, world = _speed_world()
    founders = tuple(world.organisms.values())
    low_speed = next(
        organism.developmental_profile.int_value(MAX_SPEED)
        for organism in founders
        if organism.genetic_phenotype.int_value(MAX_SPEED) == LOW_SPEED
    )
    high_speed = next(
        organism.developmental_profile.int_value(MAX_SPEED)
        for organism in founders
        if organism.genetic_phenotype.int_value(MAX_SPEED) == HIGH_SPEED
    )
    movement = StraightLineTowardTarget()

    low_displacement = movement.choose_displacement(
        current_x=0,
        current_y=0,
        target_x=8,
        target_y=0,
        max_speed=low_speed,
    )
    high_displacement = movement.choose_displacement(
        current_x=0,
        current_y=0,
        target_x=8,
        target_y=0,
        max_speed=high_speed,
    )

    assert low_displacement == (1, 0)
    assert high_displacement == (4, 0)


def test_balanced_reference_trait_world_rejects_unbalanced_population() -> None:
    """Test exact variant-by-mating-type balance is an explicit precondition."""
    config = attrs.evolve(
        ReferenceEcologyConfig(),
        initial_population=6,
    )
    architecture = build_reference_genetic_architecture(config)

    try:
        build_balanced_reference_trait_world(
            architecture,
            trait_name=MAX_SPEED,
            variant_values=(LOW_SPEED, HIGH_SPEED),
            config=config,
        )
    except ValueError as error:
        assert "divisible by twice" in str(error)
    else:
        raise AssertionError("unbalanced founder population should be rejected")
