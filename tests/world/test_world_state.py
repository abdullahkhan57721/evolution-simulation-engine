"""Tests for WorldState."""

from __future__ import annotations

import pytest

from evo_engine.world import Carcass, WorldState
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


def test_copy_is_transactionally_independent() -> None:
    """Test that a world copy can mutate without changing the original."""
    world = WorldState(width=3, height=3)
    organism = make_organism(energy=10)
    world.add_organism(organism)
    world.add_resources(x=0, y=0, amount=5)

    copied = world.copy()
    copied.organisms[0].energy = 1
    copied.add_resources(x=0, y=0, amount=2)

    assert world.organisms[0].energy == 10
    assert world.resources[(0, 0)] == 5
    assert copied.organisms[0].genome is world.organisms[0].genome
