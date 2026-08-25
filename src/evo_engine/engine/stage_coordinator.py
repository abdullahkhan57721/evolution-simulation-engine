"""Coordinate a simulation update stage."""

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
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.telemetry import AppliedEvent
from evo_engine.validation import validators


class StageCoordinator:
    """Coordinate one simulation update stage."""

    def __init__(
        self,
        processes: Sequence[Process[Any, Any]],
        resolver: Resolver,
    ) -> None:
        """Initialize an update stage.

        Args:
            processes: Simulation processes participating in the stage.
            resolver: Resolver for proposed events in the stage.

        Raises:
            ValueError: If multiple processes use the same proposed event type.
        """
        self.processes = tuple(processes)
        self.resolver = resolver
        self.required_traits = collect_required_traits(
            *self.processes,
            self.resolver,
        )

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
        """Coordinate one simulation update stage and return applied telemetry.

        All processes first propose events from the same starting state. The
        stage resolver selects the events that may occur. Every resolved event
        is then materialized before any event is applied, preserving stage
        simultaneity while allowing post-resolution work such as inheritance,
        mutation, recombination, or random placement. Processes without a
        ``materialize_event`` method are treated as already materialized.

        Materialized events are applied in resolver-returned order. Each
        successful application produces an immutable telemetry record containing
        the materialized event and structural world mutations caused by it.

        Args:
            simulation_state: Working simulation state to update.
            stage_index: Zero-based lifecycle stage index for telemetry.

        Returns:
            Applied event telemetry in resolver application order.

        Raises:
            RuntimeError: If a resolved event has no registered process.
        """
        validators.validate_int_ge(
            stage_index,
            bound=0,
            name="stage_index",
        )
        proposed_events: list[SimulationEvent] = []

        for process in self.processes:
            process_events = process.propose_events(simulation_state)
            proposed_events.extend(process_events)

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
        world = simulation_state.world

        for process, materialized_event in materialized_events:
            mutation_checkpoint = world.mutation_count
            process.apply_event(
                simulation_state,
                materialized_event,
            )
            applied_events.append(
                AppliedEvent(
                    event_step_index=materialized_event.step_index,
                    stage_index=stage_index,
                    process_type=_qualified_type_name(process),
                    event_type=_qualified_type_name(materialized_event),
                    event=materialized_event,
                    world_mutations=world.mutations_since(mutation_checkpoint),
                )
            )

        return tuple(applied_events)


def _qualified_type_name(value: object) -> str:
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"
