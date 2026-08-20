"""Preference-order Predation resolver."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.processes.predation import Predation
from evo_engine.resolvers._preference_order import (
    resolve_exclusive_preference_order,
)


class PreferenceOrder:
    """Resolve Predation events according to predator preference."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[Predation.Event]:
        """Resolve Predation events according to preference score.

        Events with higher predator preference are considered first. Each
        organism may participate in at most one resolved Predation event,
        either as predator or prey. Proposal order breaks preference ties.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            Compatible resolved Predation events.
        """
        return resolve_exclusive_preference_order(
            proposed_events,
            event_type=Predation.Event,
            preference_score=lambda event: event.preference_score,
            participant_ids=lambda event: (
                event.predator_id,
                event.prey_id,
            ),
            resolver_name=type(self).__name__,
        )
