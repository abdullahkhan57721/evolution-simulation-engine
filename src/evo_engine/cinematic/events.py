"""Select actual committed events for cinematic explanation."""

from __future__ import annotations

from evo_engine.cinematic.timeline import PortfolioAnimationTimeline
from evo_engine.telemetry import AppliedEvent
from evo_engine.validation import validators


def select_authoritative_events(
    timeline: PortfolioAnimationTimeline,
    *,
    event_name: str,
) -> tuple[AppliedEvent, ...]:
    """Return actual committed events matching one event class name.

    Selection follows displayed-frame chronology and preserves authoritative
    commit order inside each frame. The function never synthesizes an event from
    identity appearance, disappearance, proximity, or other visual inference.

    Args:
        timeline: Prepared cinematic timeline containing committed telemetry.
        event_name: Qualified or unqualified applied-event class name.

    Returns:
        Matching authoritative applied events in deterministic commit order.
    """
    if not isinstance(timeline, PortfolioAnimationTimeline):
        raise TypeError("timeline must be a PortfolioAnimationTimeline.")
    validated_name = validators.validate_str(event_name, name="event_name")
    if not validated_name.strip():
        raise ValueError("event_name must not be empty or whitespace-only.")
    return tuple(
        event
        for frame in timeline.frames
        for event in frame.applied_events
        if event.event_type == validated_name or event.event_name == validated_name
    )


def select_first_authoritative_event(
    timeline: PortfolioAnimationTimeline,
    *,
    event_name: str,
) -> AppliedEvent | None:
    """Return the first actual committed event matching ``event_name``, if any."""
    matches = select_authoritative_events(timeline, event_name=event_name)
    if not matches:
        return None
    return matches[0]
