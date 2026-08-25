"""Typed simulation specification and compilation boundary."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.behavior import BehaviorSelectionModel, UnrestrictedBehavior
from evo_engine.engine import (
    Observer,
    Simulation,
    SimulationEngine,
    StepCoordinator,
    StoppingCondition,
)
from evo_engine.genetics import GeneticArchitecture
from evo_engine.telemetry import TelemetryObserver
from evo_engine.world import WorldState

from .dependencies import DependencyReport


@attrs.frozen(slots=True, kw_only=True)
class CompiledSimulation:
    """Bundle a validated simulation and engine produced from one specification.

    Attributes:
        simulation: Mutable simulation initialized from the validated spec.
        engine: Runtime engine matching the validated spec.
        dependency_report: Static dependency analysis performed at compilation.
    """

    simulation: Simulation = attrs.field(
        validator=attrs.validators.instance_of(Simulation),
    )
    engine: SimulationEngine = attrs.field(
        validator=attrs.validators.instance_of(SimulationEngine),
    )
    dependency_report: DependencyReport = attrs.field(
        validator=attrs.validators.instance_of(DependencyReport),
    )


@attrs.frozen(slots=True, kw_only=True)
class SimulationSpec:
    """Describe a complete biological simulation before mutable runtime exists.

    ``SimulationSpec`` is the configuration boundary for cross-component
    validation. Individual model constructors validate their own local values;
    compilation validates relationships among models, required capabilities,
    and initial biological state before creating a runnable simulation.

    Attributes:
        initial_world_state: Initial world supplied as configuration input.
        genetic_architecture: Shared biological heritable-state architecture.
        step_coordinator: Complete configured timestep coordinator.
        stopping_condition: Condition terminating the simulation.
        seed: Optional deterministic random seed.
        behavior_selection_model: Shared behavioral policy.
        observers: Observers of committed world states.
        telemetry_observers: Observers of committed event telemetry.
    """

    initial_world_state: WorldState = attrs.field(
        validator=attrs.validators.instance_of(WorldState),
    )
    genetic_architecture: GeneticArchitecture = attrs.field(
        validator=attrs.validators.instance_of(GeneticArchitecture),
    )
    step_coordinator: StepCoordinator
    stopping_condition: StoppingCondition
    seed: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(int)),
    )
    behavior_selection_model: BehaviorSelectionModel = attrs.field(
        factory=UnrestrictedBehavior,
        validator=attrs.validators.instance_of(BehaviorSelectionModel),
    )
    observers: tuple[Observer, ...] = ()
    telemetry_observers: tuple[TelemetryObserver, ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate structural component protocols and observer collections."""
        if type(self.seed) is bool:
            raise TypeError("seed must be an integer or None, not a Boolean.")
        if not callable(getattr(self.step_coordinator, "coordinate", None)):
            raise TypeError("step_coordinator must provide a callable coordinate method.")
        if not callable(getattr(self.stopping_condition, "should_stop", None)):
            raise TypeError(
                "stopping_condition must provide a callable should_stop method."
            )
        if type(self.observers) is not tuple:
            raise TypeError("observers must be a tuple.")
        for index, observer in enumerate(self.observers):
            if not isinstance(observer, Observer):
                raise TypeError(f"observers[{index}] must implement Observer.")
        if type(self.telemetry_observers) is not tuple:
            raise TypeError("telemetry_observers must be a tuple.")
        for index, observer in enumerate(self.telemetry_observers):
            if not isinstance(observer, TelemetryObserver):
                raise TypeError(
                    f"telemetry_observers[{index}] must implement TelemetryObserver."
                )

    @classmethod
    def from_iterables(
        cls,
        *,
        initial_world_state: WorldState,
        genetic_architecture: GeneticArchitecture,
        step_coordinator: StepCoordinator,
        stopping_condition: StoppingCondition,
        seed: int | None = None,
        behavior_selection_model: BehaviorSelectionModel | None = None,
        observers: Iterable[Observer] = (),
        telemetry_observers: Iterable[TelemetryObserver] = (),
    ) -> SimulationSpec:
        """Build a specification while normalizing observer iterables to tuples.

        Args:
            initial_world_state: Initial world supplied as configuration input.
            genetic_architecture: Shared biological genetic architecture.
            step_coordinator: Complete configured timestep coordinator.
            stopping_condition: Condition terminating the simulation.
            seed: Optional deterministic random seed.
            behavior_selection_model: Optional shared behavior policy.
            observers: State observers to attach to the compiled engine.
            telemetry_observers: Telemetry observers to attach to the engine.

        Returns:
            Immutable simulation specification.
        """
        kwargs: dict[str, object] = {
            "initial_world_state": initial_world_state,
            "genetic_architecture": genetic_architecture,
            "step_coordinator": step_coordinator,
            "stopping_condition": stopping_condition,
            "seed": seed,
            "observers": tuple(observers),
            "telemetry_observers": tuple(telemetry_observers),
        }
        if behavior_selection_model is not None:
            kwargs["behavior_selection_model"] = behavior_selection_model
        return cls(**kwargs)  # type: ignore[arg-type]

    def compile(self) -> CompiledSimulation:
        """Validate the complete object graph and create runnable runtime objects.

        Returns:
            Validated simulation, matching engine, and dependency report.

        Raises:
            ValueError: If cross-component dependencies or initial biological
                state are inconsistent.
        """
        from evo_engine.configuration.validation import SimulationSpecValidator

        report = SimulationSpecValidator().validate(self)
        simulation = Simulation(
            initial_world_state=self.initial_world_state,
            genetic_architecture=self.genetic_architecture,
            seed=self.seed,
            behavior_selection_model=self.behavior_selection_model,
        )
        engine = SimulationEngine(
            step_coordinator=self.step_coordinator,
            stopping_condition=self.stopping_condition,
            observers=self.observers,
            telemetry_observers=self.telemetry_observers,
        )
        return CompiledSimulation(
            simulation=simulation,
            engine=engine,
            dependency_report=report,
        )
