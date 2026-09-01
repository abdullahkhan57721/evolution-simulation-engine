"""Tests for WorldState."""

from __future__ import annotations

import math

import pytest

from evo_engine.world import (
    Carcass,
    EnvironmentalField,
    EnvironmentalValueChanged,
    WorldState,
)
from tests.helpers import make_organism


def test_add_organism_assigns_monotonic_ids() -> None:
    """Test that world-managed organism IDs are never recycled."""
    world = WorldState(width=5, height=5)
    first = make_organism()
    second = make_organism()

    world.add_organism(first)
    world.remove_organism(first.id)
    world.add_organism(second)

    assert first.id == 0
    assert second.id == 1


def test_add_organism_rejects_out_of_bounds_coordinate() -> None:
    """Test that organisms cannot be inserted outside world bounds."""
    world = WorldState(width=2, height=2)
    organism = make_organism(x=2, y=0)

    with pytest.raises(ValueError):
        world.add_organism(organism)


def test_public_organism_mapping_is_read_only() -> None:
    """Test that callers cannot structurally mutate the organism mapping."""
    world = WorldState(width=2, height=2)
    organism = make_organism()
    world.add_organism(organism)

    with pytest.raises(TypeError):
        world.organisms[99] = organism  # type: ignore[index]


def test_remove_organism_returns_removed_entity() -> None:
    """Test that removal returns the world entity that was removed."""
    world = WorldState(width=2, height=2)
    organism = make_organism()
    world.add_organism(organism)

    removed = world.remove_organism(organism.id)

    assert removed is organism
    assert not world.organisms


def test_move_organism_updates_position() -> None:
    """Test controlled world movement."""
    world = WorldState(width=5, height=5)
    organism = make_organism(x=1, y=1)
    world.add_organism(organism)

    world.move_organism(
        organism_id=organism.id,
        x=3,
        y=4,
    )

    assert (organism.x, organism.y) == (3, 4)


def test_move_organism_validates_destination_before_mutation() -> None:
    """Test that invalid movement leaves organism position unchanged."""
    world = WorldState(width=2, height=2)
    organism = make_organism(x=1, y=1)
    world.add_organism(organism)

    with pytest.raises(ValueError):
        world.move_organism(
            organism_id=organism.id,
            x=2,
            y=1,
        )

    assert (organism.x, organism.y) == (1, 1)


def test_carcass_ids_are_world_managed_and_monotonic() -> None:
    """Test that carcass IDs are unique and never recycled."""
    world = WorldState(width=2, height=2)
    first = Carcass(x=0, y=0, resource_units=5)
    second = Carcass(x=1, y=1, resource_units=5)

    world.add_carcass(first)
    world.remove_carcass(first.id)
    world.add_carcass(second)

    assert first.id == 0
    assert second.id == 1


def test_add_resources_accumulates_at_coordinate() -> None:
    """Test sparse resource accumulation."""
    world = WorldState(width=2, height=2)

    world.add_resources(x=1, y=1, amount=3)
    world.add_resources(x=1, y=1, amount=4)

    assert world.resources[(1, 1)] == 7


@pytest.mark.parametrize("amount", [0, -1])
def test_resource_mutation_requires_positive_amount(amount: int) -> None:
    """Test that zero and negative resource transfers are rejected."""
    world = WorldState(width=2, height=2)

    with pytest.raises(ValueError):
        world.add_resources(x=0, y=0, amount=amount)


def test_remove_resources_deletes_empty_sparse_entry() -> None:
    """Test that zero-resource cells are omitted from sparse storage."""
    world = WorldState(width=2, height=2)
    world.add_resources(x=0, y=0, amount=5)

    world.remove_resources(x=0, y=0, amount=5)

    assert (0, 0) not in world.resources


def test_remove_resources_rejects_overdraw() -> None:
    """Test that resource removal cannot exceed local availability."""
    world = WorldState(width=2, height=2)
    world.add_resources(x=0, y=0, amount=2)

    with pytest.raises(ValueError):
        world.remove_resources(x=0, y=0, amount=3)

    assert world.resources[(0, 0)] == 2


def test_environmental_field_uses_default_and_sparse_overrides() -> None:
    """Test spatial environmental values fall back to an immutable default."""
    world = WorldState(
        width=3,
        height=3,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20.0),
        ),
    )

    assert world.environmental_field_names == ("temperature",)
    assert world.environmental_value("temperature", x=1, y=2) == 20.0
    assert not world.environmental_overrides("temperature")

    world.set_environmental_value("temperature", x=1, y=2, value=24.5)

    assert world.environmental_value("temperature", x=1, y=2) == 24.5
    assert world.environmental_value("temperature", x=0, y=0) == 20.0
    assert world.environmental_overrides("temperature") == {(1, 2): 24.5}

    world.set_environmental_value("temperature", x=1, y=2, value=20.0)

    assert not world.environmental_overrides("temperature")


def test_environmental_mutation_is_journaled_only_for_effective_change() -> None:
    """Test environmental telemetry stores field, coordinate, before, and after."""
    world = WorldState(
        width=2,
        height=2,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20),
        ),
    )
    checkpoint = world.effect_count

    world.set_environmental_value("temperature", x=1, y=0, value=20)
    assert world.effect_count == checkpoint

    world.change_environmental_value("temperature", x=1, y=0, delta=2.5)

    assert world.effects_since(checkpoint) == (
        EnvironmentalValueChanged(
            field_name="temperature",
            x=1,
            y=0,
            before=20,
            after=22.5,
        ),
    )


def test_environmental_fields_reject_unknown_names_and_invalid_coordinates() -> None:
    """Test environmental access validates field identity and world bounds."""
    world = WorldState(
        width=2,
        height=2,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20),
        ),
    )

    with pytest.raises(KeyError, match="humidity"):
        world.environmental_value("humidity", x=0, y=0)

    with pytest.raises(ValueError):
        world.set_environmental_value("temperature", x=2, y=0, value=21)


def test_environmental_field_definitions_are_unique_and_finite() -> None:
    """Test environmental field definitions are meaningful and unambiguous."""
    with pytest.raises(ValueError, match="duplicate"):
        WorldState(
            width=2,
            height=2,
            environmental_fields=(
                EnvironmentalField(name="temperature", default_value=20),
                EnvironmentalField(name="temperature", default_value=21),
            ),
        )

    with pytest.raises(ValueError, match="finite"):
        EnvironmentalField(name="temperature", default_value=math.inf)

    with pytest.raises(ValueError, match="name"):
        EnvironmentalField(name="   ", default_value=20)


def test_copy_is_transactionally_independent() -> None:
    """Test that a world copy can mutate without changing the original."""
    world = WorldState(
        width=3,
        height=3,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20),
        ),
    )
    organism = make_organism(energy=10)
    world.add_organism(organism)
    world.add_resources(x=0, y=0, amount=5)
    world.set_environmental_value("temperature", x=0, y=0, value=22)

    copied = world.copy()
    copied.organisms[0].energy = 1
    copied.add_resources(x=0, y=0, amount=2)
    copied.set_environmental_value("temperature", x=0, y=0, value=25)

    assert world.organisms[0].energy == 10
    assert world.resources[(0, 0)] == 5
    assert world.environmental_value("temperature", x=0, y=0) == 22
    assert copied.environmental_value("temperature", x=0, y=0) == 25
    assert copied.organisms[0].genome is world.organisms[0].genome
    assert copied.effect_count == 2
