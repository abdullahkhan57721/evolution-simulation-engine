"""Tests for the controlled locomotion genetic and founder composition."""

from __future__ import annotations

import random

from evo_engine.genetics import MAX_SPEED, ClonalInheritance
from evo_engine.presets.controlled_locomotion import (
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_founder_genome,
    build_controlled_locomotion_genetic_architecture,
    build_controlled_locomotion_world,
)


def test_controlled_architecture_contains_only_inherited_max_speed() -> None:
    """Test E2 genetics has one focal trait and no nonfocal inherited state."""
    architecture = build_controlled_locomotion_genetic_architecture()
    genome = build_controlled_locomotion_founder_genome(
        architecture,
        max_speed=7,
    )

    phenotype = architecture.express(genome)

    assert architecture.trait_names == frozenset({MAX_SPEED})
    assert phenotype.int_value(MAX_SPEED) == 7


def test_no_mutation_clonal_inheritance_preserves_focal_capacity_exactly() -> None:
    """Test one-parent propagation creates no focal mutation or recombination."""
    architecture = build_controlled_locomotion_genetic_architecture()
    parent = build_controlled_locomotion_founder_genome(
        architecture,
        max_speed=9,
    )

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(1234),
    )

    assert offspring == parent
    assert architecture.express(offspring).int_value(MAX_SPEED) == 9


def test_founder_world_is_deterministic_and_nonfocal_biology_is_fixed() -> None:
    """Test caller order fixes IDs while body mass and energy stay nonheritable."""
    config = ControlledLocomotionConfig(
        width=20,
        height=20,
        founders=(
            ControlledLocomotionFounder(max_speed=2, x=4, y=5),
            ControlledLocomotionFounder(max_speed=8, x=11, y=12),
        ),
        resource_deposits=(
            ControlledResourceDeposit(x=15, y=10, amount=40),
        ),
        initial_energy=77,
        body_mass=3,
    )
    architecture = build_controlled_locomotion_genetic_architecture()

    world = build_controlled_locomotion_world(architecture, config)

    assert tuple(world.organisms) == (0, 1)
    first = world.organisms[0]
    second = world.organisms[1]
    assert (first.x, first.y, first.energy, first.body_mass) == (4, 5, 77, 3)
    assert (second.x, second.y, second.energy, second.body_mass) == (11, 12, 77, 3)
    assert first.genetic_phenotype.int_value(MAX_SPEED) == 2
    assert second.genetic_phenotype.int_value(MAX_SPEED) == 8
    assert world.resources == {(15, 10): 40}
