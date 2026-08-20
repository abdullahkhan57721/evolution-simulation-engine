"""Models that determine potential organism growth."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.organism import Organism


class GrowthModel(Protocol):
    """Define how much body mass an organism can potentially gain."""

    def determine_body_mass_gain(
        self,
        organism: Organism,
        *,
        target_body_mass: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return potential body-mass gain for one timestep.

        Args:
            organism: Organism whose potential growth is being determined.
            target_body_mass: Realized developmental body-mass target.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer potential body-mass gain.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedGrowthRate:
    """Provide the same potential body-mass gain each timestep.

    Attributes:
        amount_per_timestep: Potential body-mass units gained per timestep.
    """

    amount_per_timestep: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_body_mass_gain(
        self,
        organism: Organism,
        *,
        target_body_mass: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured fixed potential body-mass gain.

        Args:
            organism: Organism whose potential growth is being determined.
            target_body_mass: Realized developmental body-mass target.
            simulation_state: Current simulation state.

        Returns:
            Configured nonnegative body-mass gain.
        """
        return self.amount_per_timestep
