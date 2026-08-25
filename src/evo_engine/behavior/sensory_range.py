"""Models that determine how far organisms can detect spatial targets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.characteristics import (
    DevelopmentalProfileCharacteristics,
    integer_characteristic,
)
from evo_engine.genetics.builtin_traits import SENSORY_RANGE
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class SensoryRangeModel(Protocol):
    """Determine the spatial detection radius available to an organism."""

    def determine_range(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's nonnegative sensory radius.

        Args:
            organism: Organism attempting to detect a spatial target.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative sensory radius in grid-distance units.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedSensoryRange:
    """Give every organism the same fixed sensory radius.

    Attributes:
        radius: Nonnegative detection radius.
    """

    radius: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_range(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured fixed sensory radius.

        Args:
            organism: Organism attempting to detect a spatial target.
            simulation_state: Current simulation state.

        Returns:
            Configured sensory radius.
        """
        return self.radius


@attrs.frozen(slots=True, kw_only=True)
class CharacteristicSensoryRange:
    """Read sensory radius from a configurable operative characteristic source.

    Attributes:
        characteristic_name: Operative characteristic storing sensory range.
        source: Object providing ``value_for``. Defaults to realized
            developmental characteristics.
    """

    characteristic_name: str = SENSORY_RANGE
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
        """Return the operative characteristic required for sensory range."""
        return frozenset({self.characteristic_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the biological trait backing the required characteristic."""
        return self.required_characteristics

    def determine_range(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's nonnegative operative sensory radius.

        Args:
            organism: Organism attempting to detect a spatial target.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative sensory radius.
        """
        return integer_characteristic(
            self.source,
            organism,
            self.characteristic_name,
            context=simulation_state,
            minimum=0,
        )


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeSensoryRange:
    """Use an integer genetic phenotype trait as sensory radius.

    Attributes:
        trait_name: Genetic phenotype trait that stores sensory range.
    """

    trait_name: str = SENSORY_RANGE

    def __attrs_post_init__(self) -> None:
        """Validate the configured sensory-range trait name."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the genetic phenotype trait required for sensory range."""
        return frozenset({self.trait_name})

    def determine_range(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's genetically expressed sensory radius.

        Args:
            organism: Organism attempting to detect a spatial target.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative genetically expressed sensory radius.

        Raises:
            ValueError: If the expressed sensory range is negative.
        """
        sensory_range = organism.genetic_phenotype.int_value(self.trait_name)
        validators.validate_int_ge(
            sensory_range,
            bound=0,
            name=self.trait_name,
        )
        return sensory_range


def determine_sensory_range(
    sensory_range_model: SensoryRangeModel,
    organism: Organism,
    *,
    simulation_state: SimulationState,
) -> int:
    """Return a validated sensory radius from a sensory-range model.

    Args:
        sensory_range_model: Model determining spatial detection radius.
        organism: Organism attempting to detect a spatial target.
        simulation_state: Current simulation state.

    Returns:
        Validated nonnegative sensory radius.

    Raises:
        TypeError: If the model returns a non-integer value.
        ValueError: If the model returns a negative value.
    """
    sensory_range = sensory_range_model.determine_range(
        organism,
        simulation_state=simulation_state,
    )
    validators.validate_int_ge(
        sensory_range,
        bound=0,
        name="sensory_range_model.determine_range return value",
    )
    return sensory_range
