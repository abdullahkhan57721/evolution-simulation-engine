"""Domain-neutral fixtures shared by kernel tests."""

from __future__ import annotations

import copy

import attrs

from evo_engine.engine import SimulationState


@attrs.define(slots=True)
class CounterState:
    """Minimal copyable state for kernel execution tests."""

    value: int = 0
    notes: list[str] = attrs.field(factory=list)

    def copy(self) -> CounterState:
        """Return an independent transactional copy."""
        return copy.deepcopy(self)


@attrs.frozen(slots=True, kw_only=True)
class IncrementEvent:
    """Represent one generic counter increment."""

    step_index: int
    amount: int = 1


@attrs.frozen(slots=True, kw_only=True)
class IncrementProcess:
    """Increment the counter by a configured amount."""

    amount: int = 1

    @property
    def event_type(self) -> type[IncrementEvent]:
        """Return the proposal type."""
        return IncrementEvent

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[IncrementEvent]:
        """Propose one increment from the current committed index."""
        return [
            IncrementEvent(
                step_index=simulation_state.step_index,
                amount=self.amount,
            )
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: IncrementEvent,
        /,
    ) -> None:
        """Apply one increment."""
        simulation_state.world.value += event.amount
