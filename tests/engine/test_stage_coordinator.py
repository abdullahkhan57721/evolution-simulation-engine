"""Tests for StageCoordinator."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.engine import StageCoordinator
from evo_engine.resolvers import AcceptAll
from tests.helpers import add_organism, make_state


@attrs.frozen(slots=True, kw_only=True)
class IncrementProcess:
    """Minimal process used to exercise stage orchestration."""

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Increment event."""

        step_index: int
        organism_id: int
        amount: int

    @property
    def event_type(self) -> type[Event]:
        """Return the proposal type."""
        return self.Event

    def propose_events(self, simulation_state):
        """Propose one increment."""
        return [
            self.Event(
                step_index=simulation_state.step_index,
                organism_id=0,
                amount=1,
            )
        ]

    def apply_event(self, simulation_state, materialized_event) -> None:
        """Apply the increment."""
        simulation_state.world.organisms[0].energy += materialized_event.amount


def test_coordinate_proposes_resolves_and_applies() -> None:
    """Test the normal stage lifecycle for a simple process."""
    state = make_state()
    add_organism(state, energy=10)

    StageCoordinator(
        processes=(IncrementProcess(),),
        resolver=AcceptAll(),
    ).coordinate(state)

    assert state.world.organisms[0].energy == 11


def test_stage_rejects_duplicate_proposed_event_types() -> None:
    """Test unambiguous event-to-process ownership within a stage."""
    with pytest.raises(ValueError):
        StageCoordinator(
            processes=(
                IncrementProcess(),
                IncrementProcess(),
            ),
            resolver=AcceptAll(),
        )


def test_resolved_unknown_event_type_raises() -> None:
    """Test that resolvers cannot inject events with no owning process."""
    state = make_state()
    add_organism(state)

    @attrs.frozen(slots=True, kw_only=True)
    class ForeignEvent:
        step_index: int

    class ForeignResolver:
        def resolve_events(self, simulation_state, proposed_events):
            return [ForeignEvent(step_index=simulation_state.step_index)]

    coordinator = StageCoordinator(
        processes=(IncrementProcess(),),
        resolver=ForeignResolver(),
    )

    with pytest.raises(RuntimeError):
        coordinator.coordinate(state)


def test_all_events_materialize_before_any_apply() -> None:
    """Test that materializers observe the same pre-application world."""
    state = make_state()
    add_organism(state, energy=10)
    observations: list[int] = []

    @attrs.frozen(slots=True, kw_only=True)
    class MaterializingProcess:
        @attrs.frozen(slots=True, kw_only=True)
        class Proposal:
            step_index: int
            amount: int

        @attrs.frozen(slots=True, kw_only=True)
        class Event:
            step_index: int
            amount: int
            observed_energy: int

        @property
        def event_type(self):
            return self.Proposal

        def propose_events(self, simulation_state):
            return [
                self.Proposal(
                    step_index=simulation_state.step_index,
                    amount=1,
                ),
                self.Proposal(
                    step_index=simulation_state.step_index,
                    amount=1,
                ),
            ]

        def materialize_event(self, simulation_state, resolved_event):
            observations.append(simulation_state.world.organisms[0].energy)
            return self.Event(
                step_index=resolved_event.step_index,
                amount=resolved_event.amount,
                observed_energy=simulation_state.world.organisms[0].energy,
            )

        def apply_event(self, simulation_state, materialized_event) -> None:
            assert materialized_event.observed_energy == 10
            simulation_state.world.organisms[0].energy -= materialized_event.amount

    StageCoordinator(
        processes=(MaterializingProcess(),),
        resolver=AcceptAll(),
    ).coordinate(state)

    assert observations == [10, 10]
    assert state.world.organisms[0].energy == 8
