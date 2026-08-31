"""Domain-neutral contracts for deriving references to admitted entities.

Entity references are intentionally separate from access, admission, and
departure. A reference model derives the domain-specific handle by which an
already-admitted entity is addressed. It does not allocate references, mutate
membership, resolve storage, or interpret lifecycle meaning.

Including domain state in the contract allows references to be state-local or
context-dependent without imposing any particular identity representation.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

ReferenceEntityT = TypeVar("ReferenceEntityT", contravariant=True)
ReferenceStateT = TypeVar("ReferenceStateT", contravariant=True)
ReferenceT = TypeVar("ReferenceT", covariant=True)


class EntityReferenceModel(Protocol[ReferenceEntityT, ReferenceStateT, ReferenceT]):
    """Derive a domain-specific reference for an already-admitted entity."""

    def reference(
        self,
        entity: ReferenceEntityT,
        *,
        state: ReferenceStateT,
    ) -> ReferenceT:
        """Return the reference that identifies an entity in domain state.

        Args:
            entity: Already-admitted entity whose reference is requested.
            state: Domain state in which the reference is meaningful.

        Returns:
            Domain-specific entity reference.
        """
        ...
