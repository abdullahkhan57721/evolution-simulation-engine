"""Run arbitrary simulations until their stopping conditions are met."""

from __future__ import annotations

from collections.abc import Iterable

from evo_engine.engine.protocols import Observer, StepCoordinator, StoppingCondition
from evo_engine.engine.simulation import Simulation
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.telemetry import TelemetryObserver


class SimulationEngine:
    """Coordinate domain-neutral execution, observation, and telemetry.

    Static domain validation belongs at configuration/compilation boundaries.
    The runtime engine deliberately knows nothing about biological traits,
    genetics, resources, organisms, or any other modeled-domain semantics.
    """

    def __init__(
        self,
        step_coordinator: StepCoordinator,
        stopping_condition: StoppingCondition,
        *,
        observers: Iterable[Observer] = (),
        telemetry_observers: Iterable[TelemetryObserver] = (),
    ) -> None:
        """Initialize the simulation engine.

        Args:
            step_coordinator: Coordinator responsible for simulation steps.
            stopping_condition: Condition determining when a simulation ends.
            observers: Optional observers of committed model states.
            telemetry_observers: Optional observers of committed event telemetry.

        Raises:
            TypeError: If an observer does not implement its required protocol.
        """
        self.step_coordinator = step_coordinator
        self.stopping_condition = stopping_condition
        self.observers = tuple(observers)
        self.telemetry_observers = tuple(telemetry_observers)

        for index, observer in enumerate(self.observers):
            if not isinstance(observer, Observer):
                raise TypeError(
                    f"observers[{index}] must implement Observer; "
                    f"received {observer!r}."
                )

        for index, observer in enumerate(self.telemetry_observers):
            if not isinstance(observer, TelemetryObserver):
                raise TypeError(
                    f"telemetry_observers[{index}] must implement TelemetryObserver; "
                    f"received {observer!r}."
                )

    def run(self, simulation: Simulation) -> None:
        """Run a compiled/configured simulation until its stopping condition.

        The engine assumes static configuration invariants have already been
        established by the domain's configuration compiler. Runtime processes
        remain responsible for state-dependent invariants that cannot be proven
        before execution.

        Args:
            simulation: Simulation to run.
        """
        self._observe(simulation.state)

        while not self.stopping_condition.should_stop(simulation.state):
            simulation.state = self.step_coordinator.coordinate(
                simulation_state=simulation.state,
            )
            self._observe_telemetry(simulation.state)
            self._observe(simulation.state)

    def _observe(self, simulation_state: SimulationState) -> None:
        for observer in self.observers:
            if observer.should_observe(
                simulation_state.world,
                step_index=simulation_state.step_index,
            ):
                observer.observe(
                    simulation_state.world,
                    step_index=simulation_state.step_index,
                )

    def _observe_telemetry(self, simulation_state: SimulationState) -> None:
        telemetry = simulation_state.last_step_telemetry
        if telemetry is None:
            return

        for observer in self.telemetry_observers:
            if observer.should_observe_telemetry(telemetry):
                observer.observe_telemetry(telemetry)
