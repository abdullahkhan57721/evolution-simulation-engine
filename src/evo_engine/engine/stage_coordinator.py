"""Coordinate one domain-neutral simulation update stage."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, cast

from evo_engine.engine.protocols import (
    EventMaterializer,
    Process,
    Resolver,
    SimulationEvent,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.telemetry import AppliedEvent

_MaterializerCallable = Callable[
    [SimulationState, SimulationEvent],
    SimulationEvent,
]
_MutationsSinceCallable = Callable[[int], object]
_EventDispatch = tuple[
    Process[Any, Any],
    _MaterializerCallable | None,
    str,
    str,
]
_MaterializedEvent = tuple[
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
            _EventDispatch,
        ] = {}
        self._event_type_names: dict[type[object], str] = {}

        for process in self.processes:
            event_type = process.event_type
            if event_type in self._dispatch_by_event_type:
                raise ValueError(
                    "Processes within a stage must have unique event types."
                )

            materializer: _MaterializerCallable | None = None
            if isinstance(process, EventMaterializer):
                materializer = cast(
                    _MaterializerCallable,
                    process.materialize_event,
                )

            event_type_name = _qualified_type_name(event_type)
            self._event_type_names[event_type] = event_type_name
            self._dispatch_by_event_type[event_type] = (
                process,
                materializer,
                _qualified_type_name(type(process)),
                event_type_name,
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

        The domain state may optionally expose ``mutation_count`` and
        ``mutations_since``. Mutations captured through that journal are attached
        to committed telemetry as opaque domain effects.
        """
        if type(stage_index) is not int:
            raise TypeError("stage_index must be an integer.")
        if stage_index < 0:
            raise ValueError("stage_index must be nonnegative.")

        proposed_events: list[SimulationEvent] = []
        for process in self.processes:
            proposed_events.extend(process.propose_events(simulation_state))

        resolved_events = self.resolver.resolve_events(
            simulation_state=simulation_state,
            proposed_events=proposed_events,
        )

        materialized_events: list[_MaterializedEvent] = []
        for resolved_event in resolved_events:
            event_type = type(resolved_event)
            dispatch = self._dispatch_by_event_type.get(event_type)
            if dispatch is None:
                raise RuntimeError(
                    "No process is registered for resolved event type "
                    f"{event_type.__name__}."
                )

            process, materializer, process_type_name, event_type_name = dispatch
            if materializer is None:
                materialized_event = resolved_event
            else:
                materialized_event = materializer(
                    simulation_state,
                    resolved_event,
                )
                materialized_type = type(materialized_event)
                event_type_name = self._event_type_names.get(materialized_type)
                if event_type_name is None:
                    event_type_name = _qualified_type_name(materialized_type)
                    self._event_type_names[materialized_type] = event_type_name

            materialized_events.append(
                (
                    process,
                    materialized_event,
                    process_type_name,
                    event_type_name,
                )
            )

        return _apply_materialized_events(
            simulation_state=simulation_state,
            materialized_events=materialized_events,
            stage_index=stage_index,
        )


def _apply_materialized_events(
    *,
    simulation_state: SimulationState,
    materialized_events: Sequence[_MaterializedEvent],
    stage_index: int,
) -> tuple[AppliedEvent, ...]:
    """Apply materialized events and capture optional domain-state effects."""
    applied_events: list[AppliedEvent] = []
    domain_state = simulation_state.world
    mutations_since: _MutationsSinceCallable | None = None

    for (
        process,
        materialized_event,
        process_type_name,
        event_type_name,
    ) in materialized_events:
        checkpoint = getattr(domain_state, "mutation_count", None)
        if checkpoint is not None and (type(checkpoint) is not int or checkpoint < 0):
            raise TypeError(
                "domain-state mutation_count must be a nonnegative integer."
            )

        process.apply_event(simulation_state, materialized_event)

        effects: tuple[Any, ...] = ()
        if checkpoint is not None:
            if mutations_since is None:
                mutations_since = _resolve_mutations_since(domain_state)
            mutations = mutations_since(checkpoint)
            if type(mutations) is not tuple:
                raise TypeError("domain-state mutations_since must return a tuple.")
            effects = mutations

        applied_events.append(
            AppliedEvent._from_kernel_values(
                event_step_index=materialized_event.step_index,
                stage_index=stage_index,
                process_type=process_type_name,
                event_type=event_type_name,
                event=materialized_event,
                effects=effects,
            )
        )

    return tuple(applied_events)


def _resolve_mutations_since(domain_state: object) -> _MutationsSinceCallable:
    mutations_since = getattr(domain_state, "mutations_since", None)
    if not callable(mutations_since):
        raise TypeError(
            "domain state with mutation_count must provide callable mutations_since."
        )
    return cast(_MutationsSinceCallable, mutations_since)


def _qualified_type_name(value_type: type[object]) -> str:
    return f"{value_type.__module__}.{value_type.__qualname__}"
