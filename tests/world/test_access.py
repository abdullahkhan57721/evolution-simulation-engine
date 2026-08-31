"""Tests for world-specific entity access adapters."""

from __future__ import annotations

from evo_engine.world import WorldOrganismAccess
from tests.helpers import add_organism, make_state


def test_world_organism_access_gets_by_stable_identifier() -> None:
    """Test world access resolves organisms without mutating world state."""
    state = make_state()
    organism = add_organism(state)
    checkpoint = state.world.mutation_count

    resolved = WorldOrganismAccess().get(organism.id, state=state.world)

    assert resolved is organism
    assert state.world.mutation_count == checkpoint


def test_world_organism_access_returns_stable_snapshot() -> None:
    """Test world enumeration is detached from later membership changes."""
    state = make_state()
    first = add_organism(state)
    access = WorldOrganismAccess()

    snapshot = access.entities(state=state.world)
    second = add_organism(state)

    assert snapshot == (first,)
    assert access.entities(state=state.world) == (first, second)
