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

    Higher preference scores are considered first. Proposal order breaks ties.
    Once an event is accepted, none of its conflict keys may appear in another
    accepted event. Keys may be any hashable domain reference or resource token;
    the resolver does not interpret their meaning.

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

    participating_keys: set[ConflictKeyT] = set()
    resolved_events: list[EventT] = []

    for _, event in ordered_events:
        event_keys = tuple(participant_keys(event))

        if len(set(event_keys)) != len(event_keys):
            raise ValueError(
                f"{resolver_name} received an event with duplicate conflict keys."
            )

        conflict_keys = set(event_keys)

        # Greedy exclusivity turns the proposal graph into a compatible
        # matching without requiring a global optimization algorithm.
        if conflict_keys & participating_keys:
            continue

        resolved_events.append(event)
        participating_keys.update(conflict_keys)

    return resolved_events
