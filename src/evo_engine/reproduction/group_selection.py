"""Reproductive-group selection policies."""

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
class ReproductiveGroup:
    """Represent one candidate group of reproductive participants.

    Shared reproduction orchestration permits any nonempty group size. Concrete
    group-selection policies decide which organisms participate, while a separate
    genetic-contributor policy decides which participants supply transmissible
    state during materialization.

    Attributes:
        participant_ids: Ordered state-local references of reproductive participants.
        preference_score: Group preference used during conflict resolution.
    """

    participant_ids: tuple[int, ...]
    preference_score: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int,
    )

    def __attrs_post_init__(self) -> None:
        """Validate participant references."""
        validators.validate_tuple(
            self.participant_ids,
            name="participant_ids",
        )

        if not self.participant_ids:
            raise ValueError("participant_ids must contain at least one participant ID.")

        seen_ids: set[int] = set()

        for index, participant_id in enumerate(self.participant_ids):
            validators.validate_int_ge(
                participant_id,
                bound=0,
                name=f"participant_ids[{index}]",
            )

            if participant_id in seen_ids:
                raise ValueError(
                    "participant_ids must not contain duplicate participant IDs."
                )

            seen_ids.add(participant_id)


class ReproductiveGroupSelection(Protocol):
    """Define how eligible organisms form candidate reproductive groups."""

    def propose_reproductive_groups(
        self,
        eligible_participants: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> Sequence[ReproductiveGroup]:
        """Propose candidate reproductive groups.

        Args:
            eligible_participants: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references for
                resolver-facing reproductive groups.

        Returns:
            Candidate nonempty reproductive groups.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class SingleParent:
    """Propose each eligible organism as a one-participant reproductive group."""

    def propose_reproductive_groups(
        self,
        eligible_participants: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> list[ReproductiveGroup]:
        """Propose one reproductive group per eligible organism.

        Args:
            eligible_participants: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references.

        Returns:
            Candidate one-participant groups.
        """
        world = simulation_state.domain_state
        return [
            ReproductiveGroup(
                participant_ids=(
                    reference_model.reference(
                        participant,
                        state=world,
                    ),
                ),
            )
            for participant in eligible_participants
        ]


CanMate = Callable[[Organism, Organism, SimulationState], bool]
PairPreferenceFunction = Callable[[Organism, Organism, SimulationState], int]


def _always_can_mate(
    first_participant: Organism,
    second_participant: Organism,
    simulation_state: SimulationState,
) -> bool:
    """Return whether a reproductive pair is biologically compatible."""
    return True


def _neutral_pair_preference(
    first_participant: Organism,
    second_participant: Organism,
    simulation_state: SimulationState,
) -> int:
    """Return a neutral mating preference score."""
    return 0


@attrs.frozen(slots=True, kw_only=True)
class PairwiseMating:
    """Propose every eligible two-participant mating pair.

    Callable mating collaborators may optionally expose ``required_traits``.
    Those nested requirements are aggregated automatically with explicitly
    declared callback dependencies, preserving support for plain functions and
    lambdas while enabling structured trait-aware sexual-selection policies.

    Attributes:
        neighborhood: Hard spatial neighborhood within which mating is possible.
        can_mate: Callable determining biological pair compatibility.
        preference_function: Callable returning an integer preference score for a
            candidate pair. If participant roles are interchangeable, this
            function should be symmetric in its two organism arguments.
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
    required_traits: frozenset[str] = attrs.field(factory=frozenset)

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

    def propose_reproductive_groups(
        self,
        eligible_participants: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        reference_model: EntityReferenceModel[Organism, WorldState, int],
    ) -> list[ReproductiveGroup]:
        """Propose every spatially and biologically valid participant pair.

        Args:
            eligible_participants: Organisms individually eligible to reproduce.
            simulation_state: Current simulation state.
            reference_model: Policy deriving state-local organism references.

        Returns:
            Candidate two-participant reproductive groups.

        Raises:
            TypeError: If can_mate does not return a Boolean or the preference
                function does not return an integer.
        """
        groups: list[ReproductiveGroup] = []
        world = simulation_state.domain_state

        # combinations() treats participant roles as interchangeable and avoids
        # emitting both (A, B) and (B, A). Role-specific reproduction uses a
        # different ReproductiveGroupSelection implementation.
        for first_participant, second_participant in combinations(
            eligible_participants,
            2,
        ):
            if not self.neighborhood.contains(
                center_x=first_participant.x,
                center_y=first_participant.y,
                other_x=second_participant.x,
                other_y=second_participant.y,
                width=world.width,
                height=world.height,
            ):
                continue

            can_mate = self.can_mate(
                first_participant,
                second_participant,
                simulation_state,
            )

            if type(can_mate) is not bool:
                raise TypeError("can_mate must return a Boolean.")

            if not can_mate:
                continue

            preference_score = self.preference_function(
                first_participant,
                second_participant,
                simulation_state,
            )

            if type(preference_score) is not int:
                raise TypeError("preference_function must return an integer.")

            groups.append(
                ReproductiveGroup(
                    participant_ids=(
                        reference_model.reference(
                            first_participant,
                            state=world,
                        ),
                        reference_model.reference(
                            second_participant,
                            state=world,
                        ),
                    ),
                    preference_score=preference_score,
                )
            )

        return groups
