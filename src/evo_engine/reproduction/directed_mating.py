"""Directed mate-choice policies for explicitly role-ordered parent pairs."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import validate_required_traits
from evo_engine.validation import validators
from evo_engine.world.organism import Organism


def _validate_trait_name(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


@attrs.frozen(slots=True, kw_only=True)
class ChooserSignalCompatibility:
    """Require the second parent's signal to meet the first parent's threshold.

    This policy is intentionally directional. It should be paired with a parent
    selector whose tuple order has explicit role semantics, such as
    ``DirectedPairwiseMating``.

    Attributes:
        chooser_threshold_trait: Integer trait read from the first parent.
        signal_trait: Integer signal trait read from the second parent.
    """

    chooser_threshold_trait: str
    signal_trait: str

    def __attrs_post_init__(self) -> None:
        """Validate directed mate-choice trait names."""
        _validate_trait_name(
            self.chooser_threshold_trait,
            name="chooser_threshold_trait",
        )
        _validate_trait_name(self.signal_trait, name="signal_trait")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the two genetic phenotype traits read by this policy."""
        return validate_required_traits(
            frozenset((self.chooser_threshold_trait, self.signal_trait))
        )

    def __call__(
        self,
        chooser: Organism,
        signaler: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the signaler meets the chooser's acceptance threshold."""
        threshold = chooser.genetic_phenotype.int_value(self.chooser_threshold_trait)
        signal = signaler.genetic_phenotype.int_value(self.signal_trait)
        return signal >= threshold


@attrs.frozen(slots=True, kw_only=True)
class ChooserSignalMarginPreference:
    """Score a directed pairing by signal margin above chooser threshold.

    Attributes:
        chooser_threshold_trait: Integer threshold trait on the first parent.
        signal_trait: Integer signal trait on the second parent.
    """

    chooser_threshold_trait: str
    signal_trait: str

    def __attrs_post_init__(self) -> None:
        """Validate directed preference trait names."""
        _validate_trait_name(
            self.chooser_threshold_trait,
            name="chooser_threshold_trait",
        )
        _validate_trait_name(self.signal_trait, name="signal_trait")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the two genetic phenotype traits read by this policy."""
        return validate_required_traits(
            frozenset((self.chooser_threshold_trait, self.signal_trait))
        )

    def __call__(
        self,
        chooser: Organism,
        signaler: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return signal minus chooser threshold as a directed preference score."""
        threshold = chooser.genetic_phenotype.int_value(self.chooser_threshold_trait)
        signal = signaler.genetic_phenotype.int_value(self.signal_trait)
        return signal - threshold
