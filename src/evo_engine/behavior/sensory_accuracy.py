"""Models that determine organism sensory detection accuracy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.genetics.builtin_traits import SENSORY_ACCURACY
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class SensoryAccuracyModel(Protocol):
    """Determine the percentage probability of detecting an in-range stimulus."""

    def determine_accuracy_percent(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return sensory detection accuracy from 0 through 100 inclusive.

        Args:
            organism: Organism attempting to detect a stimulus.
            simulation_state: Current simulation state.

        Returns:
            Integer detection percentage from 0 through 100 inclusive.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedSensoryAccuracy:
    """Use one fixed sensory detection percentage for all organisms.

    Attributes:
        accuracy_percent: Detection probability from 0 through 100 inclusive.
    """

    accuracy_percent: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_in_range(0, 100),
    )

    def determine_accuracy_percent(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured sensory detection percentage.

        Args:
            organism: Organism attempting detection.
            simulation_state: Current simulation state.

        Returns:
            Configured detection percentage.
        """
        return self.accuracy_percent


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeSensoryAccuracy:
    """Read sensory accuracy from an integer genetic phenotype trait.

    Attributes:
        trait_name: Genetic phenotype trait storing accuracy as an integer
            percentage from 0 through 100 inclusive.
    """

    trait_name: str = SENSORY_ACCURACY

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
        """Return the genetic phenotype trait used for sensory accuracy."""
        return frozenset({self.trait_name})

    def determine_accuracy_percent(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's expressed sensory detection percentage.

        Args:
            organism: Organism attempting detection.
            simulation_state: Current simulation state.

        Returns:
            Validated detection percentage from 0 through 100 inclusive.

        Raises:
            TypeError: If the expressed trait is not an integer.
            ValueError: If the expressed trait is outside 0 through 100.
        """
        accuracy_percent = organism.genetic_phenotype.int_value(self.trait_name)
        validators.validate_int_in_range(
            accuracy_percent,
            lower=0,
            upper=100,
            name=f"genetic_phenotype[{self.trait_name!r}]",
        )
        return accuracy_percent


def determine_sensory_accuracy(
    sensory_accuracy_model: SensoryAccuracyModel,
    organism: Organism,
    *,
    simulation_state: SimulationState,
) -> int:
    """Return validated sensory accuracy from a configured model.

    Args:
        sensory_accuracy_model: Model determining detection accuracy.
        organism: Organism attempting detection.
        simulation_state: Current simulation state.

    Returns:
        Validated integer percentage from 0 through 100 inclusive.

    Raises:
        TypeError: If the model output is not an integer.
        ValueError: If the model output is outside 0 through 100.
    """
    accuracy_percent = sensory_accuracy_model.determine_accuracy_percent(
        organism,
        simulation_state=simulation_state,
    )
    validators.validate_int_in_range(
        accuracy_percent,
        lower=0,
        upper=100,
        name="sensory accuracy",
    )
    return accuracy_percent
