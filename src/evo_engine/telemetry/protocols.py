"""Protocols for consuming and interpreting committed simulation telemetry."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from evo_engine.telemetry.records import StepTelemetry


@runtime_checkable
class TelemetryObserver(Protocol):
    """Observe committed event telemetry without participating in updates."""

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        """Return whether one committed step telemetry record should be observed."""
        ...

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        """Observe one committed step telemetry record."""
        ...


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
