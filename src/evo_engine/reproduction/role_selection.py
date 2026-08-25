"""Role-aware parent-selection policies."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import (
    collect_required_traits,
    validate_required_traits,
)
from evo_engine.reproduction.parent_selection import ParentGroup
from evo_engine.reproduction.roles import ReproductiveRoleModel
from evo_engine.spatial.neighborhoods import Neighborhood
from evo_engine.validation import validators
from evo_engine.world.organism import Organism

CanMate = Callable[[Organism, Organism, SimulationState], bool]
PairPreferenceFunction = Callable[[Organism, Organism, SimulationState], int]


def _always_can_mate(
    first_parent: Organism,
    second_parent: Organism,
    simulation_state: SimulationState,
) -> bool:
    return True


def _neutral_preference(
    first_parent: Organism,
    second_parent: Organism,
    simulation_state: SimulationState,
) -> int:
    return 0


def _nonblank(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


@attrs.frozen(slots=True, kw_only=True)
class DirectedPairwiseMating:
    """Propose ordered two-parent groups selected through explicit roles.

    Parent tuple order has a documented meaning for this selector: index zero
    occupies ``first_role`` and index one occupies ``second_role``. The roles
    are contextual capabilities supplied by ``role_model`` rather than fields
    stored directly on organisms.

    Attributes:
        first_role: Required role for the first parent in each ordered group.
        second_role: Required role for the second parent.
        role_model: Policy assigning available roles to each organism.
        neighborhood: Hard spatial neighborhood within which mating is possible.
        can_mate: Directed biological compatibility policy.
        preference_function: Directed integer mate-choice score.
        required_traits: Additional dependencies for opaque callbacks.
    """

    first_role: str
    second_role: str
    role_model: ReproductiveRoleModel
    neighborhood: Neighborhood
    can_mate: CanMate = attrs.field(
        default=_always_can_mate,
        validator=attrs.validators.is_callable(),
    )
    preference_function: PairPreferenceFunction = attrs.field(
        default=_neutral_preference,
        validator=attrs.validators.is_callable(),
    )
    required_traits: frozenset[str] = attrs.field(factory=frozenset)

    def __attrs_post_init__(self) -> None:
        """Validate role-aware mating configuration and dependencies."""
        _nonblank(self.first_role, name="first_role")
        _nonblank(self.second_role, name="second_role")
        if self.first_role == self.second_role:
            raise ValueError("first_role and second_role must be different.")
        if not callable(getattr(self.role_model, "roles_for", None)):
            raise TypeError("role_model must provide a callable roles_for method.")
        if not callable(getattr(self.neighborhood, "contains", None)):
            raise TypeError("neighborhood must provide a callable contains method.")
        declared = validate_required_traits(
            self.required_traits, name="required_traits"
        )
        nested = collect_required_traits(
            self.role_model,
            self.can_mate,
            self.preference_function,
        )
        object.__setattr__(self, "required_traits", declared | nested)

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
        """Return every valid ordered first-role/second-role candidate pair."""
        first_candidates = tuple(
            parent
            for parent in eligible_parents
            if self.first_role in self.role_model.roles_for(parent, simulation_state)
        )
        second_candidates = tuple(
            parent
            for parent in eligible_parents
            if self.second_role in self.role_model.roles_for(parent, simulation_state)
        )
        groups: list[ParentGroup] = []
        for first_parent in first_candidates:
            for second_parent in second_candidates:
                group = self._propose_pair(
                    first_parent,
                    second_parent,
                    simulation_state=simulation_state,
                )
                if group is not None:
                    groups.append(group)
        return groups

    def _propose_pair(
        self,
        first_parent: Organism,
        second_parent: Organism,
        *,
        simulation_state: SimulationState,
    ) -> ParentGroup | None:
        """Return one valid directed parent group or ``None``."""
        if first_parent.id == second_parent.id:
            return None
        if not self._within_neighborhood(
            first_parent,
            second_parent,
            simulation_state=simulation_state,
        ):
            return None

        can_mate = self.can_mate(
            first_parent,
            second_parent,
            simulation_state,
        )
        if type(can_mate) is not bool:
            raise TypeError("can_mate must return a Boolean.")
        if not can_mate:
            return None

        score = self.preference_function(
            first_parent,
            second_parent,
            simulation_state,
        )
        if type(score) is not int:
            raise TypeError("preference_function must return an integer.")

        return ParentGroup(
            parent_ids=(first_parent.id, second_parent.id),
            preference_score=score,
        )

    def _within_neighborhood(
        self,
        first_parent: Organism,
        second_parent: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        world = simulation_state.world
        return self.neighborhood.contains(
            center_x=first_parent.x,
            center_y=first_parent.y,
            other_x=second_parent.x,
            other_y=second_parent.y,
            width=world.width,
            height=world.height,
        )
