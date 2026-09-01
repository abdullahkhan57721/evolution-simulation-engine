"""Measure reference-ecology runtime without imposing timing thresholds."""

from __future__ import annotations

import cProfile
import io
import pstats
from statistics import fmean, median
from time import perf_counter

import attrs

from evo_engine.engine import Simulation, SimulationEngine
from evo_engine.presets import (
    ReferenceEcologyConfig,
    build_reference_ecology,
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class ReferencePerformanceScenario:
    """Define one deterministic reference-ecology performance scenario.

    Attributes:
        name: Stable scenario name used in reports.
        config: Reference configuration executed by the scenario.
        observed: Whether to include the full reference observation stack.
    """

    name: str
    config: ReferenceEcologyConfig
    observed: bool = False

    def __attrs_post_init__(self) -> None:
        """Validate scenario configuration."""
        validated_name = validators.validate_str(self.name, name="name")
        if not validated_name.strip():
            raise ValueError("name must not be empty or whitespace-only.")
        if not isinstance(self.config, ReferenceEcologyConfig):
            raise TypeError("config must be a ReferenceEcologyConfig.")
        validators.validate_bool(self.observed, name="observed")


@attrs.frozen(slots=True, kw_only=True)
class ReferenceRunOutcome:
    """Record deterministic state dimensions from one measured run."""

    completed_steps: int
    final_population_size: int
    final_carcass_count: int
    final_total_resources: int


@attrs.frozen(slots=True, kw_only=True)
class ReferenceBenchmarkResult:
    """Store repeated wall-clock measurements for one scenario."""

    scenario_name: str
    observed: bool
    repeats: int
    warmups: int
    durations_seconds: tuple[float, ...]
    outcome: ReferenceRunOutcome

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
    def median_seconds_per_step(self) -> float:
        """Return median runtime normalized by completed simulation steps."""
        if self.outcome.completed_steps == 0:
            return 0.0
        return self.median_seconds / self.outcome.completed_steps


@attrs.frozen(slots=True, kw_only=True)
class ReferenceProfileResult:
    """Store one cumulative-time cProfile report and deterministic outcome."""

    scenario_name: str
    observed: bool
    report: str
    outcome: ReferenceRunOutcome


REFERENCE_CORE_BASELINE = ReferencePerformanceScenario(
    name="reference-core",
    config=ReferenceEcologyConfig(),
    observed=False,
)
REFERENCE_OBSERVED_BASELINE = ReferencePerformanceScenario(
    name="reference-observed",
    config=ReferenceEcologyConfig(),
    observed=True,
)


def benchmark_reference_scenario(
    scenario: ReferencePerformanceScenario,
    *,
    repeats: int = 3,
    warmups: int = 1,
) -> ReferenceBenchmarkResult:
    """Benchmark only simulation execution for a deterministic scenario.

    Runtime construction is intentionally excluded from timing. Each warmup and
    measured repeat receives a freshly constructed simulation so state mutation
    from earlier runs cannot affect later measurements.

    Args:
        scenario: Deterministic reference scenario to execute.
        repeats: Number of measured executions.
        warmups: Number of unmeasured executions performed first.

    Returns:
        Repeated wall-clock measurements and the common deterministic outcome.

    Raises:
        RuntimeError: If repeated executions do not produce the same outcome.
    """
    _validate_measurement_counts(repeats=repeats, warmups=warmups)

    for _ in range(warmups):
        prepared = _prepare_reference_run(scenario)
        prepared.engine.run(prepared.simulation)

    durations: list[float] = []
    expected_outcome: ReferenceRunOutcome | None = None

    for _ in range(repeats):
        prepared = _prepare_reference_run(scenario)
        started = perf_counter()
        prepared.engine.run(prepared.simulation)
        durations.append(perf_counter() - started)
        outcome = _reference_outcome(prepared.simulation)
        if expected_outcome is None:
            expected_outcome = outcome
        elif outcome != expected_outcome:
            raise RuntimeError("deterministic performance scenario changed outcome.")

    if expected_outcome is None:
        raise RuntimeError("benchmark produced no measured outcome.")

    return ReferenceBenchmarkResult(
        scenario_name=scenario.name,
        observed=scenario.observed,
        repeats=repeats,
        warmups=warmups,
        durations_seconds=tuple(durations),
        outcome=expected_outcome,
    )


def profile_reference_scenario(
    scenario: ReferencePerformanceScenario,
    *,
    top_functions: int = 25,
    stats_path: str | None = None,
) -> ReferenceProfileResult:
    """Profile one execution and report functions by cumulative time.

    Args:
        scenario: Deterministic reference scenario to execute.
        top_functions: Maximum number of profiler rows to print.
        stats_path: Optional destination for raw ``pstats`` data.

    Returns:
        Textual cumulative-time report and final deterministic outcome.
    """
    validators.validate_int_ge(top_functions, bound=1, name="top_functions")
    prepared = _prepare_reference_run(scenario)
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

    return ReferenceProfileResult(
        scenario_name=scenario.name,
        observed=scenario.observed,
        report=stream.getvalue(),
        outcome=_reference_outcome(prepared.simulation),
    )


@attrs.frozen(slots=True)
class _PreparedReferenceRun:
    simulation: Simulation
    engine: SimulationEngine


def _prepare_reference_run(
    scenario: ReferencePerformanceScenario,
) -> _PreparedReferenceRun:
    if not isinstance(scenario, ReferencePerformanceScenario):
        raise TypeError("scenario must be a ReferencePerformanceScenario.")

    if scenario.observed:
        ecology = build_reference_ecology(scenario.config)
        return _PreparedReferenceRun(ecology.simulation, ecology.engine)

    return _PreparedReferenceRun(
        build_reference_simulation(scenario.config),
        build_reference_engine(scenario.config),
    )


def _reference_outcome(simulation: Simulation) -> ReferenceRunOutcome:
    state = simulation.state
    world = state.domain_state
    return ReferenceRunOutcome(
        completed_steps=state.step_index,
        final_population_size=len(world.organisms),
        final_carcass_count=len(world.carcasses),
        final_total_resources=sum(world.resources.values()),
    )


def _validate_measurement_counts(*, repeats: int, warmups: int) -> None:
    validators.validate_int_ge(repeats, bound=1, name="repeats")
    validators.validate_int_ge(warmups, bound=0, name="warmups")
