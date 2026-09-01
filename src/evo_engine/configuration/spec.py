"""Domain-neutral simulation specification and compilation boundary."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.configuration.dependencies import Dependency, DependencyReport
from evo_engine.context import SimulationContext
from evo_engine.engine import (
    Observer,
    Simulation,
    SimulationEngine,
    StepCoordinator,
    StoppingCondition,
)
from evo_engine.telemetry import TelemetryObserver


@attrs.frozen(slots=True, kw_only=True)
class CompiledSimulation:
    """Bundle a validated simulation and matching runtime engine."""

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
    """Describe a complete domain-neutral simulation before mutable runtime exists."""

    initial_domain_state: object
    step_coordinator: StepCoordinator
    stopping_condition: StoppingCondition
    seed: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(int)),
    )
    context: SimulationContext = attrs.field(factory=SimulationContext)
    observers: tuple[Observer, ...] = ()
    telemetry_observers: tuple[TelemetryObserver, ...] = ()
    required_dependencies: frozenset[Dependency] = frozenset()
    provided_dependencies: frozenset[Dependency] = frozenset()

    def __attrs_post_init__(self) -> None:
        """Validate structural runtime contracts and immutable collections."""
        if not callable(getattr(self.initial_domain_state, "copy", None)):
            raise TypeError("initial_domain_state must provide a callable copy method.")
        if type(self.seed) is bool:
            raise TypeError("seed must be an integer or None, not a Boolean.")
        if not callable(getattr(self.step_coordinator, "coordinate", None)):
            raise TypeError(
                "step_coordinator must provide a callable coordinate method."
            )
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
        if type(self.required_dependencies) is not frozenset:
            raise TypeError("required_dependencies must be a frozenset.")
        if type(self.provided_dependencies) is not frozenset:
            raise TypeError("provided_dependencies must be a frozenset.")

    @classmethod
    def from_iterables(
        cls,
        *,
        initial_domain_state: object,
        step_coordinator: StepCoordinator,
        stopping_condition: StoppingCondition,
        seed: int | None = None,
        context: SimulationContext | None = None,
        observers: Iterable[Observer] = (),
        telemetry_observers: Iterable[TelemetryObserver] = (),
        required_dependencies: Iterable[Dependency] = (),
        provided_dependencies: Iterable[Dependency] = (),
    ) -> SimulationSpec:
        """Build a specification while normalizing iterable inputs."""
        return cls(
            initial_domain_state=initial_domain_state,
            step_coordinator=step_coordinator,
            stopping_condition=stopping_condition,
            seed=seed,
            context=SimulationContext() if context is None else context,
            observers=tuple(observers),
            telemetry_observers=tuple(telemetry_observers),
            required_dependencies=frozenset(required_dependencies),
            provided_dependencies=frozenset(provided_dependencies),
        )

    def compile(self) -> CompiledSimulation:
        """Run generic preflight and create runnable runtime objects."""
        from evo_engine.configuration.validation import SimulationSpecValidator

        report = SimulationSpecValidator().validate(self)
        simulation = Simulation(
            initial_domain_state=self.initial_domain_state,
            seed=self.seed,
            context=self.context,
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
