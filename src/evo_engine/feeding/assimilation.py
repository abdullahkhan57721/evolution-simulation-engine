"""Models that convert consumed resources into organism energy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.characteristics import (
    DevelopmentalProfileCharacteristics,
    integer_characteristic,
)
from evo_engine.genetics.builtin_traits import ASSIMILATION_EFFICIENCY
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class AssimilationModel(Protocol):
    """Determine usable energy gained from consumed environmental resources."""

    def determine_energy_gain(
        self,
        organism: Organism,
        *,
        consumed_amount: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return nonnegative energy gained from consumed resource units.

        Args:
            organism: Organism consuming the resources.
            consumed_amount: Resource units actually allocated and consumed.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy gain.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FullAssimilation:
    """Convert each consumed resource unit into one energy unit."""

    def determine_energy_gain(
        self,
        organism: Organism,
        *,
        consumed_amount: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return the consumed amount unchanged as energy gain.

        Args:
            organism: Organism consuming the resources.
            consumed_amount: Resource units actually consumed.
            simulation_state: Current simulation state.

        Returns:
            Energy gain equal to consumed resource units.
        """
        return validators.validate_int_ge(
            consumed_amount,
            bound=0,
            name="consumed_amount",
        )


@attrs.frozen(slots=True, kw_only=True)
class FixedAssimilationEfficiency:
    """Convert consumed resources using one fixed percentage efficiency.

    Integer energy uses half-up rounding. For example, three consumed resource
    units at 50% efficiency yield two energy units.

    Attributes:
        efficiency_percent: Percentage of consumed resources converted to
            usable energy, from 0 through 100 inclusive.
    """

    efficiency_percent: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(0, 100),
    )

    def determine_energy_gain(
        self,
        organism: Organism,
        *,
        consumed_amount: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return percentage-assimilated energy from consumed resources.

        Args:
            organism: Organism consuming the resources.
            consumed_amount: Resource units actually consumed.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative energy gain.
        """
        return _percentage_energy_gain(
            consumed_amount,
            efficiency_percent=self.efficiency_percent,
        )


@attrs.frozen(slots=True, kw_only=True)
class CharacteristicAssimilationEfficiency:
    """Read assimilation efficiency from an operative characteristic source.

    Attributes:
        characteristic_name: Characteristic storing an efficiency percentage.
        source: Object providing ``value_for``. Defaults to realized
            developmental characteristics.
    """

    characteristic_name: str = ASSIMILATION_EFFICIENCY
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
        """Return the operative characteristic required for assimilation."""
        return frozenset({self.characteristic_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the biological trait backing the required characteristic."""
        return self.required_characteristics

    def determine_energy_gain(
        self,
        organism: Organism,
        *,
        consumed_amount: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return energy gained using the operative assimilation efficiency.

        Args:
            organism: Organism consuming the resources.
            consumed_amount: Resource units actually consumed.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative energy gain.
        """
        efficiency_percent = integer_characteristic(
            self.source,
            organism,
            self.characteristic_name,
            context=simulation_state,
            minimum=0,
            maximum=100,
        )
        return _percentage_energy_gain(
            consumed_amount,
            efficiency_percent=efficiency_percent,
        )


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeAssimilationEfficiency:
    """Read assimilation efficiency from an integer genetic phenotype trait.

    Attributes:
        trait_name: Genetic phenotype trait storing efficiency as an integer
            percentage from 0 through 100 inclusive.
    """

    trait_name: str = ASSIMILATION_EFFICIENCY

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
        """Return the genetic phenotype trait used for assimilation efficiency."""
        return frozenset({self.trait_name})

    def determine_energy_gain(
        self,
        organism: Organism,
        *,
        consumed_amount: int,
        simulation_state: SimulationState,
    ) -> int:
        """Return energy gained using the organism's expressed efficiency.

        Args:
            organism: Organism consuming the resources.
            consumed_amount: Resource units actually consumed.
            simulation_state: Current simulation state.

        Returns:
            Rounded nonnegative energy gain.

        Raises:
            TypeError: If the expressed efficiency is not an integer.
            ValueError: If the expressed efficiency is outside 0 through 100.
        """
        efficiency_percent = organism.genetic_phenotype.int_value(self.trait_name)
        validators.validate_int_in_range(
            efficiency_percent,
            lower=0,
            upper=100,
            name=f"genetic_phenotype[{self.trait_name!r}]",
        )

        return _percentage_energy_gain(
            consumed_amount,
            efficiency_percent=efficiency_percent,
        )


def determine_assimilated_energy(
    assimilation_model: AssimilationModel,
    organism: Organism,
    *,
    consumed_amount: int,
    simulation_state: SimulationState,
) -> int:
    """Return validated energy gain from a configured assimilation model.

    Args:
        assimilation_model: Model converting consumed resources into energy.
        organism: Organism consuming the resources.
        consumed_amount: Resource units actually consumed.
        simulation_state: Current simulation state.

    Returns:
        Validated nonnegative integer energy gain.

    Raises:
        TypeError: If consumed amount or model output is not an integer.
        ValueError: If consumed amount or model output is negative.
    """
    validated_consumed_amount = validators.validate_int_ge(
        consumed_amount,
        bound=0,
        name="consumed_amount",
    )
    energy_gain = assimilation_model.determine_energy_gain(
        organism,
        consumed_amount=validated_consumed_amount,
        simulation_state=simulation_state,
    )

    return validators.validate_int_ge(
        energy_gain,
        bound=0,
        name="assimilated energy gain",
    )


def _percentage_energy_gain(
    consumed_amount: int,
    *,
    efficiency_percent: int,
) -> int:
    consumed_amount = validators.validate_int_ge(
        consumed_amount,
        bound=0,
        name="consumed_amount",
    )
    validators.validate_int_in_range(
        efficiency_percent,
        lower=0,
        upper=100,
        name="efficiency_percent",
    )

    return (consumed_amount * efficiency_percent + 50) // 100
