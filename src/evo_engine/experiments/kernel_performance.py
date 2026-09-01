"""Measure domain-neutral simulation-kernel execution overhead."""

from __future__ import annotations

import cProfile
import io
import pstats
from statistics import fmean, median
from time import perf_counter

import attrs

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    SimulationState,
    StageCoordinator,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class KernelPerformanceScenario:
    """Define one synthetic domain-neutral kernel performance scenario.

    Attributes:
        name: Stable scenario name used in reports.
        steps: Number of simulation steps to execute.
        events_per_step: Number of trivial events committed per step.
        journaled: Whether the minimal model state exposes effect journaling.
    """

    name: str
    steps: int
    events_per_step: int
    journaled: bool = False

    def __attrs_post_init__(self) -> None:
        """Validate benchmark dimensions."""
        validated_name = validators.validate_str(self.name, name="name")
        if not validated_name.strip():
            raise ValueError("name must not be empty or whitespace-only.")
        validators.validate_int_ge(self.steps, bound=1, name="steps")
        validators.validate_int_ge(
            self.events_per_step,
            bound=1,
            name="events_per_step",
        )
        validators.validate_bool(self.journaled, name="journaled")


@attrs.frozen(slots=True, kw_only=True)
class KernelRunOutcome:
    """Record deterministic dimensions from one synthetic kernel run."""

    completed_steps: int
    applied_events: int
    final_step_event_count: int


@attrs.frozen(slots=True, kw_only=True)
class KernelBenchmarkResult:
    """Store repeated wall-clock measurements for one kernel scenario."""

    scenario_name: str
    journaled: bool
    repeats: int
    warmups: int
    durations_seconds: tuple[float, ...]
    outcome: KernelRunOutcome

    @property
    def minimum_seconds(self) -> float:
        """Return the fastest measured repeat."""
        return min(self.durations_seconds)

    @property
    def median_seconds(self) -> float:
        """Return the median measured repeat."""
        return float(median(self.durations_seconds))

    @property
    def mean_seconds(self) -> float:
        """Return the arithmetic mean measured repeat."""
        return fmean(self.durations_seconds)

    @property
    def maximum_seconds(self) -> float:
        """Return the slowest measured repeat."""
        return max(self.durations_seconds)

    @property
    def median_seconds_per_event(self) -> float:
        """Return median runtime normalized by committed events."""
        if self.outcome.applied_events == 0:
            return 0.0
        return self.median_seconds / self.outcome.applied_events


@attrs.frozen(slots=True, kw_only=True)
class KernelProfileResult:
    """Store one cumulative-time cProfile report and deterministic outcome."""

    scenario_name: str
    journaled: bool
    report: str
    outcome: KernelRunOutcome


KERNEL_CORE_BASELINE = KernelPerformanceScenario(
    name="kernel-core",
    steps=50,
    events_per_step=100,
    journaled=False,
)
KERNEL_JOURNALED_BASELINE = KernelPerformanceScenario(
    name="kernel-journaled",
    steps=50,
    events_per_step=100,
    journaled=True,
)


def benchmark_kernel_scenario(
    scenario: KernelPerformanceScenario,
    *,
    repeats: int = 3,
    warmups: int = 1,
) -> KernelBenchmarkResult:
    """Benchmark simulation execution for a synthetic kernel scenario.

    Construction is excluded from timing. The synthetic model state and process
    deliberately perform only trivial deterministic work so orchestration costs
    remain visible without importing any modeled-domain package.
    """
    _validate_measurement_counts(repeats=repeats, warmups=warmups)

    for _ in range(warmups):
        prepared = _prepare_kernel_run(scenario)
        prepared.engine.run(prepared.simulation)

    durations: list[float] = []
    expected_outcome: KernelRunOutcome | None = None
    for _ in range(repeats):
        prepared = _prepare_kernel_run(scenario)
        started = perf_counter()
        prepared.engine.run(prepared.simulation)
        durations.append(perf_counter() - started)
        outcome = _kernel_outcome(prepared.simulation)
        if expected_outcome is None:
            expected_outcome = outcome
        elif outcome != expected_outcome:
            raise RuntimeError(
                "deterministic kernel performance scenario changed outcome."
            )

    if expected_outcome is None:
        raise RuntimeError("benchmark produced no measured outcome.")

    return KernelBenchmarkResult(
        scenario_name=scenario.name,
        journaled=scenario.journaled,
        repeats=repeats,
        warmups=warmups,
        durations_seconds=tuple(durations),
        outcome=expected_outcome,
    )


