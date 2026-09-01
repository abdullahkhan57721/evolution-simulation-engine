"""Reusable mating-compatibility and sexual-selection policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.characteristics import (
    GeneticPhenotypeCharacteristics,
    integer_characteristic,
)
from evo_engine.genetics import CHOOSINESS, MATE_SEARCH_RANGE, MATING_SIGNAL
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.spatial.distances import Chebyshev, DistanceMetric
from evo_engine.validation import validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class MatingCompatibility(Protocol):
    """Determine whether two individually eligible organisms may mate."""

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the candidate parent pair is compatible."""
        ...


@runtime_checkable
class MatingPreference(Protocol):
    """Score a candidate mating pair for conflict resolution."""

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return an integer pair preference score; higher is preferred."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class MutualMateSearchRange:
    """Require each parent to be within the other's operative search range.

    Parent roles are currently interchangeable, so the built-in search rule is
    deliberately mutual: a pair is discoverable only when spatial distance lies
    within both organisms' search ranges.

    Attributes:
        distance_metric: Spatial metric used to compare parent coordinates.
        trait_name: Biological trait/characteristic storing nonnegative range.
        source: Characteristic source used to read the operative range. Defaults
            to raw genetic expression for backward compatibility.
    """

    distance_metric: DistanceMetric = attrs.field(factory=Chebyshev)
    trait_name: str = MATE_SEARCH_RANGE
    source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate mating-search configuration."""
        if not callable(getattr(self.distance_metric, "distance", None)):
            raise TypeError("distance_metric must provide a callable distance method.")

        trait_name = validators.validate_str(self.trait_name, name="trait_name")
        if not trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return the mate-search operative characteristic."""
        return frozenset({self.trait_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the biological trait required by the policy."""
        return self.required_characteristics

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether both parents can discover each other."""
        first_range = integer_characteristic(
            self.source,
            first_parent,
            self.trait_name,
            context=simulation_state,
            minimum=0,
        )
        second_range = integer_characteristic(
            self.source,
            second_parent,
            self.trait_name,
            context=simulation_state,
            minimum=0,
        )
        world = simulation_state.domain_state
        distance = self.distance_metric.distance(
            x1=first_parent.x,
            y1=first_parent.y,
            x2=second_parent.x,
            y2=second_parent.y,
            width=world.width,
            height=world.height,
        )

        return distance <= first_range and distance <= second_range


@attrs.frozen(slots=True, kw_only=True)
class MutualSignalCompatibility:
    """Require each parent's signal to satisfy the other's choosiness threshold.

    Attributes:
        choosiness_trait_name: Trait/characteristic storing minimum acceptable
            partner signal.
        signal_trait_name: Trait/characteristic storing mating signal strength.
        source: Characteristic source used to read both operative values.
    """

    choosiness_trait_name: str = CHOOSINESS
    signal_trait_name: str = MATING_SIGNAL
    source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate configured sexual-selection names and source."""
        _validate_trait_names(
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return choosiness and mating-signal operative characteristics."""
        return frozenset({self.choosiness_trait_name, self.signal_trait_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return biological traits required by the policy."""
        return self.required_characteristics

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether both parents satisfy each other's acceptance threshold."""
        first_choosiness, first_signal = _sexual_selection_values(
            first_parent,
            source=self.source,
            simulation_state=simulation_state,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )
        second_choosiness, second_signal = _sexual_selection_values(
            second_parent,
            source=self.source,
            simulation_state=simulation_state,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )

        return second_signal >= first_choosiness and first_signal >= second_choosiness


@attrs.frozen(slots=True, kw_only=True)
class MutualSignalMarginPreference:
    """Prefer pairs whose signals exceed both parents' acceptance thresholds.

    The score is symmetric in parent order and equals the sum of both mutual
    signal surpluses. A pair exactly meeting both thresholds receives zero.

    Attributes:
        choosiness_trait_name: Trait/characteristic storing minimum acceptable
            partner signal.
        signal_trait_name: Trait/characteristic storing mating signal strength.
        source: Characteristic source used to read both operative values.
    """

    choosiness_trait_name: str = CHOOSINESS
    signal_trait_name: str = MATING_SIGNAL
    source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)

    def __attrs_post_init__(self) -> None:
        """Validate configured sexual-selection names and source."""
        _validate_trait_names(
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )
        if not callable(getattr(self.source, "value_for", None)):
            raise TypeError("source must provide a callable value_for method.")

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return choosiness and mating-signal operative characteristics."""
        return frozenset({self.choosiness_trait_name, self.signal_trait_name})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return biological traits required by the preference."""
        return self.required_characteristics

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return the symmetric total mutual signal surplus."""
        first_choosiness, first_signal = _sexual_selection_values(
            first_parent,
            source=self.source,
            simulation_state=simulation_state,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )
        second_choosiness, second_signal = _sexual_selection_values(
            second_parent,
            source=self.source,
            simulation_state=simulation_state,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )

        return second_signal - first_choosiness + first_signal - second_choosiness


@attrs.frozen(slots=True, kw_only=True)
class AllOfMatingCompatibility:
    """Require every composed mating compatibility policy to accept a pair.

    Attributes:
        compatibilities: Ordered mating compatibility policies to evaluate.
    """

    compatibilities: tuple[MatingCompatibility, ...]

    def __attrs_post_init__(self) -> None:
        """Validate composed mating compatibility policies."""
        if not self.compatibilities:
            raise ValueError("compatibilities must contain at least one policy.")

        for compatibility in self.compatibilities:
            if not callable(compatibility):
                raise TypeError("each mating compatibility must be callable.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the union of nested mating trait requirements."""
        return collect_required_traits(*self.compatibilities)

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every nested mating policy accepts the pair."""
        return all(
            compatibility(first_parent, second_parent, simulation_state)
            for compatibility in self.compatibilities
        )


def _validate_trait_names(
    *,
    choosiness_trait_name: str,
    signal_trait_name: str,
) -> None:
    for field_name, trait_name in (
        ("choosiness_trait_name", choosiness_trait_name),
        ("signal_trait_name", signal_trait_name),
    ):
        validated_name = validators.validate_str(trait_name, name=field_name)
        if not validated_name.strip():
            raise ValueError(f"{field_name} must not be empty or whitespace-only.")


def _sexual_selection_values(
    organism: Organism,
    *,
    source: object,
    simulation_state: SimulationState,
    choosiness_trait_name: str,
    signal_trait_name: str,
) -> tuple[int, int]:
    choosiness = integer_characteristic(
        source,
        organism,
        choosiness_trait_name,
        context=simulation_state,
        minimum=0,
    )
    signal = integer_characteristic(
        source,
        organism,
        signal_trait_name,
        context=simulation_state,
        minimum=0,
    )
    return choosiness, signal
