"""Build declarative simulation specifications for the reference ecology."""

from __future__ import annotations

from collections.abc import Iterable

from evo_engine.configuration import SimulationSpec
from evo_engine.engine import Observer
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
) -> SimulationSpec:
    """Build an immutable, dependency-validatable reference simulation spec.

    The existing reference simulation and engine builders remain available as
    lower-level biological composition APIs. This function lifts those same
    configured components into ``SimulationSpec`` so cross-component validation
    happens before mutable runtime is created.

    Args:
        config: Optional reference configuration. Defaults to standard values.
        observers: Optional committed-state observers.
        telemetry_observers: Optional committed-event observers.

    Returns:
        Reference ecology specification ready for ``compile()``.
    """
    resolved_config = resolve_reference_config(config)
    observer_tuple = tuple(observers)
    telemetry_observer_tuple = tuple(telemetry_observers)
    simulation = build_reference_simulation(resolved_config)
    engine = build_reference_engine(
        resolved_config,
        observers=observer_tuple,
        telemetry_observers=telemetry_observer_tuple,
    )

    return SimulationSpec(
        initial_world_state=simulation.state.world,
        genetic_architecture=simulation.genetic_architecture,
        step_coordinator=engine.step_coordinator,
        stopping_condition=engine.stopping_condition,
        seed=resolved_config.seed,
        behavior_selection_model=simulation.context.require("behavior_selection_model"),
        observers=observer_tuple,
        telemetry_observers=telemetry_observer_tuple,
    )
