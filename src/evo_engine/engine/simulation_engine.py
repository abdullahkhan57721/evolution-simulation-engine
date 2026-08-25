"""Run simulations until their stopping conditions are met."""

from __future__ import annotations

from collections.abc import Iterable

from evo_engine.engine.protocols import Observer, StepCoordinator, StoppingCondition
from evo_engine.engine.simulation import Simulation
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.telemetry import TelemetryObserver


class SimulationEngine:
    """Coordinate execution, state observation, and committed event telemetry."""

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
            observers: Optional observers of committed simulation states.
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

        self.required_traits = collect_required_traits(
            self.step_coordinator,
            self.stopping_condition,
            *self.observers,
            *self.telemetry_observers,
        )

    def run(self, simulation: Simulation) -> None:
        """Run a simulation until its stopping condition is met.

        Genetic phenotype dependencies declared by engine components, observers,
        telemetry observers, and shared simulation configuration are validated
        before step zero.

        State observers are offered the authoritative baseline and each committed
        post-step state. Telemetry observers are called only after a successful
        step commit and therefore never see events from a discarded working copy.

        Args:
            simulation: Simulation to run.

        Raises:
            ValueError: If a configured component requires an undefined
                genetic phenotype trait.
        """
        required_traits = self.required_traits | collect_required_traits(
            simulation.state.behavior_selection_model,
        )
        simulation.genetic_architecture.require_traits(
            required_traits,
            context="configured simulation engine and simulation",
        )

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
