"""Proposal-order resource-allocation resolver."""

from __future__ import annotations

from collections.abc import Sequence

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.processes.resource_consumption import ResourceConsumption
from evo_engine.resolvers.resource_allocation._common import (
    build_resolved_events,
    group_event_indices_by_coordinate,
    require_resource_consumption_events,
)


class ProposalOrder:
    """Allocate local resources according to proposal order."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[ResourceConsumption.Event]:
        """Allocate resources according to proposal order at each coordinate.

        Each request receives as much as possible before the next request at
        the same coordinate is considered.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            Resolved Resource Consumption events.
        """
        resource_events = require_resource_consumption_events(proposed_events)
        allocations = [0] * len(resource_events)

        indices_by_coordinate = group_event_indices_by_coordinate(resource_events)

        for coordinate, indices in indices_by_coordinate.items():
            available = simulation_state.domain_state.resources.get(
                coordinate,
                0,
            )

            for index in indices:
                if available == 0:
                    break

                allocation = min(
                    resource_events[index].amount,
                    available,
                )

                allocations[index] = allocation
                available -= allocation

        return build_resolved_events(
            resource_events,
            allocations,
        )
