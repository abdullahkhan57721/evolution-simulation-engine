"""Basal metabolic energy-cost models."""

from __future__ import annotations

import math
from typing import Protocol

import attrs

from evo_engine.energetics._common import (
    round_nonnegative_cost,
    validate_finite_number,
)
from evo_engine.energetics.coefficients import (
    CoefficientSource,
    coefficient_required_traits,
    determine_coefficient,
    validate_coefficient_source,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.organism import Organism


class MetabolicCostModel(Protocol):
    """Define how basal metabolic energy expenditure is calculated."""

    def calculate_cost(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's metabolic energy cost for one timestep.

        Args:
            organism: Organism whose metabolic cost is being calculated.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy cost.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedMetabolicCost:
    """Charge every organism the same basal metabolic cost.

    Attributes:
        amount: Energy charged per organism per timestep.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def calculate_cost(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured fixed metabolic cost.

        Args:
            organism: Organism whose cost is being calculated.
            simulation_state: Current simulation state.

        Returns:
            Configured nonnegative energy cost.
        """
        return self.amount


@attrs.frozen(slots=True, kw_only=True)
class PowerLawMetabolicCost:
    """Scale basal metabolic cost as a power of current body mass.

    The model evaluates ``coefficient * body_mass**mass_exponent`` and rounds
    the result to integer energy units. ``coefficient`` may be a fixed number
    or an organism-specific coefficient model. The exponent remains model
    configuration; for example, an allometric model can use ``0.75`` without
    hard-coding that relationship into Metabolism or organism genetics.

    Attributes:
        coefficient: Fixed or organism-specific nonnegative coefficient.
        mass_exponent: Finite power applied to current body mass.
        minimum_cost: Minimum integer cost after rounding.
    """

    coefficient: CoefficientSource
    mass_exponent: int | float
    minimum_cost: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate power-law configuration."""
        validate_coefficient_source(
            self.coefficient,
            name="coefficient",
        )
        validate_finite_number(
            self.mass_exponent,
            name="mass_exponent",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured coefficient source."""
        return coefficient_required_traits(self.coefficient)

    def calculate_cost(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return a power-law basal metabolic cost.

        Args:
            organism: Organism whose cost is being calculated.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative integer energy cost.
        """
        coefficient = determine_coefficient(
            self.coefficient,
            organism,
            simulation_state=simulation_state,
            name="metabolic coefficient",
        )
        raw_cost = coefficient * math.pow(
            organism.body_mass,
            self.mass_exponent,
        )

        return round_nonnegative_cost(
            raw_cost,
            minimum_cost=self.minimum_cost,
        )
