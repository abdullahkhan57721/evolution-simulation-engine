"""Tests for world-specific entity departure adapters."""

from __future__ import annotations

from evo_engine.world import OrganismRemoved, WorldOrganismDeparture
from tests.helpers import add_organism, make_state


def test_world_organism_departure_removes_and_returns_organism() -> None:
    """Test the adapter preserves WorldState removal mechanics."""
    state = make_state()
    organism = add_organism(state)
    checkpoint = state.domain_state.effect_count

    departed = WorldOrganismDeparture().depart(
        organism.id,
        state=state.domain_state,
    )

    assert departed is organism
    assert organism.id not in state.domain_state.organisms
    effects = state.domain_state.effects_since(checkpoint)
    assert effects == (OrganismRemoved(organism_id=organism.id),)
