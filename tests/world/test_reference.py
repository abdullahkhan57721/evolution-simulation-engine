"""Tests for world-specific organism reference adapters."""

from __future__ import annotations

import pytest

from evo_engine.world import WorldOrganismReference
from tests.helpers import add_organism, make_state


def test_world_organism_reference_returns_registered_id_without_mutation() -> None:
    """Test world reference derivation preserves state and returns permanent ID."""
    state = make_state()
    organism = add_organism(state)
    checkpoint = state.domain_state.effect_count

    reference = WorldOrganismReference().reference(
        organism,
        state=state.domain_state,
    )

    assert reference == organism.id
    assert state.domain_state.effects_since(checkpoint) == ()


def test_world_organism_reference_rejects_entity_from_another_world() -> None:
    """Test equal numeric IDs do not make references valid across worlds."""
    state = make_state()
    add_organism(state)
    other_state = make_state()
    foreign = add_organism(other_state)

    with pytest.raises(
        ValueError,
        match="entity must be the organism registered under its ID in state",
    ):
        WorldOrganismReference().reference(
            foreign,
            state=state.domain_state,
        )
