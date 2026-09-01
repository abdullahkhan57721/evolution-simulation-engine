"""Tests for predation proposal reference caching."""

from __future__ import annotations

from collections import Counter

from evo_engine.processes import Predation
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState
from tests.helpers import add_organism, make_integer_architecture, make_state


class CountingOrganismReference:
    """Count world-reference derivations while preserving reference semantics."""

    def __init__(self) -> None:
        self.calls: list[int] = []
        self.delegate = WorldOrganismReference()

    def reference(
        self,
        entity: Organism,
        *,
        state: WorldState,
    ) -> int:
        """Record and delegate one organism-reference derivation."""
        self.calls.append(entity.id)
        return self.delegate.reference(entity, state=state)


def test_predation_derives_each_snapshot_reference_once() -> None:
    """Test pair enumeration reuses one reference per snapshot organism."""
    architecture = make_integer_architecture("adult_body_mass")
    state = make_state(genetic_architecture=architecture)
    predator = add_organism(
        state,
        trait_values={"adult_body_mass": 10},
        energy=20,
        x=1,
        y=1,
    )
    prey = add_organism(
        state,
        trait_values={"adult_body_mass": 6},
        energy=20,
        x=1,
        y=1,
    )
    reference_model = CountingOrganismReference()

    events = Predation(
        neighborhood=SameCell(),
        consumption_percent=50,
        reference_model=reference_model,
    ).propose_events(state)

    assert len(events) == 1
    assert Counter(reference_model.calls) == Counter({predator.id: 1, prey.id: 1})
