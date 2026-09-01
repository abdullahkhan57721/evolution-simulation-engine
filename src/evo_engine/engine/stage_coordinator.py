"""Coordinate one domain-neutral simulation update stage."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, NamedTuple, cast

from evo_engine.engine.protocols import (
    EventMaterializer,
    Process,
    Resolver,
    SimulationEvent,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.telemetry import AppliedEvent

_MaterializeEventCallable = Callable[
    [SimulationState, SimulationEvent],
    SimulationEvent,
]
_EffectsSinceCallable = Callable[[int], object]


class _ProcessDispatch(NamedTuple):
    """Cache one process's event-dispatch metadata."""

    process: Process[Any, Any]
    materialize_event: _MaterializeEventCallable | None
    process_type_name: str
    proposed_event_type_name: str


# Prepared applications are created once per resolved event and immediately
# unpacked during application, so a plain tuple keeps that hot-path data minimal.
_PreparedApplication = tuple[
    Process[Any, Any],
    SimulationEvent,
    str,
    str,
]


class StageCoordinator:
    """Coordinate proposal, resolution, materialization, and application."""

    def __init__(
        self,
        processes: Sequence[Process[Any, Any]],
        resolver: Resolver,
    ) -> None:
        """Initialize an update stage."""
        self.processes = tuple(processes)
        self.resolver = resolver
        self._dispatch_by_event_type: dict[
            type[SimulationEvent],
            _ProcessDispatch,
        ] = {}
        self._event_type_names: dict[type[object], str] = {}

        for process in self.processes:
            event_type = process.event_type
            if event_type in self._dispatch_by_event_type:
                raise ValueError(
                    "Processes within a stage must have unique event types."
                )

            materialize_event: _MaterializeEventCallable | None = None
            if isinstance(process, EventMaterializer):
                materialize_event = cast(
                    _MaterializeEventCallable,
                    process.materialize_event,
                )

            event_type_name = _qualified_type_name(event_type)
            self._event_type_names[event_type] = event_type_name
            self._dispatch_by_event_type[event_type] = _ProcessDispatch(
                process=process,
                materialize_event=materialize_event,
                process_type_name=_qualified_type_name(type(process)),
                proposed_event_type_name=event_type_name,
            )

    def coordinate(
        self,
        simulation_state: SimulationState,
        *,
        stage_index: int = 0,
    ) -> tuple[AppliedEvent, ...]:
        """Coordinate one stage and return telemetry for applied transitions.

        All processes propose from the same stage-start state. The resolver then
        selects compatible transitions. Every selected transition is materialized
        before any is applied, preserving stage simultaneity while allowing
        accepted stochastic consequences to be determined after resolution.

        The domain state may optionally expose ``effect_count`` and
        ``effects_since``. Effects captured through that journal are attached to
        committed telemetry as opaque domain values.
        """
        if type(stage_index) is not int:
            raise TypeError("stage_index must be an integer.")
        if stage_index < 0:
            raise ValueError("stage_index must be nonnegative.")

        proposed_events = self._propose_events(simulation_state)
        resolved_events = self.resolver.resolve_events(
            simulation_state=simulation_state,
            proposed_events=proposed_events,
        )
        prepared_applications = self._prepare_applications(
            simulation_state,
            resolved_events,
        )
        return _apply_prepared_applications(
            simulation_state=simulation_state,
            prepared_applications=prepared_applications,
            stage_index=stage_index,
        )

    def _propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[SimulationEvent]:
        """Collect proposals from every process against the stage-start state."""
        proposed_events: list[SimulationEvent] = []
        for process in self.processes:
            proposed_events.extend(process.propose_events(simulation_state))
        return proposed_events

    def _prepare_applications(
        self,
        simulation_state: SimulationState,
        resolved_events: Sequence[SimulationEvent],
    ) -> list[_PreparedApplication]:
        """Materialize all resolved events before any application begins."""
        prepared_applications: list[_PreparedApplication] = []
        for resolved_event in resolved_events:
            event_type = type(resolved_event)
            dispatch = self._dispatch_by_event_type.get(event_type)
            if dispatch is None:
                raise RuntimeError(
                    "No process is registered for resolved event type "
                    f"{event_type.__name__}."
                )

            materialized_event = resolved_event
            event_type_name = dispatch.proposed_event_type_name
            if dispatch.materialize_event is not None:
                materialized_event = dispatch.materialize_event(
                    simulation_state,
                    resolved_event,
                )
                event_type_name = self._event_type_name(type(materialized_event))

            prepared_applications.append(
                (
                    dispatch.process,
                    materialized_event,
                    dispatch.process_type_name,
                    event_type_name,
                )
            )
        return prepared_applications

    def _event_type_name(self, event_type: type[object]) -> str:
        """Return and cache the qualified name for one materialized event type."""
        event_type_name = self._event_type_names.get(event_type)
        if event_type_name is None:
            event_type_name = _qualified_type_name(event_type)
            self._event_type_names[event_type] = event_type_name
        return event_type_name


def _apply_prepared_applications(
    *,
    simulation_state: SimulationState,
    prepared_applications: Sequence[_PreparedApplication],
    stage_index: int,
) -> tuple[AppliedEvent, ...]:
    """Apply prepared events and capture optional domain-state effects."""
    applied_events: list[AppliedEvent] = []
    domain_state = simulation_state.world
    effects_since: _EffectsSinceCallable | None = None

    for process, event, process_type_name, event_type_name in prepared_applications:
        effect_checkpoint = getattr(domain_state, "effect_count", None)
        if effect_checkpoint is not None and (
            type(effect_checkpoint) is not int or effect_checkpoint < 0
        ):
            raise TypeError("domain-state effect_count must be a nonnegative integer.")

        process.apply_event(simulation_state, event)

        effects: tuple[Any, ...] = ()
        if effect_checkpoint is not None:
            if effects_since is None:
                effects_since = _resolve_effects_since(domain_state)
            captured_effects = effects_since(effect_checkpoint)
            if type(captured_effects) is not tuple:
                raise TypeError("domain-state effects_since must return a tuple.")
            effects = captured_effects

        applied_events.append(
            AppliedEvent._from_kernel_values(
                event_step_index=event.step_index,
                stage_index=stage_index,
                process_type=process_type_name,
                event_type=event_type_name,
                event=event,
                effects=effects,
            )
        )

    return tuple(applied_events)


def _resolve_effects_since(domain_state: object) -> _EffectsSinceCallable:
    effects_since = getattr(domain_state, "effects_since", None)
    if not callable(effects_since):
        raise TypeError(
            "domain state with effect_count must provide callable effects_since."
        )
    return cast(_EffectsSinceCallable, effects_since)


def _qualified_type_name(value_type: type[object]) -> str:
    """Return a stable module-qualified type name."""
    return f"{value_type.__module__}.{value_type.__qualname__}"
