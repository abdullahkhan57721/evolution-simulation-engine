"""Energy-cost models for organism growth."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.energetics._common import (
    round_nonnegative_cost,
    validate_finite_number,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class GrowthCostModel(Protocol):
    """Define how growth is converted into an energy cost."""

    def calculate_cost(
        self,
        organism: Organism,
        *,
        body_mass_gain: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the energy cost of a proposed body-mass gain.

        Args:
            organism: Organism paying the growth cost.
            body_mass_gain: Body-mass units that would actually be gained.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy cost.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class LinearGrowthCost:
    """Charge energy linearly with body-mass gain.

    The raw cost is ``energy_per_body_mass_unit * body_mass_gain`` and uses the
    shared half-up energetic rounding convention. A configured minimum applies
    only when body-mass gain is nonzero; zero growth always costs zero.

    Attributes:
        energy_per_body_mass_unit: Nonnegative energy cost per body-mass unit.
        minimum_nonzero_cost: Minimum cost for a positive body-mass gain.
    """

    energy_per_body_mass_unit: int | float
    minimum_nonzero_cost: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate linear growth-cost configuration."""
        coefficient = validate_finite_number(
            self.energy_per_body_mass_unit,
            name="energy_per_body_mass_unit",
        )

        if coefficient < 0:
            raise ValueError(
                "energy_per_body_mass_unit must be nonnegative; "
                f"received {coefficient!r}."
            )

    def calculate_cost(
        self,
        organism: Organism,
        *,
        body_mass_gain: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the linear energetic cost of body-mass gain.

        Args:
            organism: Organism paying the growth cost.
            body_mass_gain: Body-mass units that would actually be gained.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative integer energy cost.

        Raises:
            TypeError: If body_mass_gain is not an integer.
            ValueError: If body_mass_gain is negative.
        """
        validated_gain = validators.validate_int_ge(
            body_mass_gain,
            bound=0,
            name="body_mass_gain",
        )

        if validated_gain == 0:
            return 0

        raw_cost = self.energy_per_body_mass_unit * validated_gain

        return round_nonnegative_cost(
            raw_cost,
            minimum_cost=self.minimum_nonzero_cost,
        )
