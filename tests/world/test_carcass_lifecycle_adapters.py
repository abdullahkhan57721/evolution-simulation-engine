"""Tests for carcass adapters over generic entity lifecycle contracts."""

from __future__ import annotations

import pytest

from evo_engine.world import (
    Carcass,
    WorldCarcassAccess,
    WorldCarcassAdmission,
    WorldCarcassDeparture,
    WorldCarcassReference,
    WorldState,
)


def test_carcass_lifecycle_adapters_share_world_membership_semantics() -> None:
    """Test carcass admission, access, reference, and departure compose."""
    world = WorldState(width=4, height=4)
    carcass = Carcass(x=1, y=2, resource_units=5)

    WorldCarcassAdmission().admit(carcass, state=world)

    assert carcass.id == 0
    assert WorldCarcassAccess().entities(state=world) == (carcass,)
    assert WorldCarcassAccess().get(carcass.id, state=world) is carcass
    assert WorldCarcassReference().reference(carcass, state=world) == carcass.id

    removed = WorldCarcassDeparture().depart(carcass.id, state=world)

    assert removed is carcass
    assert not world.carcasses
    assert world.effect_count == 2


def test_carcass_reference_is_state_local() -> None:
    """Test equal numeric carcass IDs do not create cross-world references."""
    first_world = WorldState(width=2, height=2)
    second_world = WorldState(width=2, height=2)
    first = Carcass(x=0, y=0, resource_units=1)
    second = Carcass(x=0, y=0, resource_units=1)
    first_world.add_carcass(first)
    second_world.add_carcass(second)

    assert first.id == second.id == 0

    with pytest.raises(ValueError, match="registered under its ID"):
        WorldCarcassReference().reference(first, state=second_world)
