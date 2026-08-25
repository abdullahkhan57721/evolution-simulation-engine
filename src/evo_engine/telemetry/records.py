"""Immutable telemetry records for committed simulation events."""

from __future__ import annotations

import math
from typing import TypeAlias

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class OrganismAdded:
    """Record an organism added to the world.

    Attributes:
        organism_id: Permanent ID assigned to the added organism.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class OrganismRemoved:
    """Record an organism removed from the active world.

    Attributes:
        organism_id: Permanent ID of the removed organism.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class OrganismMoved:
    """Record an organism coordinate change.

    Attributes:
        organism_id: Permanent organism ID.
        from_x: Previous horizontal coordinate.
        from_y: Previous vertical coordinate.
        to_x: New horizontal coordinate.
        to_y: New vertical coordinate.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    from_x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    from_y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    to_x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    to_y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class CarcassAdded:
    """Record a carcass added to the world.

    Attributes:
        carcass_id: Permanent ID assigned to the carcass.
    """

    carcass_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class CarcassRemoved:
    """Record a carcass removed from the world.

    Attributes:
        carcass_id: Permanent ID of the removed carcass.
    """

    carcass_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )


@attrs.frozen(slots=True, kw_only=True)
class ResourcesChanged:
    """Record a resource quantity change at one coordinate.

    Attributes:
        x: Horizontal coordinate.
        y: Vertical coordinate.
        before: Resource quantity before the mutation.
        after: Resource quantity after the mutation.
    """

    x: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    before: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    after: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    @property
    def delta(self) -> int:
        """Return signed resource change."""
        return self.after - self.before


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentalValueChanged:
    """Record one spatial environmental scalar-value change.

    Attributes:
        field_name: Name of the environmental field that changed.
        x: Horizontal coordinate.
        y: Vertical coordinate.
        before: Finite field value before the mutation.
        after: Finite field value after the mutation.
    """

    field_name: str = attrs.field(validator=attrs_validators.validate_str)
    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    before: int | float
    after: int | float

    def __attrs_post_init__(self) -> None:
        """Validate field naming and finite before/after values."""
        if not self.field_name.strip():
            raise ValueError("field_name must not be empty or whitespace-only.")
        _validate_finite_number(self.before, name="before")
        _validate_finite_number(self.after, name="after")

    @property
    def delta(self) -> int | float:
        """Return signed environmental-value change."""
        return self.after - self.before


WorldMutation: TypeAlias = (
    OrganismAdded
    | OrganismRemoved
    | OrganismMoved
    | CarcassAdded
    | CarcassRemoved
    | ResourcesChanged
    | EnvironmentalValueChanged
)

_WORLD_MUTATION_TYPES = (
    OrganismAdded,
    OrganismRemoved,
    OrganismMoved,
    CarcassAdded,
    CarcassRemoved,
    ResourcesChanged,
    EnvironmentalValueChanged,
)


@attrs.frozen(slots=True, kw_only=True)
class AppliedEvent:
    """Record one successfully applied materialized simulation event.

    ``event`` retains the materialized domain event so process-specific details
    remain available without coupling telemetry to concrete process packages.
    Built-in engine events are immutable value objects.

    Attributes:
        event_step_index: Simulation step index carried by the applied event.
        stage_index: Zero-based lifecycle stage index in which the event occurred.
        process_type: Fully qualified process class name.
        event_type: Fully qualified materialized event class name.
        event: Materialized event supplied to the process application method.
        world_mutations: Structural world mutations caused by the event.
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
    world_mutations: tuple[WorldMutation, ...] = attrs.field(
        factory=tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate telemetry naming and mutation invariants."""
        if not self.process_type.strip():
            raise ValueError("process_type must not be empty or whitespace-only.")
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty or whitespace-only.")

        validators.validate_tuple(
            self.world_mutations,
            name="world_mutations",
        )
        for index, mutation in enumerate(self.world_mutations):
            if not isinstance(mutation, _WORLD_MUTATION_TYPES):
                raise TypeError(
                    f"world_mutations[{index}] must be a WorldMutation; "
                    f"received {mutation!r}."
                )

    @property
    def process_name(self) -> str:
        """Return the unqualified process class name."""
        return self.process_type.rsplit(".", 1)[-1]

    @property
    def event_name(self) -> str:
        """Return the unqualified event class name."""
        return self.event_type.rsplit(".", 1)[-1]

    @property
    def added_organism_ids(self) -> tuple[int, ...]:
        """Return organism IDs added by this event."""
        return tuple(
            mutation.organism_id
            for mutation in self.world_mutations
            if isinstance(mutation, OrganismAdded)
        )

    @property
    def removed_organism_ids(self) -> tuple[int, ...]:
        """Return organism IDs removed by this event."""
        return tuple(
            mutation.organism_id
            for mutation in self.world_mutations
            if isinstance(mutation, OrganismRemoved)
        )


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


def _validate_finite_number(value: object, *, name: str) -> int | float:
    number = validators.validate_number(value, name=name)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite; received {number!r}.")
    return number
