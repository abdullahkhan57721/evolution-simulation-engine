"""Environment-aware trait-development models."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Generic, TypeVar

import attrs

from evo_engine.development.context import DevelopmentLocation
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState

ChoiceT = TypeVar("ChoiceT")


def _validate_nonblank_name(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


def _validate_finite_number(value: object, *, name: str) -> int | float:
    validated = validators.validate_number(value, name=name)
    if not math.isfinite(validated):
        raise ValueError(f"{name} must be finite.")
    return validated


def _round_half_away_from_zero(value: float) -> int:
    magnitude = math.floor(abs(value) + 0.5)
    return magnitude if value >= 0 else -magnitude


def _clamp_integer(
    value: int,
    *,
    minimum: int | None,
    maximum: int | None,
) -> int:
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _local_environmental_value(
    field_name: str,
    *,
    simulation_state: SimulationState | None,
    location: DevelopmentLocation | None,
) -> int | float:
    if simulation_state is None:
        raise ValueError(
            "simulation_state is required for environment-aware development."
        )
    if location is None:
        raise ValueError("location is required for environment-aware development.")

    return simulation_state.world.environmental_value(
        field_name,
        x=location.x,
        y=location.y,
    )


@attrs.frozen(slots=True, kw_only=True)
class LinearEnvironmentalDevelopment:
    """Add a linear environmental offset to an integer genetic target.

    This is phenotypic plasticity without genotype-dependent sensitivity:

    ``P = G + slope * (E - E_ref)``.

    Attributes:
        environmental_field_name: Spatial environmental field read at the
            developmental location.
        reference_environment: Environmental value at which phenotype equals
            the genetically expressed value.
        slope: Trait-value change per environmental unit.
        minimum: Optional inclusive lower bound on the realized integer target.
        maximum: Optional inclusive upper bound on the realized integer target.
    """

    environmental_field_name: str
    reference_environment: int | float
    slope: int | float
    minimum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )
    maximum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )

    def __attrs_post_init__(self) -> None:
        """Validate reaction-norm configuration."""
        _validate_nonblank_name(
            self.environmental_field_name,
            name="environmental_field_name",
        )
        _validate_finite_number(
            self.reference_environment,
            name="reference_environment",
        )
        _validate_finite_number(self.slope, name="slope")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must be less than or equal to maximum.")

    def develop(
        self,
        value: int,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
        location: DevelopmentLocation | None = None,
    ) -> int:
        """Return the environmentally shifted developmental target.

        Args:
            value: Genetically expressed integer target at the reference
                environment.
            rng: Simulation random-number generator; unused by this
                deterministic model.
            simulation_state: Current simulation state containing the field.
            location: Coordinate at which the environment is sampled.

        Returns:
            Environmentally realized integer target.
        """
        genetic_value = validators.validate_int(value, name="value")
        environment = _local_environmental_value(
            self.environmental_field_name,
            simulation_state=simulation_state,
            location=location,
        )
        realized = genetic_value + self.slope * (
            environment - self.reference_environment
        )
        return _clamp_integer(
            _round_half_away_from_zero(realized),
            minimum=self.minimum,
            maximum=self.maximum,
        )


@attrs.frozen(slots=True, kw_only=True)
class GenotypeScaledEnvironmentalDevelopment:
    """Realize a linear genotype-by-environment reaction norm.

    The genetically expressed integer value is the phenotype at the reference
    environment and also scales environmental sensitivity:

    ``P = G * (1 + sensitivity * (E - E_ref))``.

    Different genetic values therefore have different reaction-norm slopes,
    making the environmental effect genotype dependent rather than merely
    additive.

    Attributes:
        environmental_field_name: Spatial environmental field read at the
            developmental location.
        reference_environment: Environmental value at which phenotype equals
            the genetically expressed value.
        sensitivity: Fractional change in the genetic target per environmental
            unit.
        minimum: Optional inclusive lower bound on the realized integer target.
        maximum: Optional inclusive upper bound on the realized integer target.
    """

    environmental_field_name: str
    reference_environment: int | float
    sensitivity: int | float
    minimum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )
    maximum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )

    def __attrs_post_init__(self) -> None:
        """Validate GxE reaction-norm configuration."""
        _validate_nonblank_name(
            self.environmental_field_name,
            name="environmental_field_name",
        )
        _validate_finite_number(
            self.reference_environment,
            name="reference_environment",
        )
        _validate_finite_number(self.sensitivity, name="sensitivity")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must be less than or equal to maximum.")

    def develop(
        self,
        value: int,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
        location: DevelopmentLocation | None = None,
    ) -> int:
        """Return a genotype-dependent environmental realization.

        Args:
            value: Genetically expressed integer target at the reference
                environment.
            rng: Simulation random-number generator; unused by this
                deterministic model.
            simulation_state: Current simulation state containing the field.
            location: Coordinate at which the environment is sampled.

        Returns:
            Realized integer target after genotype-dependent environmental
            scaling.
        """
        genetic_value = validators.validate_int(value, name="value")
        environment = _local_environmental_value(
            self.environmental_field_name,
            simulation_state=simulation_state,
            location=location,
        )
        realized = genetic_value * (
            1 + self.sensitivity * (environment - self.reference_environment)
        )
        return _clamp_integer(
            _round_half_away_from_zero(realized),
            minimum=self.minimum,
            maximum=self.maximum,
        )


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentalThresholdDevelopment(Generic[ChoiceT]):
    """Choose a developmental target from a local environmental threshold.

    The genetically expressed input value is deliberately ignored. This models
    environmentally determined categorical outcomes while still preserving the
    genetic phenotype's trait identity in the developmental profile.

    Attributes:
        environmental_field_name: Spatial environmental field read at the
            developmental location.
        threshold: Inclusive threshold separating the two outcomes.
        below_value: Target produced when the local value is below threshold.
        at_or_above_value: Target produced at or above threshold.
    """

    environmental_field_name: str
    threshold: int | float
    below_value: ChoiceT
    at_or_above_value: ChoiceT

    def __attrs_post_init__(self) -> None:
        """Validate environmental-threshold configuration."""
        _validate_nonblank_name(
            self.environmental_field_name,
            name="environmental_field_name",
        )
        _validate_finite_number(self.threshold, name="threshold")

    def develop(
        self,
        value: ChoiceT,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
        location: DevelopmentLocation | None = None,
    ) -> ChoiceT:
        """Return the categorical outcome selected by local environment.

        Args:
            value: Genetically expressed value; ignored by this model.
            rng: Simulation random-number generator; unused by this
                deterministic model.
            simulation_state: Current simulation state containing the field.
            location: Coordinate at which the environment is sampled.

        Returns:
            Configured below-threshold or at/above-threshold value.
        """
        environment = _local_environmental_value(
            self.environmental_field_name,
            simulation_state=simulation_state,
            location=location,
        )
        if environment < self.threshold:
            return self.below_value
        return self.at_or_above_value
