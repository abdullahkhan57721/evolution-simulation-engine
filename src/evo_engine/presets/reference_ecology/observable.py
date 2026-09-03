"""Compose optional observers onto the complete reference ecology preset."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.engine import Observer, SimulationEngine
from evo_engine.presets.reference_ecology.builders import (
    ReferenceEcology,
    build_reference_ecology as _build_reference_ecology,
)
from evo_engine.presets.reference_ecology.config import ReferenceEcologyConfig
from evo_engine.telemetry import TelemetryObserver


def build_reference_ecology(
    config: ReferenceEcologyConfig | None = None,
    *,
    additional_observers: Iterable[Observer] = (),
    additional_telemetry_observers: Iterable[TelemetryObserver] = (),
) -> ReferenceEcology:
    """Build the complete reference ecology with optional extra observers.

    The preset's population, genetic-composition, event, and pedigree recorders
    remain attached. Additional observers are appended after those standard
    recorders and are therefore pure opt-in costs. With no additional observers,
    this function returns the ordinary reference ecology unchanged.

    Args:
        config: Optional reference configuration. Defaults to standard values.
        additional_observers: Extra committed-state observers to attach.
        additional_telemetry_observers: Extra committed-telemetry observers to
            attach.

    Returns:
        Complete reference ecology with the requested additive observers.
    """
    ecology = _build_reference_ecology(config)
    extra_observers = tuple(additional_observers)
    extra_telemetry_observers = tuple(additional_telemetry_observers)

    if not extra_observers and not extra_telemetry_observers:
        return ecology

    return attrs.evolve(
        ecology,
        engine=SimulationEngine(
            step_coordinator=ecology.engine.step_coordinator,
            stopping_condition=ecology.engine.stopping_condition,
            observers=(*ecology.engine.observers, *extra_observers),
            telemetry_observers=(
                *ecology.engine.telemetry_observers,
                *extra_telemetry_observers,
            ),
        ),
    )
