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
    ) -> None:
        """Coordinate one simulation update stage.

        All processes first propose events from the same starting state. The
        stage resolver selects the events that may occur. Every resolved event
        is then materialized before any event is applied, preserving stage
        simultaneity while allowing post-resolution work such as inheritance,
        mutation, recombination, or random placement. Processes without a
        ``materialize_event`` method are treated as already materialized.

        Materialized events are applied in resolver-returned order.

        Args:
            simulation_state: Working simulation state to update.

        Raises:
            RuntimeError: If a resolved event has no registered process.
        """
        # Phase 1 — proposal. Every process observes the same pre-stage
        # world because nothing is applied until all proposals are resolved.
        proposed_events: list[SimulationEvent] = []

        for process in self.processes:
            process_events = process.propose_events(
                simulation_state,
            )
            proposed_events.extend(process_events)

        # Phase 2 — conflict resolution across the full proposal set.
        resolved_events = self.resolver.resolve_events(
            simulation_state=simulation_state,
            proposed_events=proposed_events,
        )

        # Phase 3 — materialize every accepted proposal before mutating the
        # world. This preserves stage simultaneity while allowing expensive or
        # stochastic details to be generated only for events that will occur.
        materialized_events: list[tuple[Process[Any, Any], SimulationEvent]] = []

        for resolved_event in resolved_events:
            process = self._processes_by_event_type.get(type(resolved_event))

            if process is None:
                raise RuntimeError(
                    "No process is registered for resolved event type "
                    f"{type(resolved_event).__name__}."
                )

            # Materialization is an optional process capability. Runtime
            # protocol checking keeps the coordinator independent of concrete
            # process classes while avoiding string-based reflection.
            if isinstance(process, EventMaterializer):
                materialized_event = process.materialize_event(
                    simulation_state,
                    resolved_event,
                )
            else:
                materialized_event = resolved_event

            materialized_events.append(
                (
                    process,
                    materialized_event,
                )
            )

        # Phase 4 — application is deliberately mechanical. Resolver order
        # is preserved because it may encode deterministic conflict outcomes.
        for process, materialized_event in materialized_events:
            process.apply_event(
                simulation_state,
                materialized_event,
            )
