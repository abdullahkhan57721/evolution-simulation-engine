"""Focused tests for semantic WorldState transaction copying."""

from __future__ import annotations

from evo_engine.world import Carcass, EnvironmentalField, WorldState
from tests.helpers import make_organism


def test_copy_shares_only_immutable_world_and_organism_state() -> None:
    """Test semantic copies share definitions but isolate mutable state."""
    field = EnvironmentalField(name="temperature", default_value=20)
    world = WorldState(width=3, height=3, environmental_fields=(field,))
    organism = make_organism(energy=10)
    carcass = Carcass(x=1, y=1, resource_units=7)
    world.add_organism(organism)
    world.add_carcass(carcass)
    world.add_resources(x=0, y=0, amount=5)
    world.set_environmental_value("temperature", x=2, y=2, value=23)

    copied = world.copy()

    copied_organism = copied.organisms[organism.id]
    copied_carcass = copied.carcasses[carcass.id]

    assert copied.environmental_fields is world.environmental_fields
    assert copied_organism is not organism
    assert copied_organism.genome is organism.genome
    assert copied_organism.genetic_phenotype is organism.genetic_phenotype
    assert copied_organism.developmental_profile is organism.developmental_profile
    assert copied_carcass is not carcass
    assert copied.mutation_count == 0

    copied_organism.energy = 1
    copied_carcass.resource_units = 2
    copied.add_resources(x=0, y=0, amount=3)
    copied.set_environmental_value("temperature", x=2, y=2, value=25)

    assert organism.energy == 10
    assert carcass.resource_units == 7
    assert world.resources[(0, 0)] == 5
    assert world.environmental_value("temperature", x=2, y=2) == 23


def test_copy_preserves_independent_identity_allocation_counters() -> None:
    """Test copied worlds continue ID allocation without sharing counters."""
    world = WorldState(width=2, height=2)
    first_organism = make_organism()
    first_carcass = Carcass(x=0, y=0, resource_units=1)
    world.add_organism(first_organism)
    world.add_carcass(first_carcass)

    copied = world.copy()
    original_next_organism = make_organism()
    copied_next_organism = make_organism()
    original_next_carcass = Carcass(x=1, y=0, resource_units=1)
    copied_next_carcass = Carcass(x=1, y=0, resource_units=1)

    world.add_organism(original_next_organism)
    copied.add_organism(copied_next_organism)
    world.add_carcass(original_next_carcass)
    copied.add_carcass(copied_next_carcass)

    assert original_next_organism.id == copied_next_organism.id == 1
    assert original_next_carcass.id == copied_next_carcass.id == 1
    assert len(world.organisms) == len(copied.organisms) == 2
    assert len(world.carcasses) == len(copied.carcasses) == 2
