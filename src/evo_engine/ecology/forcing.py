"""Time-dependent environmental forcing models."""

from __future__ import annotations

import math
from typing import Protocol

import attrs

from evo_engine.validation import attrs_validators, validators


def _finite_number(value: object, *, name: str) -> int | float:
    validated = validators.validate_number(value, name=name)
    if not math.isfinite(validated):
        raise ValueError(f"{name} must be finite.")
    return validated


class EnvironmentalForcingModel(Protocol):
    """Define an environmental field value as a function of simulation time."""

    def value_at(self, step_index: int) -> int | float | None:
        """Return the target value for a step, or ``None`` for no change."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class LinearEnvironmentalForcing:
    """Change an environmental value linearly with simulation time.

    Attributes:
        initial_value: Value at step zero.
        change_per_step: Signed change applied per step index.
    """

    initial_value: int | float
    change_per_step: int | float

    def __attrs_post_init__(self) -> None:
        """Validate finite forcing parameters."""
        _finite_number(self.initial_value, name="initial_value")
        _finite_number(self.change_per_step, name="change_per_step")

    def value_at(self, step_index: int) -> int | float:
        """Return the linear target value at one step."""
        validated_step = validators.validate_int_ge(
            step_index,
            bound=0,
            name="step_index",
        )
        return self.initial_value + self.change_per_step * validated_step


@attrs.frozen(slots=True, kw_only=True)
class SinusoidalEnvironmentalForcing:
    """Oscillate an environmental value sinusoidally through time.

    Attributes:
        mean: Mean environmental value.
        amplitude: Nonnegative distance from mean to seasonal extreme.
        period_steps: Positive number of simulation steps per complete cycle.
        phase_steps: Horizontal phase offset measured in simulation steps.
    """

    mean: int | float
    amplitude: int | float
    period_steps: int = attrs.field(validator=attrs_validators.validate_int_ge(1))
    phase_steps: int | float = 0

    def __attrs_post_init__(self) -> None:
        """Validate sinusoidal forcing parameters."""
        _finite_number(self.mean, name="mean")
        amplitude = _finite_number(self.amplitude, name="amplitude")
        _finite_number(self.phase_steps, name="phase_steps")
        if amplitude < 0:
            raise ValueError("amplitude must be nonnegative.")

    def value_at(self, step_index: int) -> float:
        """Return the sinusoidal target value at one step."""
        validated_step = validators.validate_int_ge(
            step_index,
            bound=0,
            name="step_index",
        )
        angle = 2 * math.pi * (validated_step - self.phase_steps) / self.period_steps
        return self.mean + self.amplitude * math.sin(angle)


@attrs.frozen(slots=True, kw_only=True)
class ScheduledEnvironmentalForcing:
    """Apply explicit environmental changes at selected simulation steps.

    Unlisted steps return ``None`` and therefore do not change the field. This
    supports pulses, disturbances, regime changes, and manually specified
    environmental histories without requiring a special process for each case.

    Attributes:
        schedule: Strictly increasing ``(step_index, value)`` pairs.
    """

    schedule: tuple[tuple[int, int | float], ...]

    def __attrs_post_init__(self) -> None:
        """Validate the environmental schedule."""
        validators.validate_tuple(self.schedule, name="schedule")
        previous_step = -1
        for index, entry in enumerate(self.schedule):
            if type(entry) is not tuple:
                raise TypeError(f"schedule[{index}] must be a tuple.")
            if len(entry) != 2:
                raise ValueError(f"schedule[{index}] must contain exactly two items.")
            step_index, value = entry
            validated_step = validators.validate_int_ge(
                step_index,
                bound=0,
                name=f"schedule[{index}][0]",
            )
            _finite_number(value, name=f"schedule[{index}][1]")
            if validated_step <= previous_step:
                raise ValueError("schedule step indices must be strictly increasing.")
            previous_step = validated_step

    def value_at(self, step_index: int) -> int | float | None:
        """Return the scheduled target at one step, if any."""
        validated_step = validators.validate_int_ge(
            step_index,
            bound=0,
            name="step_index",
        )
        for scheduled_step, value in self.schedule:
            if scheduled_step == validated_step:
                return value
            if scheduled_step > validated_step:
                break
        return None
