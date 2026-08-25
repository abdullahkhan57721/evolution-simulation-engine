"""Contextual reproductive-role assignment policies."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import validators
from evo_engine.world.organism import Organism


def _nonblank(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


class ReproductiveRoleModel(Protocol):
    """Determine which contextual reproductive roles an organism may occupy."""

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by role assignment."""
        ...

    def roles_for(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> frozenset[str]:
        """Return nonblank role labels available to an organism."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class MatingTypeRoles:
    """Map immutable mating types to contextual reproductive roles.

    A mating type may provide zero, one, or multiple roles. Roles are therefore
    participation capabilities of a mating system, not additional organism
    identity fields. This permits simultaneous hermaphroditism and other
    multi-role systems without assigning contradictory mating types.

    Attributes:
        roles_by_mating_type: ``(mating_type, roles)`` mappings. Each roles tuple
            contains unique nonblank role labels.
        default_roles: Roles available to unlisted mating types.
    """

    roles_by_mating_type: tuple[tuple[str, tuple[str, ...]], ...]
    default_roles: tuple[str, ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate mating-type-to-role mappings."""
        validators.validate_tuple(self.roles_by_mating_type, name="roles_by_mating_type")
        seen_types: set[str] = set()
        for index, entry in enumerate(self.roles_by_mating_type):
            if type(entry) is not tuple:
                raise TypeError(f"roles_by_mating_type[{index}] must be a tuple.")
            if len(entry) != 2:
                raise ValueError(
                    f"roles_by_mating_type[{index}] must contain exactly two items."
                )
            mating_type, roles = entry
            validated_type = _nonblank(
                mating_type,
                name=f"roles_by_mating_type[{index}][0]",
            )
            if validated_type in seen_types:
                raise ValueError("roles_by_mating_type must not contain duplicate types.")
            seen_types.add(validated_type)
            self._validate_roles(roles, name=f"roles_by_mating_type[{index}][1]")
        self._validate_roles(self.default_roles, name="default_roles")

    @staticmethod
    def _validate_roles(roles: object, *, name: str) -> None:
        validated_roles = validators.validate_tuple(roles, name=name)
        seen: set[str] = set()
        for index, role in enumerate(validated_roles):
            validated_role = _nonblank(role, name=f"{name}[{index}]")
            if validated_role in seen:
                raise ValueError(f"{name} must not contain duplicate roles.")
            seen.add(validated_role)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return no genetic phenotype trait requirements."""
        return frozenset()

    def roles_for(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> frozenset[str]:
        """Return roles configured for the organism's mating type."""
        for mating_type, roles in self.roles_by_mating_type:
            if organism.mating_type == mating_type:
                return frozenset(roles)
        return frozenset(self.default_roles)
