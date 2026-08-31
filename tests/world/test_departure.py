"""Tests for world-specific entity departure adapters."""

from __future__ import annotations

from evo_engine.telemetry import OrganismRemoved
from evo_engine.world import WorldOrganismDeparture
from tests.helpers import add_organism, make_state


def test_world_organism_departure_removes_and_returns_organism() -> None:
    """Test the adapter preserves WorldState removal mechanics."""
    state = make_state()
    organism = add_organism(state)
    checkpoint = state.world.mutation_count

    departed = WorldOrganismDeparture().depart(
        organism.id,
        state=state.world,
    )

    assert departed is organism
    assert organism.id not in state.world.organisms
    mutations = state.world.mutations_since(checkpoint)
    assert mutations == (OrganismRemoved(organism_id=organism.id),)
