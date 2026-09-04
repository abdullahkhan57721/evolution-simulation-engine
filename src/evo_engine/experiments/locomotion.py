"""Pure locomotion measurements derived from committed movement evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence

import attrs

from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.processes import Movement
from evo_engine.telemetry import AppliedEvent
from evo_engine.validation import validators
from evo_engine.world import OrganismMoved


@attrs.frozen(slots=True, kw_only=True)
class AppliedMovementMeasurement:
    """Measure one successfully applied locomotion event.

    Attempted distance comes from the materialized movement event. Realized
    distance comes from the committed ``OrganismMoved`` effect, so boundary
    resolution or a no-op endpoint cannot be mistaken for actual displacement.

    Attributes:
        event_step_index: Pre-step index carried by the applied event.
        completed_step_index: Committed-state index caused by the event.
        organism_id: Permanent ID of the moving organism.
        attempted_distance: Euclidean magnitude of the attempted displacement.
        realized_distance: Euclidean committed coordinate displacement.
        locomotion_energy_expenditure: Energy charged by the applied movement.
    """

    event_step_index: int
    completed_step_index: int
    organism_id: int
    attempted_distance: float
    realized_distance: float
    locomotion_energy_expenditure: int

    def __attrs_post_init__(self) -> None:
        """Validate measurement values and event/state alignment."""
        validators.validate_int_ge(
            self.event_step_index,
            bound=0,
            name="event_step_index",
        )
        validators.validate_int_ge(
            self.completed_step_index,
            bound=1,
            name="completed_step_index",
        )
        if self.completed_step_index != self.event_step_index + 1:
            raise ValueError(
                "completed_step_index must equal event_step_index + 1."
            )
        validators.validate_int_ge(self.organism_id, bound=0, name="organism_id")
        _validate_nonnegative_finite_float(
            self.attempted_distance,
            name="attempted_distance",
        )
        _validate_nonnegative_finite_float(
            self.realized_distance,
            name="realized_distance",
        )
        validators.validate_int_ge(
            self.locomotion_energy_expenditure,
            bound=0,
            name="locomotion_energy_expenditure",
        )


@attrs.frozen(slots=True, kw_only=True)
class LocomotionReplicateMeasurements:
    """Store explicit-denominator locomotion measurements for one run/seed."""

    provenance: ScientificRunProvenance
    applied_movement_count: int
    total_attempted_distance: float
    total_realized_distance: float
    mean_realized_distance_per_applied_movement: float | None
    total_locomotion_energy_expenditure: int

    def __attrs_post_init__(self) -> None:
        """Validate replicate measurement denominators and totals."""
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        validators.validate_int_ge(
            self.applied_movement_count,
            bound=0,
            name="applied_movement_count",
        )
        _validate_nonnegative_finite_float(
            self.total_attempted_distance,
            name="total_attempted_distance",
        )
        _validate_nonnegative_finite_float(
            self.total_realized_distance,
            name="total_realized_distance",
        )
        if self.mean_realized_distance_per_applied_movement is None:
            if self.applied_movement_count != 0:
                raise ValueError(
                    "mean_realized_distance_per_applied_movement may be None only "
                    "when applied_movement_count is zero."
                )
        else:
            _validate_nonnegative_finite_float(
                self.mean_realized_distance_per_applied_movement,
                name="mean_realized_distance_per_applied_movement",
            )
            if self.applied_movement_count == 0:
                raise ValueError(
                    "mean_realized_distance_per_applied_movement must be None "
                    "when applied_movement_count is zero."
                )
        validators.validate_int_ge(
            self.total_locomotion_energy_expenditure,
            bound=0,
            name="total_locomotion_energy_expenditure",
        )


def measure_applied_movement(
    applied_event: AppliedEvent,
) -> AppliedMovementMeasurement:
    """Derive one locomotion measurement from authoritative committed evidence.

    Args:
        applied_event: Successfully applied telemetry wrapping ``Movement.Event``.

    Returns:
        Immutable measurement separating attempted and realized displacement.

    Raises:
        TypeError: If the telemetry does not contain a movement event.
        ValueError: If event/effect evidence is internally inconsistent.
    """
    if not isinstance(applied_event, AppliedEvent):
        raise TypeError("applied_event must be an AppliedEvent.")
    event = applied_event.event
    if not isinstance(event, Movement.Event):
        raise TypeError("applied_event must contain a Movement.Event.")
    if event.step_index != applied_event.event_step_index:
        raise ValueError(
            "Movement.Event.step_index must match AppliedEvent.event_step_index."
        )

    movement_effects = tuple(
        effect for effect in applied_event.effects if isinstance(effect, OrganismMoved)
    )
    if len(movement_effects) > 1:
        raise ValueError("One applied movement must not contain multiple move effects.")

    realized_distance = 0.0
    if movement_effects:
        effect = movement_effects[0]
        if effect.organism_id != event.organism_id:
            raise ValueError("Movement event/effect organism IDs must match.")
        if (effect.to_x, effect.to_y) != (event.new_x, event.new_y):
            raise ValueError("Movement event endpoint must match its committed effect.")
        realized_distance = math.hypot(
            effect.to_x - effect.from_x,
            effect.to_y - effect.from_y,
        )

    return AppliedMovementMeasurement(
        event_step_index=applied_event.event_step_index,
        completed_step_index=applied_event.completed_step_index,
        organism_id=event.organism_id,
        attempted_distance=math.hypot(event.dx, event.dy),
        realized_distance=realized_distance,
        locomotion_energy_expenditure=event.energy_cost,
    )


def summarize_locomotion_replicate(
    *,
    provenance: ScientificRunProvenance,
    events: Sequence[AppliedEvent],
) -> LocomotionReplicateMeasurements:
    """Summarize committed movement evidence for exactly one simulation replicate.

    The denominator of ``mean_realized_distance_per_applied_movement`` is the
    number of successfully applied ``Movement.Event`` records. A run with no
    applied movement has an undefined mean represented by ``None``, not zero.

    Args:
        provenance: Scientific identity of the one run/seed being summarized.
        events: Committed applied-event evidence from that run.

    Returns:
        Locomotion totals and explicit-denominator mean for the replicate.
    """
    if not isinstance(provenance, ScientificRunProvenance):
        raise TypeError("provenance must be a ScientificRunProvenance.")

    measurements: list[AppliedMovementMeasurement] = []
    for index, applied_event in enumerate(events):
        if not isinstance(applied_event, AppliedEvent):
            raise TypeError(
                f"events[{index}] must be an AppliedEvent; received "
                f"{applied_event!r}."
            )
        if isinstance(applied_event.event, Movement.Event):
            measurements.append(measure_applied_movement(applied_event))

    count = len(measurements)
    total_realized_distance = sum(
        measurement.realized_distance for measurement in measurements
    )
    return LocomotionReplicateMeasurements(
        provenance=provenance,
        applied_movement_count=count,
        total_attempted_distance=sum(
            measurement.attempted_distance for measurement in measurements
        ),
        total_realized_distance=total_realized_distance,
        mean_realized_distance_per_applied_movement=(
            total_realized_distance / count if count else None
        ),
        total_locomotion_energy_expenditure=sum(
            measurement.locomotion_energy_expenditure
            for measurement in measurements
        ),
    )


def _validate_nonnegative_finite_float(value: object, *, name: str) -> float:
    validated = validators.validate_float(value, name=name)
    if not math.isfinite(validated) or validated < 0.0:
        raise ValueError(f"{name} must be finite and nonnegative; received {value!r}.")
    return validated
