"""Protocols for components that declare behavioral purpose."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BehavioralPurposeProvider(Protocol):
    """Expose the behavioral purpose represented by a configured component."""

    @property
    def behavioral_purpose(self) -> str:
        """Return the component's behavioral-purpose name."""
        ...
