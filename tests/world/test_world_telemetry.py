"""Tests for WorldState transaction-local effect telemetry."""

from __future__ import annotations

from evo_engine.world import OrganismMoved, OrganismRemoved, ResourcesChanged
from tests.helpers import add_organism, make_state


def test_world_journals_effects_in_occurrence_order() -> None:
    """Test structural world changes can be read from an effect checkpoint."""
    state = make_state()
    organism = add_organism(state, x=1, y=1)
    checkpoint = state.world.effect_count

    state.world.move_organism(organism_id=organism.id, x=2, y=1)
    state.world.add_resources(x=2, y=1, amount=5)
    state.world.remove_resources(x=2, y=1, amount=2)
    state.world.remove_organism(organism.id)

    assert state.world.effects_since(checkpoint) == (
        OrganismMoved(
            organism_id=organism.id,
            from_x=1,
            from_y=1,
            to_x=2,
            to_y=1,
        ),
        ResourcesChanged(x=2, y=1, before=0, after=5),
        ResourcesChanged(x=2, y=1, before=5, after=3),
        OrganismRemoved(organism_id=organism.id),
    )


def test_world_copy_starts_fresh_effect_journal() -> None:
    """Test transactional copies preserve ecology but not prior telemetry noise."""
    state = make_state()
    organism = add_organism(state)
    state.world.add_resources(x=0, y=0, amount=3)

    copied = state.world.copy()

    assert copied.effect_count == 0
    assert organism.id in copied.organisms
    assert copied.resources[(0, 0)] == 3
