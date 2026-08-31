"""Domain-neutral contracts for admitting entities into mutable model state.

Admission is intentionally separate from entity production. A production model
constructs an already-determined entity; an admission model defines how that
entity becomes part of domain state. The contract contains no biological,
spatial, identity, or container semantics.

Admission belongs to mechanical application. Stochastic choices and other
materialization decisions should be settled before ``admit`` is called.
"""

from __future__ import annotations

from typing import Protocol, TypeVar

AdmissionEntityT = TypeVar("AdmissionEntityT", contravariant=True)
AdmissionStateT = TypeVar("AdmissionStateT", contravariant=True)


class EntityAdmissionModel(Protocol[AdmissionEntityT, AdmissionStateT]):
    """Admit an already-produced entity into mutable domain state."""

    def admit(
        self,
        entity: AdmissionEntityT,
        *,
        state: AdmissionStateT,
    ) -> None:
        """Admit an entity into domain state.

        Args:
            entity: Fully produced entity ready to enter domain state.
            state: Mutable domain state receiving the entity.
        """
        ...
