"""Models that determine potential organism growth."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import GROWTH_RATE
from evo_engine.validation import attrs_validators, validators
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


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeGrowthRate:
    """Use an expressed genetic trait as potential per-timestep growth.

    The process still caps realized gain at the organism's developmental adult
    body-mass target and applies its configured energetic affordability rules.
    This model only determines the potential mass increment before those later
    constraints are applied.

    Attributes:
        trait_name: Genetic phenotype trait storing nonnegative growth units per
            timestep.
    """

    trait_name: str = attrs.field(
        default=GROWTH_RATE,
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the genetic phenotype trait required by this model."""
        return frozenset({self.trait_name})

    def determine_body_mass_gain(
        self,
        organism: Organism,
        *,
        target_body_mass: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's expressed nonnegative growth rate.

        Args:
            organism: Organism whose potential growth is being determined.
            target_body_mass: Realized developmental body-mass target.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer potential body-mass gain.

        Raises:
            KeyError: If the configured trait is absent.
            TypeError: If the genetic phenotype value is not an integer.
            ValueError: If the genetic phenotype value is negative.
        """
        return validators.validate_int_ge(
            organism.genetic_phenotype.int_value(self.trait_name),
            bound=0,
            name=f"genetic_phenotype[{self.trait_name!r}]",
        )
