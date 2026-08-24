"""Protocols for simulation engine components."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.world import WorldState


class SimulationEvent(Protocol):
    """Define the common interface for simulation events."""

    @property
    def step_index(self) -> int:
        """Return the simulation step associated with the event."""
        ...


ProposedEventT_co = TypeVar(
    "ProposedEventT_co",
    bound=SimulationEvent,
    covariant=True,
)
MaterializedEventT_contra = TypeVar(
    "MaterializedEventT_contra",
    bound=SimulationEvent,
    contravariant=True,
)
MaterializableEventT_contra = TypeVar(
    "MaterializableEventT_contra",
    bound=SimulationEvent,
    contravariant=True,
)
MaterializedEventT_co = TypeVar(
    "MaterializedEventT_co",
    bound=SimulationEvent,
    covariant=True,
)


class Process(Protocol[ProposedEventT_co, MaterializedEventT_contra]):
    """Define the interface for simulation processes.

    A process proposes events for resolution and applies materialized events.
    For processes that do not require post-resolution materialization, the
    proposed and applied event types may be the same.
    """

    @property
    def event_type(self) -> type[ProposedEventT_co]:
        """Return the proposed event type belonging to the process."""
        ...

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> Sequence[ProposedEventT_co]:
        """Propose events from simulation state."""
        ...

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: MaterializedEventT_contra,
        /,
    ) -> None:
        """Apply a materialized event to simulation state.

        The event parameter is positional-only in the protocol so concrete
        processes may use a more descriptive local name such as
        ``resolved_event`` or ``materialized_event`` without breaking
        structural typing.
        """
        ...


@runtime_checkable
class EventMaterializer(Protocol[MaterializableEventT_contra, MaterializedEventT_co]):
    """Define optional post-resolution event materialization."""

    def materialize_event(
        self,
        simulation_state: SimulationState,
        event: MaterializableEventT_contra,
        /,
    ) -> MaterializedEventT_co:
        """Materialize a resolved event before stage application begins."""
        ...


class Resolver(Protocol):
    """Define the interface for stage event resolvers."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> Sequence[SimulationEvent]:
        """Resolve proposed events for one simulation stage."""
        ...


class StepCoordinator(Protocol):
    """Define the interface for simulation step coordinators."""

    def coordinate(
        self,
        simulation_state: SimulationState,
    ) -> SimulationState:
        """Coordinate one simulation step."""
        ...


class StoppingCondition(Protocol):
    """Define the interface for simulation stopping conditions."""

    def should_stop(
        self,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the simulation should stop."""
        ...


@runtime_checkable
class Observer(Protocol):
    """Observe committed world state without participating in simulation updates.

    Observer implementations must treat ``world_state`` as read-only. The engine
    calls observers only for authoritative committed states, never for an
    in-progress transactional working copy.
    """

    def should_observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> bool:
        """Return whether the current committed state should be observed."""
        ...

    def observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> None:
        """Observe the current committed state without mutating it."""
        ...
