"""Equal-share resource-allocation resolver."""

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


class EqualShare:
    """Allocate local resources as equally as possible."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[ResourceConsumption.Event]:
        """Allocate resources equally among requests at each coordinate.

        Requests smaller than their equal share are fully satisfied, and
        unused resources are redistributed among the remaining requests.
        Integer remainders are distributed in proposal order.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            Resolved Resource Consumption events.
        """
        resource_events = require_resource_consumption_events(proposed_events)
        allocations = [0] * len(resource_events)

        for coordinate, indices in group_event_indices_by_coordinate(
            resource_events
        ).items():
            available = simulation_state.domain_state.resources.get(
                coordinate,
                0,
            )
            self._allocate_coordinate(
                resource_events,
                indices,
                available=available,
                allocations=allocations,
            )

        return build_resolved_events(
            resource_events,
            allocations,
        )

    @staticmethod
    def _allocate_coordinate(
        resource_events: list[ResourceConsumption.Event],
        indices: list[int],
        *,
        available: int,
        allocations: list[int],
    ) -> None:
        """Allocate one coordinate's resources by repeated water filling."""
        active_indices = [
            index for index in indices if resource_events[index].amount > 0
        ]

        while available > 0 and active_indices:
            equal_share = available // len(active_indices)

            if equal_share == 0:
                for index in active_indices[:available]:
                    allocations[index] += 1
                return

            distributed = EqualShare._allocate_round(
                resource_events,
                active_indices,
                equal_share=equal_share,
                allocations=allocations,
            )
            available -= distributed

            active_indices = [
                index
                for index in active_indices
                if allocations[index] < resource_events[index].amount
            ]

            if distributed == 0:
                return

    @staticmethod
    def _allocate_round(
        resource_events: list[ResourceConsumption.Event],
        active_indices: list[int],
        *,
        equal_share: int,
        allocations: list[int],
    ) -> int:
        """Apply one equal-share allocation round and return units distributed."""
        distributed = 0

        for index in active_indices:
            remaining_request = resource_events[index].amount - allocations[index]
            allocation = min(
                equal_share,
                remaining_request,
            )
            allocations[index] += allocation
            distributed += allocation

        return distributed
