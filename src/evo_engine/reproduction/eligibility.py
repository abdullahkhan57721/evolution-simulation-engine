"""Individual eligibility policies for reproduction."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.organism import Organism


class ReproductiveEligibility(Protocol):
    """Define whether an organism is individually eligible to reproduce."""

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism is individually eligible to reproduce.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether the organism is individually eligible to reproduce.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AlwaysEligible:
    """Consider every organism individually eligible for reproduction."""

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return True for every organism.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            True.
        """
        return True


@attrs.frozen(slots=True, kw_only=True)
class MinimumEnergyEligibility:
    """Require a minimum current energy for reproductive eligibility.

    Attributes:
        minimum_energy: Minimum energy required to be individually eligible.
    """

    minimum_energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism meets the minimum-energy requirement.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether the organism has at least the configured minimum energy.
        """
        return organism.energy >= self.minimum_energy
