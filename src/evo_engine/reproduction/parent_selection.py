"""Parent-selection policies for reproduction."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import combinations
from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import (
    collect_required_traits,
    validate_required_traits,
)
from evo_engine.spatial.neighborhoods import Neighborhood
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class ParentGroup:
    """Represent one candidate group of reproductive parents.

    Attributes:
        parent_ids: IDs of one or two contributing parents.
        preference_score: Pairing preference used during conflict resolution.
    """

    parent_ids: tuple[int, ...]
    preference_score: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int,
    )

    def __attrs_post_init__(self) -> None:
        """Validate parent IDs."""
        validators.validate_tuple(
            self.parent_ids,
            name="parent_ids",
        )

        if len(self.parent_ids) not in (1, 2):
            raise ValueError("parent_ids must contain exactly one or two parent IDs.")

        seen_ids: set[int] = set()

        for index, parent_id in enumerate(self.parent_ids):
            validators.validate_int_ge(
                parent_id,
                bound=0,
                name=f"parent_ids[{index}]",
            )

            if parent_id in seen_ids:
                raise ValueError("parent_ids must not contain duplicate parent IDs.")

            seen_ids.add(parent_id)


class ParentSelection(Protocol):
    """Define how eligible organisms form candidate parent groups."""

    @property
    def parent_count(self) -> int:
        """Return the required number of parents per candidate group."""
        ...

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
    ) -> Sequence[ParentGroup]:
        """Propose candidate parent groups.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.

        Returns:
            Candidate one- or two-parent groups.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class SingleParent:
    """Propose each eligible organism as a one-parent reproductive group."""

    @property
    def parent_count(self) -> int:
        """Return one required parent."""
        return 1

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
    ) -> list[ParentGroup]:
        """Propose one reproductive group per eligible organism.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.

        Returns:
            Candidate one-parent groups.
        """
        return [
            ParentGroup(
                parent_ids=(parent.id,),
            )
            for parent in eligible_parents
        ]


CanMate = Callable[[Organism, Organism, SimulationState], bool]
PairPreferenceFunction = Callable[[Organism, Organism, SimulationState], int]


def _always_can_mate(
    first_parent: Organism,
    second_parent: Organism,
    simulation_state: SimulationState,
) -> bool:
    """Return whether a parent pair is biologically compatible."""
    return True


def _neutral_pair_preference(
    first_parent: Organism,
    second_parent: Organism,
    simulation_state: SimulationState,
) -> int:
    """Return a neutral mating preference score."""
    return 0


@attrs.frozen(slots=True, kw_only=True)
class PairwiseMating:
    """Propose every eligible two-parent mating pair.

    Callable mating collaborators may optionally expose ``required_traits``.
    Those nested requirements are aggregated automatically with explicitly
    declared callback dependencies, preserving support for plain functions and
    lambdas while enabling structured trait-aware sexual-selection policies.

    Attributes:
        neighborhood: Hard spatial neighborhood within which mating is possible.
        can_mate: Callable determining biological pair compatibility. This can
            include organism-specific mate-search or sexual-selection rules.
        preference_function: Callable returning an integer preference score
            for a candidate pair. If parent roles are interchangeable, this
            function should be symmetric in its two parent arguments.
        required_traits: Additional genetic phenotype traits read by opaque
            custom mating callbacks. Structured policies contribute their own
            requirements automatically.
    """

    neighborhood: Neighborhood
    can_mate: CanMate = attrs.field(
        default=_always_can_mate,
        validator=attrs.validators.is_callable(),
    )
    preference_function: PairPreferenceFunction = attrs.field(
        default=_neutral_pair_preference,
        validator=attrs.validators.is_callable(),
    )
    required_traits: frozenset[str] = attrs.field(
        factory=frozenset,
    )

    def __attrs_post_init__(self) -> None:
        """Validate mating-policy collaborators and aggregate dependencies."""
        try:
            contains = self.neighborhood.contains
        except AttributeError as error:
            raise TypeError(
                "neighborhood must provide a callable contains method."
            ) from error

        if not callable(contains):
            raise TypeError("neighborhood must provide a callable contains method.")

        declared_requirements = validate_required_traits(
            self.required_traits,
            name="required_traits",
        )
        nested_requirements = collect_required_traits(
            self.can_mate,
            self.preference_function,
        )
        object.__setattr__(
            self,
            "required_traits",
            declared_requirements | nested_requirements,
        )

    @property
    def parent_count(self) -> int:
        """Return two required parents."""
        return 2

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
    ) -> list[ParentGroup]:
        """Propose every spatially and biologically valid parent pair.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.

        Returns:
            Candidate two-parent groups.

        Raises:
            TypeError: If can_mate does not return a Boolean or the
                preference function does not return an integer.
        """
        events: list[ParentGroup] = []
        world = simulation_state.world

        # combinations() treats parent roles as interchangeable and avoids
        # emitting both (A, B) and (B, A). Role-specific reproduction can use
        # a different ParentSelection implementation later.
        for first_parent, second_parent in combinations(
            eligible_parents,
            2,
        ):
            if not self.neighborhood.contains(
                center_x=first_parent.x,
                center_y=first_parent.y,
                other_x=second_parent.x,
                other_y=second_parent.y,
                width=world.width,
                height=world.height,
            ):
                continue

            can_mate = self.can_mate(
                first_parent,
                second_parent,
                simulation_state,
            )

            if type(can_mate) is not bool:
                raise TypeError("can_mate must return a Boolean.")

            if not can_mate:
                continue

            preference_score = self.preference_function(
                first_parent,
                second_parent,
                simulation_state,
            )

            if type(preference_score) is not int:
                raise TypeError("preference_function must return an integer.")

            events.append(
                ParentGroup(
                    parent_ids=(
                        first_parent.id,
                        second_parent.id,
                    ),
                    preference_score=preference_score,
                )
            )

        return events
