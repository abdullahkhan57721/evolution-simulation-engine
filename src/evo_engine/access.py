"""Domain-neutral contracts for reading entities from model state.

Entity access is intentionally separate from admission and departure. Admission
and departure mutate membership; access only resolves entity references or
provides a stable snapshot of current entities. The contract contains no
biological, spatial, identity-allocation, storage, or lifecycle semantics.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

AccessReferenceT = TypeVar("AccessReferenceT", contravariant=True)
AccessStateT = TypeVar("AccessStateT", contravariant=True)
AccessEntityT = TypeVar("AccessEntityT", covariant=True)


class EntityAccessModel(Protocol[AccessReferenceT, AccessStateT, AccessEntityT]):
    """Provide read-only access to entities held by mutable domain state."""

    def get(
        self,
        reference: AccessReferenceT,
        *,
        state: AccessStateT,
    ) -> AccessEntityT:
        """Return the entity identified by a domain-specific reference.

        Args:
            reference: Domain-specific reference used to resolve one entity.
            state: Domain state from which the entity is read.

        Returns:
            Resolved entity.
        """
        ...

    def entities(
        self,
        *,
        state: AccessStateT,
    ) -> tuple[AccessEntityT, ...]:
        """Return a stable snapshot of currently accessible entities.

        Args:
            state: Domain state from which entities are read.

        Returns:
            Tuple snapshot in the domain adapter's deterministic iteration order.
        """
        ...
