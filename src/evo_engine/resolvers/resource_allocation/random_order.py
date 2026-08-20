"""Random-order resource-allocation resolver."""

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


class RandomOrder:
    """Allocate local resources according to random request order."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[ResourceConsumption.Event]:
        """Allocate resources in random request order at each coordinate.

        Request order is randomized independently within each coordinate.
        Resolved events retain their original proposal order.

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
            available = simulation_state.world.resources.get(
                coordinate,
                0,
            )

            random_order = list(indices)

            simulation_state.rng.shuffle(random_order)

            for index in random_order:
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
