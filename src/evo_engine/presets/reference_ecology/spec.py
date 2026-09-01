"""Build declarative simulation specifications for the reference ecology."""

from __future__ import annotations

from collections.abc import Iterable

from evo_engine.behavior import BEHAVIOR_SELECTION_MODEL
from evo_engine.biology import BiologicalSimulationSpec
from evo_engine.engine import Observer
from evo_engine.genetics import GENETIC_ARCHITECTURE
from evo_engine.presets.reference_ecology.builders import (
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.presets.reference_ecology.config import (
    ReferenceEcologyConfig,
    resolve_reference_config,
)
from evo_engine.telemetry import TelemetryObserver


def build_reference_spec(
    config: ReferenceEcologyConfig | None = None,
    *,
    observers: Iterable[Observer] = (),
    telemetry_observers: Iterable[TelemetryObserver] = (),
) -> BiologicalSimulationSpec:
    """Build an immutable, dependency-validatable reference simulation spec."""
    resolved_config = resolve_reference_config(config)
    observer_tuple = tuple(observers)
    telemetry_observer_tuple = tuple(telemetry_observers)
    simulation = build_reference_simulation(resolved_config)
    engine = build_reference_engine(
        resolved_config,
        observers=observer_tuple,
        telemetry_observers=telemetry_observer_tuple,
    )

    return BiologicalSimulationSpec(
        initial_world_state=simulation.state.world,
        genetic_architecture=simulation.context.require(GENETIC_ARCHITECTURE),
        step_coordinator=engine.step_coordinator,
        stopping_condition=engine.stopping_condition,
        seed=resolved_config.seed,
        behavior_selection_model=simulation.context.require(BEHAVIOR_SELECTION_MODEL),
        observers=observer_tuple,
        telemetry_observers=telemetry_observer_tuple,
    )
