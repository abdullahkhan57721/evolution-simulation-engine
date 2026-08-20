"""Parental energy-investment policies for reproduction."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import OFFSPRING_ENERGY
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class ParentalInvestment(Protocol):
    """Define how much energy each reproductive parent invests."""

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return one energy investment for each parent.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class PhenotypeEnergyInvestment:
    """Use an integer phenotype trait as each parent's energy investment.

    Attributes:
        trait_name: Name of the phenotype trait specifying parental energy
            investment.
    """

    trait_name: str = OFFSPRING_ENERGY

    def __attrs_post_init__(self) -> None:
        """Validate the phenotype trait name."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the phenotype trait used for parental investment."""
        return frozenset({self.trait_name})

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return each parent's expressed trait value as its investment.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.

        Raises:
            ValueError: If a configured phenotype value is negative.
        """
        investments = tuple(
            parent.phenotype.int_value(self.trait_name) for parent in parents
        )

        for investment in investments:
            if investment < 0:
                raise ValueError(
                    f"phenotype trait {self.trait_name!r} must be "
                    "non-negative for parental investment."
                )

        return investments


@attrs.frozen(slots=True, kw_only=True)
class FixedEnergyInvestment:
    """Make every parent invest the same fixed amount of energy.

    Attributes:
        amount: Energy invested by each parent.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return the configured fixed investment for each parent.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.
        """
        return tuple(self.amount for _ in parents)
