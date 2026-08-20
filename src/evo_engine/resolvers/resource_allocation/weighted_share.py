"""Weighted-share resource-allocation resolver."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import attrs

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import validate_required_traits
from evo_engine.processes.resource_consumption import ResourceConsumption
from evo_engine.resolvers.resource_allocation._common import (
    build_resolved_events,
    group_event_indices_by_coordinate,
    require_resource_consumption_events,
)
from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class WeightedShare:
    """Allocate local resources proportionally to configured organism weights.

    Attributes:
        weight_function: Function returning a nonnegative integer allocation
            weight for an organism.
        required_traits: Phenotype traits read by the custom weight function.
    """

    weight_function: Callable[
        [Organism, SimulationState],
        int,
    ]
    required_traits: frozenset[str] = attrs.field(
        factory=frozenset,
    )

    def __attrs_post_init__(self) -> None:
        """Validate explicitly declared phenotype dependencies."""
        validate_required_traits(
            self.required_traits,
            name="required_traits",
        )

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> list[ResourceConsumption.Event]:
        """Allocate resources proportionally to weights at each coordinate.

        Resource allocation is capped by each organism's requested amount.
        Resources left by satisfied requests are redistributed among the
        remaining eligible requests. Integer remainders are distributed by
        largest fractional remainder, with proposal order breaking ties.

        Args:
            simulation_state: Current simulation state.
            proposed_events: Proposed simulation events.

        Returns:
            Resolved Resource Consumption events.
        """
        resource_events = require_resource_consumption_events(proposed_events)
        allocations = [0] * len(resource_events)
        weights = self._calculate_weights(
            simulation_state,
            resource_events,
        )

        for coordinate, indices in group_event_indices_by_coordinate(
            resource_events
        ).items():
            available = simulation_state.world.resources.get(
                coordinate,
                0,
            )
            self._allocate_coordinate(
                resource_events,
                indices,
                weights=weights,
                available=available,
                allocations=allocations,
            )

        return build_resolved_events(
            resource_events,
            allocations,
        )

    def _calculate_weights(
        self,
        simulation_state: SimulationState,
        resource_events: list[ResourceConsumption.Event],
    ) -> list[int]:
        """Return validated allocation weights in proposal order."""
        weights: list[int] = []

        for event in resource_events:
            organism = simulation_state.world.organisms[event.organism_id]
            weight = self.weight_function(
                organism,
                simulation_state,
            )

            if type(weight) is not int:
                raise TypeError("weight_function must return an integer.")

            if weight < 0:
                raise ValueError("Allocation weights must be nonnegative.")

            weights.append(weight)

        return weights

    @staticmethod
    def _allocate_coordinate(
        resource_events: list[ResourceConsumption.Event],
        indices: list[int],
        *,
        weights: list[int],
        available: int,
        allocations: list[int],
    ) -> None:
        """Allocate one coordinate's resources in proportional rounds."""
        while available > 0:
            active_indices = WeightedShare._active_indices(
                resource_events,
                indices,
                weights=weights,
                allocations=allocations,
            )

            if not active_indices:
                return

            distributed, remainders = WeightedShare._allocate_weighted_round(
                resource_events,
                active_indices,
                weights=weights,
                available=available,
                allocations=allocations,
            )
            available -= distributed

            if available == 0:
                return

            remainder_candidates = [
                index
                for index in active_indices
                if allocations[index] < resource_events[index].amount
            ]

            if not remainder_candidates:
                return

            remainder_distributed = WeightedShare._distribute_remainder(
                remainder_candidates,
                remainders=remainders,
                available=available,
                allocations=allocations,
            )
            available -= remainder_distributed

            if distributed == 0 and remainder_distributed == 0:
                return

    @staticmethod
    def _active_indices(
        resource_events: list[ResourceConsumption.Event],
        indices: list[int],
        *,
        weights: list[int],
        allocations: list[int],
    ) -> list[int]:
        """Return indices with remaining demand and positive weight."""
        return [
            index
            for index in indices
            if (
                allocations[index] < resource_events[index].amount
                and weights[index] > 0
            )
        ]

    @staticmethod
    def _allocate_weighted_round(
        resource_events: list[ResourceConsumption.Event],
        active_indices: list[int],
        *,
        weights: list[int],
        available: int,
        allocations: list[int],
    ) -> tuple[int, dict[int, int]]:
        """Apply floor-weighted shares and return distribution metadata."""
        total_weight = sum(weights[index] for index in active_indices)
        distributed = 0
        remainders: dict[int, int] = {}

        for index in active_indices:
            weighted_amount = available * weights[index]
            proportional_share, remainder = divmod(
                weighted_amount,
                total_weight,
            )
            remaining_request = resource_events[index].amount - allocations[index]
            allocation = min(
                proportional_share,
                remaining_request,
            )

            allocations[index] += allocation
            distributed += allocation
            remainders[index] = remainder

        return distributed, remainders

    @staticmethod
    def _distribute_remainder(
        active_indices: list[int],
        *,
        remainders: dict[int, int],
        available: int,
        allocations: list[int],
    ) -> int:
        """Distribute remaining integer units by largest fractional remainder."""
        remainder_order = sorted(
            active_indices,
            key=lambda index: (
                -remainders[index],
                index,
            ),
        )
        units_to_distribute = min(
            available,
            len(remainder_order),
        )

        for index in remainder_order[:units_to_distribute]:
            allocations[index] += 1

        return units_to_distribute
