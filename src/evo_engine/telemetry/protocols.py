"""Protocols for consuming committed simulation telemetry."""

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
