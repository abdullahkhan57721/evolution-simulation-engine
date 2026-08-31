"""Shared greedy preference-order resolution."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable, Sequence
from typing import TypeVar

from evo_engine.engine.protocols import SimulationEvent

EventT = TypeVar(
    "EventT",
    bound=SimulationEvent,
)
ConflictKeyT = TypeVar(
    "ConflictKeyT",
    bound=Hashable,
)


def resolve_exclusive_preference_order(
    proposed_events: Sequence[SimulationEvent],
    *,
    event_type: type[EventT],
    preference_score: Callable[[EventT], int],
    participant_keys: Callable[[EventT], Iterable[ConflictKeyT]],
    resolver_name: str,
) -> list[EventT]:
    """Resolve events greedily by preference with exclusive conflict keys.

    This is the capacity-one specialization of
    ``resolve_capacity_preference_order``.

    Args:
        proposed_events: Proposed simulation events.
        event_type: Event type accepted by the resolver.
        preference_score: Function returning an event's preference score.
        participant_keys: Function returning hashable conflict keys for an event.
        resolver_name: Resolver name used in validation errors.

    Returns:
        Compatible events in greedy resolution order.

    Raises:
        TypeError: If a proposal is not of event_type.
        ValueError: If an event reports duplicate conflict keys.
    """
    return resolve_capacity_preference_order(
        proposed_events,
        event_type=event_type,
        preference_score=preference_score,
        participant_keys=participant_keys,
        max_events_per_key=1,
        resolver_name=resolver_name,
    )


def resolve_capacity_preference_order(
    proposed_events: Sequence[SimulationEvent],
    *,
    event_type: type[EventT],
    preference_score: Callable[[EventT], int],
    participant_keys: Callable[[EventT], Iterable[ConflictKeyT]],
    max_events_per_key: int,
    resolver_name: str,
) -> list[EventT]:
    """Resolve preferred events subject to per-key acceptance capacity.

    Higher preference scores are considered first and proposal order breaks
    ties. Each accepted event consumes one unit of capacity for every conflict
    key it reports. A later event is rejected when any of its keys has already
    reached ``max_events_per_key`` accepted uses.

    Conflict keys may be any hashable domain reference or resource token. The
    algorithm assigns no biological meaning to the keys or to event contents.

    Args:
        proposed_events: Proposed simulation events.
        event_type: Event type accepted by the resolver.
        preference_score: Function returning an event's preference score.
        participant_keys: Function returning hashable conflict keys for an event.
        max_events_per_key: Maximum accepted events containing any one key.
        resolver_name: Resolver name used in validation errors.

    Returns:
        Capacity-compatible events in greedy resolution order.

    Raises:
        TypeError: If max_events_per_key is not an integer or a proposal is not
            of event_type.
        ValueError: If max_events_per_key is less than one or an event reports
            duplicate conflict keys.
    """
    if type(max_events_per_key) is not int:
        raise TypeError("max_events_per_key must be an integer.")
    if max_events_per_key < 1:
        raise ValueError("max_events_per_key must be at least 1.")

    indexed_events = _validated_indexed_events(
        proposed_events,
        event_type=event_type,
        resolver_name=resolver_name,
    )
    ordered_events = sorted(
        indexed_events,
        key=lambda item: (
            -preference_score(item[1]),
            item[0],
        ),
    )

    accepted_counts: dict[ConflictKeyT, int] = {}
    resolved_events: list[EventT] = []

    for _, event in ordered_events:
        event_keys = _validated_event_keys(
            event,
            participant_keys=participant_keys,
            resolver_name=resolver_name,
        )
        if any(accepted_counts.get(key, 0) >= max_events_per_key for key in event_keys):
            continue

        resolved_events.append(event)
        for key in event_keys:
            accepted_counts[key] = accepted_counts.get(key, 0) + 1

    return resolved_events


def _validated_indexed_events(
    proposed_events: Sequence[SimulationEvent],
    *,
    event_type: type[EventT],
    resolver_name: str,
) -> list[tuple[int, EventT]]:
    indexed_events: list[tuple[int, EventT]] = []

    for proposal_index, proposed_event in enumerate(proposed_events):
        if not isinstance(proposed_event, event_type):
            raise TypeError(
                f"{resolver_name} only resolves {event_type.__qualname__} objects."
            )
        indexed_events.append((proposal_index, proposed_event))

    return indexed_events


def _validated_event_keys(
    event: EventT,
    *,
    participant_keys: Callable[[EventT], Iterable[ConflictKeyT]],
    resolver_name: str,
) -> tuple[ConflictKeyT, ...]:
    event_keys = tuple(participant_keys(event))
    if len(set(event_keys)) != len(event_keys):
        raise ValueError(
            f"{resolver_name} received an event with duplicate conflict keys."
        )
    return event_keys
