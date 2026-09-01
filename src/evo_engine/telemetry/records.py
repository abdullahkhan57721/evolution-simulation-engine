"""Immutable telemetry records for committed simulation events."""

from __future__ import annotations

from typing import Self

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class AppliedEvent:
    """Record one successfully applied materialized simulation event.

    ``event`` retains the materialized domain event so process-specific details
    remain available without coupling telemetry to concrete process packages.
    ``effects`` contains opaque domain effect records captured during application;
    their meaning belongs to the modeled domain rather than the telemetry layer.

    Attributes:
        event_step_index: Simulation step index carried by the applied event.
        stage_index: Zero-based lifecycle stage index in which the event occurred.
        process_type: Fully qualified process class name.
        event_type: Fully qualified materialized event class name.
        event: Materialized event supplied to the process application method.
        effects: Domain effects caused by the event in occurrence order.
    """

    event_step_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    stage_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    process_type: str = attrs.field(
        validator=attrs_validators.validate_str,
    )
    event_type: str = attrs.field(
        validator=attrs_validators.validate_str,
    )
    event: object
    effects: tuple[object, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate telemetry naming and effect collection invariants."""
        if not self.process_type.strip():
            raise ValueError("process_type must not be empty or whitespace-only.")
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty or whitespace-only.")

        validators.validate_tuple(
            self.effects,
            name="effects",
        )

    @classmethod
    def _from_validated(
        cls,
        *,
        event_step_index: int,
        stage_index: int,
        process_type: str,
        event_type: str,
        event: object,
        effects: tuple[object, ...],
    ) -> Self:
        """Construct from values already validated by trusted kernel orchestration."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "event_step_index", event_step_index)
        object.__setattr__(instance, "stage_index", stage_index)
        object.__setattr__(instance, "process_type", process_type)
        object.__setattr__(instance, "event_type", event_type)
        object.__setattr__(instance, "event", event)
        object.__setattr__(instance, "effects", effects)
        return instance

    @property
    def process_name(self) -> str:
        """Return the unqualified process class name."""
        return self.process_type.rsplit(".", 1)[-1]

    @property
    def event_name(self) -> str:
        """Return the unqualified event class name."""
        return self.event_type.rsplit(".", 1)[-1]


@attrs.frozen(slots=True, kw_only=True)
class StepTelemetry:
    """Record all materialized events committed by one completed step.

    Attributes:
        completed_step_index: Authoritative state index after the step commits.
        events: Applied events in lifecycle and resolver application order.
    """

    completed_step_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    events: tuple[AppliedEvent, ...] = attrs.field(
        factory=tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate event collection contents."""
        validators.validate_tuple(
            self.events,
            name="events",
        )
        for index, event in enumerate(self.events):
            if not isinstance(event, AppliedEvent):
                raise TypeError(
                    f"events[{index}] must be an AppliedEvent; received {event!r}."
                )

    def events_for_process(self, process_name: str) -> tuple[AppliedEvent, ...]:
        """Return events produced by one process class name.

        Args:
            process_name: Qualified or unqualified process class name.

        Returns:
            Matching applied events in application order.
        """
        validated_name = validators.validate_str(
            process_name,
            name="process_name",
        )
        if not validated_name.strip():
            raise ValueError("process_name must not be empty or whitespace-only.")

        return tuple(
            event
            for event in self.events
            if event.process_type == validated_name
            or event.process_name == validated_name
        )
