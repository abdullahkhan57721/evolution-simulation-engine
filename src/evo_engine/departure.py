"""Domain-neutral contracts for removing entities from mutable model state.

Departure is the structural inverse of admission. An admission model defines
how an entity enters domain state; a departure model defines how an existing
entity leaves it. The contract contains no biological, mortality, migration,
identity-allocation, spatial, or container semantics.

Departure belongs to mechanical application. Domain events remain responsible
for describing *why* an entity leaves state, so biological death is not
conflated with generic removal, migration, despawning, or transfer.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

DepartureReferenceT = TypeVar("DepartureReferenceT", contravariant=True)
DepartureStateT = TypeVar("DepartureStateT", contravariant=True)
DepartedEntityT = TypeVar("DepartedEntityT", covariant=True)


class EntityDepartureModel(
    Protocol[DepartureReferenceT, DepartureStateT, DepartedEntityT]
):
    """Remove one referenced entity from mutable domain state."""

    def depart(
        self,
        reference: DepartureReferenceT,
        *,
        state: DepartureStateT,
    ) -> DepartedEntityT:
        """Remove and return an entity from domain state.

        Args:
            reference: Domain-defined reference identifying the entity to remove.
            state: Mutable domain state from which the entity departs.

        Returns:
            Entity removed from state.
        """
        ...
