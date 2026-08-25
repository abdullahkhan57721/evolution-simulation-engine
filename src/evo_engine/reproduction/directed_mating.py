"""Directed mate-choice policies for explicitly role-ordered parent pairs."""

from __future__ import annotations

import attrs

from evo_engine.characteristics import (
    GeneticPhenotypeCharacteristics,
    integer_characteristic,
)
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
        chooser_threshold_trait: Integer characteristic read from first parent.
        signal_trait: Integer signal characteristic read from second parent.
        source: Characteristic source used for both values. Defaults to raw
            genetic expression for backward compatibility.
    """

    chooser_threshold_trait: str
    signal_trait: str
    source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate directed mate-choice trait names and source."""
        _validate_trait_name(
            self.chooser_threshold_trait,
            name="chooser_threshold_trait",
        )
        _validate_trait_name(self.signal_trait, name="signal_trait")
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return operative characteristics required by this policy."""
        return frozenset((self.chooser_threshold_trait, self.signal_trait))

    @property
    def required_traits(self) -> frozenset[str]:
        """Return biological traits backing the required characteristics."""
        return validate_required_traits(self.required_characteristics)

    def __call__(
        self,
        chooser: Organism,
        signaler: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the signaler meets the chooser's acceptance threshold."""
        threshold = integer_characteristic(
            self.source,
            chooser,
            self.chooser_threshold_trait,
            context=simulation_state,
        )
        signal = integer_characteristic(
            self.source,
            signaler,
            self.signal_trait,
            context=simulation_state,
        )
        return signal >= threshold


@attrs.frozen(slots=True, kw_only=True)
class ChooserSignalMarginPreference:
    """Score a directed pairing by signal margin above chooser threshold.

    Attributes:
        chooser_threshold_trait: Integer threshold characteristic on first parent.
        signal_trait: Integer signal characteristic on second parent.
        source: Characteristic source used for both values. Defaults to raw
            genetic expression for backward compatibility.
    """

    chooser_threshold_trait: str
    signal_trait: str
    source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate directed preference trait names and source."""
        _validate_trait_name(
            self.chooser_threshold_trait,
            name="chooser_threshold_trait",
        )
        _validate_trait_name(self.signal_trait, name="signal_trait")
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return operative characteristics required by this policy."""
        return frozenset((self.chooser_threshold_trait, self.signal_trait))

    @property
    def required_traits(self) -> frozenset[str]:
        """Return biological traits backing the required characteristics."""
        return validate_required_traits(self.required_characteristics)

    def __call__(
        self,
        chooser: Organism,
        signaler: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return signal minus chooser threshold as a directed preference score."""
        threshold = integer_characteristic(
            self.source,
            chooser,
            self.chooser_threshold_trait,
            context=simulation_state,
        )
        signal = integer_characteristic(
            self.source,
            signaler,
            self.signal_trait,
            context=simulation_state,
        )
        return signal - threshold
