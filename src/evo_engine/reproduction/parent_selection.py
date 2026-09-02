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
from evo_engine.reference import EntityReferenceModel
from evo_engine.spatial.neighborhoods import Neighborhood
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class ParentGroup:
    """Represent one candidate group of reproductive parents.

    Shared reproduction orchestration permits any nonempty group size. Concrete
    parent-selection and inheritance policies remain responsible for enforcing
    any biological arity they require.

    Attributes:
        parent_ids: IDs of contributing reproductive parents.
        preference_score: Group preference used during conflict resolution.
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

        if not self.parent_ids:
            raise ValueError("parent_ids must contain at least one parent ID.")

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

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> Sequence[ParentGroup]:
        """Propose candidate parent groups.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references for
                resolver-facing parent groups.

        Returns:
            Candidate nonempty parent groups.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class SingleParent:
    """Propose each eligible organism as a one-parent reproductive group."""

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> list[ParentGroup]:
        """Propose one reproductive group per eligible organism.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references.

        Returns:
            Candidate one-parent groups.
        """
        world = simulation_state.domain_state
        return [
            ParentGroup(
                parent_ids=(
                    reference_model.reference(
                        parent,
                        state=world,
                    ),
                ),
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

    def propose_parent_groups(
        self,
        eligible_parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> list[ParentGroup]:
        """Propose every spatially and biologically valid parent pair.

        Args:
            eligible_parents: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references.

        Returns:
            Candidate two-parent groups.

        Raises:
            TypeError: If can_mate does not return a Boolean or the
                preference function does not return an integer.
        """
        events: list[ParentGroup] = []
        world = simulation_state.domain_state

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
                        reference_model.reference(
                            first_parent,
                            state=world,
                        ),
                        reference_model.reference(
                            second_parent,
                            state=world,
                        ),
                    ),
                    preference_score=preference_score,
                )
            )

        return events
