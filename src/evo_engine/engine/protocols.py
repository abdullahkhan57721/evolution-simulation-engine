"""Protocols for domain-neutral simulation engine components."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, TypeVar, runtime_checkable

from evo_engine.engine.simulation_state import SimulationState


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
ResolvedEventT_contra = TypeVar(
    "ResolvedEventT_contra",
    bound=SimulationEvent,
    contravariant=True,
)
MaterializedEventT_co = TypeVar(
    "MaterializedEventT_co",
    bound=SimulationEvent,
    covariant=True,
)


class Process(Protocol[ProposedEventT_co, MaterializedEventT_contra]):
    """Define one proposed/resolved/applied state-transition mechanism."""

    @property
    def event_type(self) -> type[ProposedEventT_co]:
        """Return the proposed event type belonging to the process."""
        ...

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> Sequence[ProposedEventT_co]:
        """Propose events from the current transactional state."""
        ...

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: MaterializedEventT_contra,
        /,
    ) -> None:
        """Apply a materialized event to simulation state."""
        ...


@runtime_checkable
class EventMaterializer(Protocol[ResolvedEventT_contra, MaterializedEventT_co]):
    """Define optional post-resolution event materialization."""

    def materialize_event(
        self,
        simulation_state: SimulationState,
        event: ResolvedEventT_contra,
        /,
    ) -> MaterializedEventT_co:
        """Materialize a resolved event before stage application begins."""
        ...


class Resolver(Protocol):
    """Resolve competing or incompatible proposed transitions."""

    def resolve_events(
        self,
        simulation_state: SimulationState,
        proposed_events: Sequence[SimulationEvent],
    ) -> Sequence[SimulationEvent]:
        """Resolve proposed events for one simulation stage."""
        ...


class StepCoordinator(Protocol):
    """Coordinate one complete simulation update step."""

    def coordinate(
        self,
        simulation_state: SimulationState,
    ) -> SimulationState:
        """Coordinate one simulation step."""
        ...


class StoppingCondition(Protocol):
    """Determine when a simulation run terminates."""

    def should_stop(
        self,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the simulation should stop."""
        ...


@runtime_checkable
class Observer(Protocol):
    """Observe committed domain state without participating in updates."""

    def should_observe(
        self,
        domain_state: Any,
        /,
        *,
        step_index: int,
    ) -> bool:
        """Return whether the current committed state should be observed."""
        ...

    def observe(
        self,
        domain_state: Any,
        /,
        *,
        step_index: int,
    ) -> None:
        """Observe the current committed state without mutating it."""
        ...