def profile_kernel_scenario(
    scenario: KernelPerformanceScenario,
    *,
    top_functions: int = 25,
    stats_path: str | None = None,
) -> KernelProfileResult:
    """Profile one synthetic kernel execution by cumulative time."""
    validators.validate_int_ge(top_functions, bound=1, name="top_functions")
    prepared = _prepare_kernel_run(scenario)
    profiler = cProfile.Profile()
    profiler.enable()
    prepared.engine.run(prepared.simulation)
    profiler.disable()

    if stats_path is not None:
        validated_path = validators.validate_str(stats_path, name="stats_path")
        if not validated_path.strip():
            raise ValueError("stats_path must not be empty or whitespace-only.")
        profiler.dump_stats(validated_path)

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_stats(top_functions)
    return KernelProfileResult(
        scenario_name=scenario.name,
        journaled=scenario.journaled,
        report=stream.getvalue(),
        outcome=_kernel_outcome(prepared.simulation),
    )


@attrs.define(slots=True, kw_only=True)
class _KernelState:
    """Minimal copyable non-journaled model state."""

    applied_events: int = 0

    def apply(self, effect: int) -> None:
        """Apply one trivial deterministic state transition."""
        self.applied_events += effect

    def copy(self) -> _KernelState:
        """Return an isolated transactional copy."""
        return _KernelState(applied_events=self.applied_events)


@attrs.define(slots=True, kw_only=True)
class _JournaledKernelState:
    """Minimal copyable model state with an effect journal."""

    applied_events: int = 0
    _mutations: list[int] = attrs.field(factory=list, repr=False)

    @property
    def mutation_count(self) -> int:
        """Return transaction-local journal length."""
        return len(self._mutations)

    def mutations_since(self, checkpoint: int) -> tuple[int, ...]:
        """Return effects recorded after a journal checkpoint."""
        return tuple(self._mutations[checkpoint:])

    def apply(self, effect: int) -> None:
        """Apply one trivial transition and record its opaque effect."""
        self.applied_events += effect
        self._mutations.append(effect)

    def copy(self) -> _JournaledKernelState:
        """Return an isolated copy with a fresh transaction journal."""
        return _JournaledKernelState(applied_events=self.applied_events)


@attrs.frozen(slots=True, kw_only=True)
class _KernelEvent:
    """Represent one trivial synthetic transition."""

    step_index: int
    effect: int = 1


@attrs.frozen(slots=True, kw_only=True)
class _KernelProcess:
    """Propose and apply fixed-count trivial transitions."""

    events_per_step: int

    @property
    def event_type(self) -> type[_KernelEvent]:
        """Return the synthetic event type."""
        return _KernelEvent

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[_KernelEvent]:
        """Propose the configured number of trivial events."""
        return [
            _KernelEvent(step_index=simulation_state.step_index)
            for _ in range(self.events_per_step)
        ]

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: _KernelEvent,
        /,
    ) -> None:
        """Apply one trivial event to the synthetic model state."""
        simulation_state.world.apply(event.effect)


@attrs.frozen(slots=True)
class _PreparedKernelRun:
    simulation: Simulation
    engine: SimulationEngine


def _prepare_kernel_run(
    scenario: KernelPerformanceScenario,
) -> _PreparedKernelRun:
    if not isinstance(scenario, KernelPerformanceScenario):
        raise TypeError("scenario must be a KernelPerformanceScenario.")

    world: _KernelState | _JournaledKernelState
    if scenario.journaled:
        world = _JournaledKernelState()
    else:
        world = _KernelState()

    process = _KernelProcess(events_per_step=scenario.events_per_step)
    stage = StageCoordinator(processes=(process,), resolver=AcceptAll())
    step_coordinator = SequentialStepCoordinator(stages=(stage,))
    engine = SimulationEngine(
        step_coordinator=step_coordinator,
        stopping_condition=MaxSteps(max_steps=scenario.steps),
    )
    return _PreparedKernelRun(
        simulation=Simulation(initial_world_state=world, seed=0),
        engine=engine,
    )


def _kernel_outcome(simulation: Simulation) -> KernelRunOutcome:
    state = simulation.state
    telemetry = state.last_step_telemetry
    final_event_count = 0 if telemetry is None else len(telemetry.events)
    return KernelRunOutcome(
        completed_steps=state.step_index,
        applied_events=state.world.applied_events,
        final_step_event_count=final_event_count,
    )


def _validate_measurement_counts(*, repeats: int, warmups: int) -> None:
    validators.validate_int_ge(repeats, bound=1, name="repeats")
    validators.validate_int_ge(warmups, bound=0, name="warmups")


__all__ = [
    "KERNEL_CORE_BASELINE",
    "KERNEL_JOURNALED_BASELINE",
    "KernelBenchmarkResult",
    "KernelPerformanceScenario",
    "KernelProfileResult",
    "KernelRunOutcome",
    "benchmark_kernel_scenario",
    "profile_kernel_scenario",
]
