"""Coordinate one domain-neutral simulation update stage."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from evo_engine.engine.protocols import (
    EventMaterializer,
    Process,
    Resolver,
    SimulationEvent,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.telemetry import AppliedEvent


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
        self._processes_by_event_type: dict[
            type[SimulationEvent],
            Process[Any, Any],
        ] = {}
        for process in self.processes:
            if process.event_type in self._processes_by_event_type:
                raise ValueError(
                    "Processes within a stage must have unique event types."
                )
            self._processes_by_event_type[process.event_type] = process

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

        materialized_events: list[tuple[Process[Any, Any], SimulationEvent]] = []
        for resolved_event in resolved_events:
            process = self._processes_by_event_type.get(type(resolved_event))
            if process is None:
                raise RuntimeError(
                    "No process is registered for resolved event type "
                    f"{type(resolved_event).__name__}."
                )
            if isinstance(process, EventMaterializer):
                materialized_event = process.materialize_event(
                    simulation_state,
                    resolved_event,
                )
            else:
                materialized_event = resolved_event
            materialized_events.append((process, materialized_event))

        applied_events: list[AppliedEvent] = []
        domain_state = simulation_state.world
        for process, materialized_event in materialized_events:
            checkpoint = _mutation_checkpoint(domain_state)
            process.apply_event(simulation_state, materialized_event)
            applied_events.append(
                AppliedEvent(
                    event_step_index=materialized_event.step_index,
                    stage_index=stage_index,
                    process_type=_qualified_type_name(process),
                    event_type=_qualified_type_name(materialized_event),
                    event=materialized_event,
                    effects=_mutations_since(domain_state, checkpoint),
                )
            )
        return tuple(applied_events)


def _mutation_checkpoint(domain_state: object) -> int | None:
    mutation_count = getattr(domain_state, "mutation_count", None)
    if mutation_count is None:
        return None
    if type(mutation_count) is not int or mutation_count < 0:
        raise TypeError("domain-state mutation_count must be a nonnegative integer.")
    return mutation_count


def _mutations_since(
    domain_state: object,
    checkpoint: int | None,
) -> tuple[Any, ...]:
    if checkpoint is None:
        return ()
    mutations_since = getattr(domain_state, "mutations_since", None)
    if not callable(mutations_since):
        raise TypeError(
            "domain state with mutation_count must provide callable mutations_since."
        )
    mutations = mutations_since(checkpoint)
    if type(mutations) is not tuple:
        raise TypeError("domain-state mutations_since must return a tuple.")
    return mutations


def _qualified_type_name(value: object) -> str:
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"
