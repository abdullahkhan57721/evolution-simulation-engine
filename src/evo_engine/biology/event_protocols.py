"""Biological event semantics interpreted by observation and analysis."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ParentageEvent(Protocol):
    """Expose genetic parentage for an event that creates offspring.

    Reproductive participation is broader than parentage: an organism may
    participate in a reproductive episode without contributing transmissible
    genetic state. This protocol intentionally records only the contributors used
    for pedigree and genetic ancestry.
    """

    @property
    def parent_ids(self) -> tuple[int, ...]:
        """Return genetic contributor IDs in biological inheritance order."""
        ...


@runtime_checkable
class MortalityEvent(Protocol):
    """Expose organism IDs whose biological death is caused by an event."""

    @property
    def deceased_organism_ids(self) -> tuple[int, ...]:
        """Return IDs of organisms biologically killed by the event."""
        ...
