"""Locomotion energy-cost models."""

from __future__ import annotations

import math
from typing import Protocol

import attrs

from evo_engine.energetics._common import (
    round_nonnegative_cost,
    validate_finite_number,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class LocomotionCostModel(Protocol):
    """Define how an attempted movement displacement consumes energy."""

    def calculate_cost(
        self,
        organism: Organism,
        *,
        dx: int,
        dy: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the locomotion cost of an attempted displacement.

        Args:
            organism: Organism attempting to move.
            dx: Attempted horizontal displacement.
            dy: Attempted vertical displacement.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy cost.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedLocomotionCost:
    """Charge a fixed energy amount whenever displacement is nonzero.

    Attributes:
        amount: Energy charged for a nonzero attempted displacement.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def calculate_cost(
        self,
        organism: Organism,
        *,
        dx: int,
        dy: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return zero when stationary and the configured amount otherwise.

        Args:
            organism: Organism attempting to move.
            dx: Attempted horizontal displacement.
            dy: Attempted vertical displacement.
            simulation_state: Current simulation state.

        Returns:
            Locomotion energy cost.
        """
        if dx == 0 and dy == 0:
            return 0

        return self.amount


@attrs.frozen(slots=True, kw_only=True)
class PowerLawLocomotionCost:
    """Scale locomotion cost with current body mass and displacement distance.

    The model evaluates
    ``coefficient * body_mass**mass_exponent * distance**distance_exponent``
    using Euclidean displacement distance and rounds the result to integer
    energy units. All exponents are configuration, allowing the same model
    class to represent many locomotion scaling assumptions.

    Attributes:
        coefficient: Nonnegative multiplicative coefficient.
        mass_exponent: Finite power applied to current body mass.
        distance_exponent: Finite power applied to Euclidean distance.
        minimum_nonzero_cost: Minimum cost for a nonzero displacement.
    """

    coefficient: int | float
    mass_exponent: int | float
    distance_exponent: int | float
    minimum_nonzero_cost: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate power-law configuration."""
        coefficient = validate_finite_number(
            self.coefficient,
            name="coefficient",
        )
        validate_finite_number(
            self.mass_exponent,
            name="mass_exponent",
        )
        validate_finite_number(
            self.distance_exponent,
            name="distance_exponent",
        )

        if coefficient < 0:
            raise ValueError(
                f"coefficient must be nonnegative; received {coefficient!r}."
            )

    def calculate_cost(
        self,
        organism: Organism,
        *,
        dx: int,
        dy: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return a power-law locomotion energy cost.

        A zero displacement always costs zero regardless of the configured
        minimum. This preserves the distinction between basal metabolism and
        locomotion expenditure.

        Args:
            organism: Organism attempting to move.
            dx: Attempted horizontal displacement.
            dy: Attempted vertical displacement.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative integer energy cost.

        Raises:
            TypeError: If dx or dy is not an integer.
        """
        validators.validate_int(
            dx,
            name="dx",
        )
        validators.validate_int(
            dy,
            name="dy",
        )

        if dx == 0 and dy == 0:
            return 0

        distance = math.hypot(
            dx,
            dy,
        )
        raw_cost = (
            self.coefficient
            * math.pow(organism.body_mass, self.mass_exponent)
            * math.pow(distance, self.distance_exponent)
        )

        return round_nonnegative_cost(
            raw_cost,
            minimum_cost=self.minimum_nonzero_cost,
        )
