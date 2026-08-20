"""Shared greedy preference-order resolution."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import TypeVar

from evo_engine.engine.protocols import SimulationEvent

EventT = TypeVar(
    "EventT",
    bound=SimulationEvent,
)


def resolve_exclusive_preference_order(
    proposed_events: Sequence[SimulationEvent],
    *,
    event_type: type[EventT],
    preference_score: Callable[[EventT], int],
    participant_ids: Callable[[EventT], Iterable[int]],
    resolver_name: str,
) -> list[EventT]:
    """Resolve events greedily by preference with exclusive participants.

    Higher preference scores are considered first. Proposal order breaks ties.
    Once an event is accepted, none of its participants may appear in another
    accepted event.

    Args:
        proposed_events: Proposed simulation events.
        event_type: Event type accepted by the resolver.
        preference_score: Function returning an event's preference score.
        participant_ids: Function returning IDs participating in an event.
        resolver_name: Resolver name used in validation errors.

    Returns:
        Compatible events in greedy resolution order.

    Raises:
        TypeError: If a proposal is not of event_type.
        ValueError: If an event reports duplicate participant IDs.
    """
    indexed_events: list[tuple[int, EventT]] = []

    for proposal_index, proposed_event in enumerate(proposed_events):
        if not isinstance(proposed_event, event_type):
            raise TypeError(
                f"{resolver_name} only resolves {event_type.__qualname__} objects."
            )

        indexed_events.append(
            (
                proposal_index,
                proposed_event,
            )
        )

    # Stable proposal indices make equal-preference outcomes deterministic.
    ordered_events = sorted(
        indexed_events,
        key=lambda item: (
            -preference_score(item[1]),
            item[0],
        ),
    )

    participating_ids: set[int] = set()
    resolved_events: list[EventT] = []

    for _, event in ordered_events:
        ids = tuple(participant_ids(event))

        if len(set(ids)) != len(ids):
            raise ValueError(
                f"{resolver_name} received an event with duplicate participant IDs."
            )

        event_ids = set(ids)

        # Greedy exclusivity turns the proposal graph into a compatible
        # matching without requiring a global optimization algorithm.
        if event_ids & participating_ids:
            continue

        resolved_events.append(event)
        participating_ids.update(event_ids)

    return resolved_events
