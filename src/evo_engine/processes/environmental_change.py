"""Environmental change simulation process."""

from __future__ import annotations

import math

import attrs

from evo_engine.ecology import EnvironmentalForcingModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators, validators


def _validate_field_name(value: object) -> str:
    validated = validators.validate_str(value, name="field_name")
    if not validated.strip():
        raise ValueError("field_name must not be empty or whitespace-only.")
    return validated


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentalChange:
    """Apply deterministic time-dependent forcing to an environmental field.

    ``coordinates=None`` applies the forcing to every cell in the world.
    Explicit coordinates restrict it to a spatial patch. Environmental changes
    use ``WorldState.set_environmental_value`` so effective changes enter the
    normal transaction-local mutation journal and event telemetry.

    Attributes:
        field_name: Environmental field modified by this process.
        forcing: Time-dependent model producing target values.
        coordinates: Optional explicit coordinates affected by the forcing.
    """

    field_name: str
    forcing: EnvironmentalForcingModel
    coordinates: tuple[tuple[int, int], ...] | None = None

    def __attrs_post_init__(self) -> None:
        """Validate environmental forcing configuration."""
        _validate_field_name(self.field_name)
        if not callable(getattr(self.forcing, "value_at", None)):
            raise TypeError("forcing must provide a callable value_at method.")
        if self.coordinates is None:
            return

        validators.validate_tuple(self.coordinates, name="coordinates")
        seen: set[tuple[int, int]] = set()
        for index, coordinate in enumerate(self.coordinates):
            if type(coordinate) is not tuple:
                raise TypeError(f"coordinates[{index}] must be a tuple.")
            if len(coordinate) != 2:
                raise ValueError(
                    f"coordinates[{index}] must contain exactly two items."
                )
            x, y = coordinate
            validators.validate_int_ge(x, bound=0, name=f"coordinates[{index}][0]")
            validators.validate_int_ge(y, bound=0, name=f"coordinates[{index}][1]")
            if coordinate in seen:
                raise ValueError("coordinates must not contain duplicates.")
            seen.add(coordinate)

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent one environmental forcing update.

        Attributes:
            step_index: Simulation step associated with the update.
            field_name: Environmental field being changed.
            value: Finite scalar target value.
            coordinates: Coordinates to which the target will be applied.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        field_name: str
        value: int | float
        coordinates: tuple[tuple[int, int], ...]

        def __attrs_post_init__(self) -> None:
            """Validate materialized environmental forcing data."""
            _validate_field_name(self.field_name)
            validated_value = validators.validate_number(self.value, name="value")
            if not math.isfinite(validated_value):
                raise ValueError("value must be finite.")
            validators.validate_tuple(self.coordinates, name="coordinates")

    @property
    def event_type(self) -> type[EnvironmentalChange.Event]:
        """Return the environmental-change event type."""
        return self.Event

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[EnvironmentalChange.Event]:
        """Propose the configured environmental update for the current step."""
        value = self.forcing.value_at(simulation_state.step_index)
        if value is None:
            return []

        validated_value = validators.validate_number(value, name="forcing value")
        if not math.isfinite(validated_value):
            raise ValueError("forcing value must be finite.")

        world = simulation_state.world
        world.environmental_value(self.field_name, x=0, y=0)
        coordinates = self.coordinates
        if coordinates is None:
            coordinates = tuple(
                (x, y)
                for y in range(world.height)
                for x in range(world.width)
            )
        else:
            for x, y in coordinates:
                world.environmental_value(self.field_name, x=x, y=y)

        return [
            self.Event(
                step_index=simulation_state.step_index,
                field_name=self.field_name,
                value=validated_value,
                coordinates=coordinates,
            )
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: EnvironmentalChange.Event,
    ) -> None:
        """Apply a resolved environmental forcing update mechanically."""
        for x, y in resolved_event.coordinates:
            simulation_state.world.set_environmental_value(
                resolved_event.field_name,
                x=x,
                y=y,
                value=resolved_event.value,
            )
