"""Reusable mating-compatibility and sexual-selection policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

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
    """Require each parent to be within the other's expressed search range.

    Parent roles are currently interchangeable, so the initial built-in search
    rule is deliberately mutual: a pair is discoverable only when the spatial
    distance lies within both organisms' search ranges.

    Attributes:
        distance_metric: Spatial metric used to compare parent coordinates.
        trait_name: Genetic phenotype trait storing nonnegative search range.
    """

    distance_metric: DistanceMetric = attrs.field(factory=Chebyshev)
    trait_name: str = MATE_SEARCH_RANGE

    def __attrs_post_init__(self) -> None:
        """Validate mating-search configuration."""
        if not callable(getattr(self.distance_metric, "distance", None)):
            raise TypeError("distance_metric must provide a callable distance method.")

        trait_name = validators.validate_str(self.trait_name, name="trait_name")
        if not trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the mate-search trait required by the policy."""
        return frozenset({self.trait_name})

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether both parents can discover each other.

        Args:
            first_parent: First candidate parent.
            second_parent: Second candidate parent.
            simulation_state: Current simulation state.

        Returns:
            ``True`` when pair distance is within both expressed search ranges.

        Raises:
            ValueError: If either expressed search range is negative.
        """
        first_range = validators.validate_int_ge(
            first_parent.genetic_phenotype.int_value(self.trait_name),
            bound=0,
            name=f"first_parent genetic_phenotype[{self.trait_name!r}]",
        )
        second_range = validators.validate_int_ge(
            second_parent.genetic_phenotype.int_value(self.trait_name),
            bound=0,
            name=f"second_parent genetic_phenotype[{self.trait_name!r}]",
        )
        world = simulation_state.world
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
        choosiness_trait_name: Genetic phenotype trait storing the minimum
            acceptable partner signal.
        signal_trait_name: Genetic phenotype trait storing mating signal strength.
    """

    choosiness_trait_name: str = CHOOSINESS
    signal_trait_name: str = MATING_SIGNAL

    def __attrs_post_init__(self) -> None:
        """Validate configured sexual-selection trait names."""
        _validate_trait_names(
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return choosiness and mating-signal trait requirements."""
        return frozenset({self.choosiness_trait_name, self.signal_trait_name})

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether both parents satisfy each other's acceptance threshold."""
        first_choosiness, first_signal = _sexual_selection_values(
            first_parent,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
            prefix="first_parent",
        )
        second_choosiness, second_signal = _sexual_selection_values(
            second_parent,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
            prefix="second_parent",
        )

        return second_signal >= first_choosiness and first_signal >= second_choosiness


@attrs.frozen(slots=True, kw_only=True)
class MutualSignalMarginPreference:
    """Prefer pairs whose signals exceed both parents' acceptance thresholds.

    The score is symmetric in parent order and equals the sum of both mutual
    signal surpluses. A pair exactly meeting both thresholds receives zero.

    Attributes:
        choosiness_trait_name: Genetic phenotype trait storing the minimum
            acceptable partner signal.
        signal_trait_name: Genetic phenotype trait storing mating signal strength.
    """

    choosiness_trait_name: str = CHOOSINESS
    signal_trait_name: str = MATING_SIGNAL

    def __attrs_post_init__(self) -> None:
        """Validate configured sexual-selection trait names."""
        _validate_trait_names(
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return choosiness and mating-signal trait requirements."""
        return frozenset({self.choosiness_trait_name, self.signal_trait_name})

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return the symmetric total mutual signal surplus."""
        first_choosiness, first_signal = _sexual_selection_values(
            first_parent,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
            prefix="first_parent",
        )
        second_choosiness, second_signal = _sexual_selection_values(
            second_parent,
            choosiness_trait_name=self.choosiness_trait_name,
            signal_trait_name=self.signal_trait_name,
            prefix="second_parent",
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
    choosiness_trait_name: str,
    signal_trait_name: str,
    prefix: str,
) -> tuple[int, int]:
    choosiness = validators.validate_int_ge(
        organism.genetic_phenotype.int_value(choosiness_trait_name),
        bound=0,
        name=f"{prefix} genetic_phenotype[{choosiness_trait_name!r}]",
    )
    signal = validators.validate_int_ge(
        organism.genetic_phenotype.int_value(signal_trait_name),
        bound=0,
        name=f"{prefix} genetic_phenotype[{signal_trait_name!r}]",
    )
    return choosiness, signal
