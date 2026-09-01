"""Tests for world-specific entity access adapters."""

from __future__ import annotations

from evo_engine.world import WorldOrganismAccess
from tests.helpers import add_organism, make_state


def test_world_organism_access_gets_by_stable_identifier() -> None:
    """Test world access resolves organisms without mutating world state."""
    state = make_state()
    organism = add_organism(state)
    checkpoint = state.domain_state.effect_count

    resolved = WorldOrganismAccess().get(organism.id, state=state.domain_state)

    assert resolved is organism
    assert state.domain_state.effect_count == checkpoint


def test_world_organism_access_returns_stable_snapshot() -> None:
    """Test world enumeration is detached from later membership changes."""
    state = make_state()
    first = add_organism(state)
    access = WorldOrganismAccess()

    snapshot = access.entities(state=state.domain_state)
    second = add_organism(state)

    assert snapshot == (first,)
    assert access.entities(state=state.domain_state) == (first, second)
