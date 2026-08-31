"""Biological event semantics interpreted by observation and analysis."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ParentageEvent(Protocol):
    """Expose reproductive parents for an event that creates offspring."""

    @property
    def parent_ids(self) -> tuple[int, ...]:
        """Return reproductive parent IDs in biological parent order."""
        ...


@runtime_checkable
class MortalityEvent(Protocol):
    """Expose organism IDs whose biological death is caused by an event."""

    @property
    def deceased_organism_ids(self) -> tuple[int, ...]:
        """Return IDs of organisms biologically killed by the event."""
        ...
