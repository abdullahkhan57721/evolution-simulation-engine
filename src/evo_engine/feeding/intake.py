"""Models that determine organism resource-intake capacity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.characteristics import (
    DevelopmentalProfileCharacteristics,
    integer_characteristic,
)
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
class CharacteristicIntakeCapacity:
    """Read intake capacity from a configurable operative characteristic source.

    Attributes:
        characteristic_name: Characteristic storing maximum intake rate.
        source: Object providing ``value_for``. Defaults to realized
            developmental characteristics.
    """

    characteristic_name: str = MAX_INTAKE_RATE
    source: object = attrs.field(factory=DevelopmentalProfileCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate characteristic name and source contract."""
        validators.validate_str(self.characteristic_name, name="characteristic_name")
        if not self.characteristic_name.strip():
            raise ValueError("characteristic_name must not be blank.")
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return the operative characteristic required for intake capacity."""
        return frozenset({self.characteristic_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the biological trait backing the required characteristic."""
        return self.required_characteristics

    def determine_capacity(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's nonnegative operative intake capacity.

        Args:
            organism: Organism considering resource consumption.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative maximum resource intake.
        """
        return integer_characteristic(
            self.source,
            organism,
            self.characteristic_name,
            context=simulation_state,
            minimum=0,
        )


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
