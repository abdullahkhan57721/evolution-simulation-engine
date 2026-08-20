"""Run simulations until their stopping conditions are met."""

from __future__ import annotations

from evo_engine.engine.protocols import StepCoordinator, StoppingCondition
from evo_engine.engine.simulation import Simulation
from evo_engine.genetics.requirements import collect_required_traits


class SimulationEngine:
    """Coordinate the execution of simulations."""

    def __init__(
        self,
        step_coordinator: StepCoordinator,
        stopping_condition: StoppingCondition,
    ) -> None:
        """Initialize the simulation engine.

        Args:
            step_coordinator: Coordinator responsible for simulation steps.
            stopping_condition: Condition determining when a simulation ends.
        """
        self.step_coordinator = step_coordinator
        self.stopping_condition = stopping_condition
        self.required_traits = collect_required_traits(
            self.step_coordinator,
            self.stopping_condition,
        )

    def run(
        self,
        simulation: Simulation,
    ) -> None:
        """Run a simulation until its stopping condition is met.

        Genetic phenotype dependencies declared by configured components are validated
        against the simulation genetic architecture before step zero.

        Args:
            simulation: Simulation to run.

        Raises:
            ValueError: If a configured component requires an undefined
                genetic phenotype trait.
        """
        simulation.genetic_architecture.require_traits(
            self.required_traits,
            context="configured simulation engine",
        )

        while not self.stopping_condition.should_stop(
            simulation.state,
        ):
            simulation.state = self.step_coordinator.coordinate(
                simulation_state=simulation.state,
            )
