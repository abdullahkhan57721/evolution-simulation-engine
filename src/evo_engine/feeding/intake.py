"""Models that determine organism resource-intake capacity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.genetics.builtin_traits import MAX_INTAKE_RATE
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class IntakeCapacityModel(Protocol):
    """Determine the maximum resource amount an organism can consume per step."""

    def determine_capacity(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's nonnegative resource-intake capacity.

        Args:
            organism: Organism considering resource consumption.
            simulation_state: Current simulation state.

        Returns:
            Maximum resource units the organism can consume this timestep.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedIntakeCapacity:
    """Give every organism the same resource-intake capacity.

    Attributes:
        amount: Maximum resource units consumable per timestep.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_capacity(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured intake capacity.

        Args:
            organism: Organism considering resource consumption.
            simulation_state: Current simulation state.

        Returns:
            Configured nonnegative capacity.
        """
        return self.amount


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeIntakeCapacity:
    """Read resource-intake capacity from an integer genetic phenotype trait.

    Attributes:
        trait_name: Genetic phenotype trait storing maximum intake rate.
    """

    trait_name: str = MAX_INTAKE_RATE

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the genetic phenotype trait used for intake capacity."""
        return frozenset({self.trait_name})

    def determine_capacity(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's genetically expressed intake capacity.

        Args:
            organism: Organism considering resource consumption.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative maximum resource intake.

        Raises:
            TypeError: If the expressed trait is not an integer.
            ValueError: If the expressed trait is negative.
        """
        return validators.validate_int_ge(
            organism.genetic_phenotype.int_value(self.trait_name),
            bound=0,
            name=f"genetic_phenotype[{self.trait_name!r}]",
        )


def determine_intake_capacity(
    intake_capacity_model: IntakeCapacityModel,
    organism: Organism,
    *,
    simulation_state: SimulationState,
) -> int:
    """Return a validated resource-intake capacity from a configured model.

    Args:
        intake_capacity_model: Model determining resource-intake capacity.
        organism: Organism considering resource consumption.
        simulation_state: Current simulation state.

    Returns:
        Validated nonnegative integer capacity.

    Raises:
        TypeError: If the model returns a non-integer capacity.
        ValueError: If the model returns a negative capacity.
    """
    capacity = intake_capacity_model.determine_capacity(
        organism,
        simulation_state=simulation_state,
    )

    return validators.validate_int_ge(
        capacity,
        bound=0,
        name="intake capacity",
    )
