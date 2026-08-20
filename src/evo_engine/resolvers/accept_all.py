"""Accept-all simulation event resolver."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState


class AcceptAll:
    """Accept all proposed events without modification."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[SimulationEvent]:
        """Accept all proposed events.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            All proposed events in their original order.
        """
        return list(proposed_events)
