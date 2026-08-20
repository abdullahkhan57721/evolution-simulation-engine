"""Shared helpers for resource-allocation resolvers."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.engine.protocols import SimulationEvent
from evo_engine.processes.resource_consumption import ResourceConsumption


def require_resource_consumption_events(
    proposed_events: Sequence[SimulationEvent],
) -> list[ResourceConsumption.Event]:
    """Return proposed events as Resource Consumption events.

    Args:
        proposed_events: Proposed simulation events.

    Returns:
        Proposed Resource Consumption events.

    Raises:
        TypeError: If any proposed event is not a Resource Consumption event.
    """
    resource_events: list[ResourceConsumption.Event] = []

    for proposed_event in proposed_events:
        if not isinstance(
            proposed_event,
            ResourceConsumption.Event,
        ):
            raise TypeError(
                "Resource allocation resolvers only accept "
                "ResourceConsumption.Event objects."
            )

        resource_events.append(proposed_event)

    return resource_events


def build_resolved_events(
    proposed_events: Sequence[ResourceConsumption.Event],
    allocations: Sequence[int],
) -> list[ResourceConsumption.Event]:
    """Create resolved events from resource allocations.

    Zero-allocation events are omitted.

    Args:
        proposed_events: Proposed Resource Consumption events.
        allocations: Resource amount allocated to each proposed event.

    Returns:
        Resolved Resource Consumption events.
    """
    resolved_events: list[ResourceConsumption.Event] = []

    for proposed_event, allocation in zip(
        proposed_events,
        allocations,
        strict=True,
    ):
        if allocation == 0:
            continue

        resolved_events.append(
            attrs.evolve(
                proposed_event,
                amount=allocation,
            )
        )

    return resolved_events


def group_event_indices_by_coordinate(
    resource_events: Sequence[ResourceConsumption.Event],
) -> dict[tuple[int, int], list[int]]:
    """Group Resource Consumption event indices by coordinate.

    Args:
        resource_events: Proposed Resource Consumption events.

    Returns:
        Event indices grouped by resource coordinate.
    """
    indices_by_coordinate: dict[
        tuple[int, int],
        list[int],
    ] = {}

    for index, event in enumerate(resource_events):
        coordinate = (
            event.x,
            event.y,
        )

        indices_by_coordinate.setdefault(
            coordinate,
            [],
        ).append(index)

    return indices_by_coordinate
