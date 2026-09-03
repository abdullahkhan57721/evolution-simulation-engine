"""Build immutable presentation results from committed reference-ecology data."""

from __future__ import annotations

from collections import Counter

import attrs

from evo_engine.experiments import (
    ReferenceExperimentResult,
    run_flagship_max_intake_replicates,
    run_reference_replicates,
)
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
    SpatialRecorder,
)
from evo_engine.presets import (
    ReferenceEcology,
    ReferenceEcologyConfig,
    ReferenceExplorationMovement,
    ReferenceGaussianMovement,
    ReferenceMooreMovement,
    ReferenceUniformMovement,
    ReferenceVonNeumannMovement,
    build_flagship_max_intake_ecology,
    build_flagship_max_intake_specification,
    build_reference_ecology,
)
from evo_engine.telemetry import StepTelemetry

REFERENCE_SCENARIO = "reference_ecology"
FLAGSHIP_MAX_INTAKE_SCENARIO = "flagship_max_intake"


@attrs.frozen(slots=True, kw_only=True)
class DashboardRun:
    """Immutable committed data consumed by the portfolio dashboard.

    The value intentionally excludes the mutable simulation, engine, world, and
    recorder objects used to produce it. Streamlit session state can therefore
    retain a completed run without becoming an alternate owner of live simulation
    internals.
    """

    config: ReferenceEcologyConfig
    completed_steps: int
    population_history: tuple[PopulationObservation, ...]
    genetic_history: tuple[GeneticCompositionObservation, ...]
    spatial_history: tuple[SpatialObservation, ...]
    telemetry_steps: tuple[StepTelemetry, ...]
    life_histories: tuple[IndividualLifeHistory, ...]
    scenario: str = REFERENCE_SCENARIO

    @property
    def final_population_size(self) -> int:
        """Return the final committed active-population size."""
        if not self.population_history:
            return 0
        return self.population_history[-1].population_size

    @property
    def final_total_resources(self) -> int:
        """Return the final committed environmental resource total."""
        if not self.population_history:
            return 0
        return self.population_history[-1].total_resources

    @property
    def final_carcass_count(self) -> int:
        """Return the final committed carcass count."""
        if not self.population_history:
            return 0
        return self.population_history[-1].carcass_count

    @property
    def total_births(self) -> int:
        """Return observed biological births after the founder baseline."""
        return sum(not history.is_founder for history in self.life_histories)

    @property
    def total_deaths(self) -> int:
        """Return observed biological deaths."""
        return sum(not history.is_alive for history in self.life_histories)

    @property
    def event_counts(self) -> tuple[tuple[str, int], ...]:
        """Return committed event counts by producing process name."""
        counts = Counter(
            event.process_name for step in self.telemetry_steps for event in step.events
        )
        return tuple(sorted(counts.items()))


def build_curated_config(
    *,
    seed: int = 42,
    max_steps: int = 50,
    initial_population: int = 20,
    width: int = 12,
    height: int = 12,
    initial_energy: int = 30,
    exploration_movement_kind: str = "moore",
    gaussian_standard_deviation: int | None = None,
    mutation_enabled: bool = True,
    mutation_percent: int | None = 1,
    mutation_max_change: int | None = 1,
    recombination_enabled: bool = True,
    recombination_percent: int | None = 50,
    resource_generation_amount: int = 6,
    resource_deposits_per_step: int = 8,
    growth_rate: int = 1,
) -> ReferenceEcologyConfig:
    """Build the validated reference configuration exposed by the dashboard.

    Conditional UI branches normalize into one real ``ReferenceEcologyConfig``.
    Dependent values are validated only while their branch is active. Inactive
    values are ignored so stale Streamlit widget state cannot affect the built
    simulation. Percentage controls are converted to the engine's existing integer
    parts-per-million contracts rather than introducing a second simulation
    configuration format.
    """
    exploration_movement = _normalize_exploration_movement(
        kind=exploration_movement_kind,
        gaussian_standard_deviation=gaussian_standard_deviation,
    )

    if type(mutation_enabled) is not bool:
        raise TypeError("mutation_enabled must be a Boolean.")
    if type(recombination_enabled) is not bool:
        raise TypeError("recombination_enabled must be a Boolean.")

    if mutation_enabled:
        if type(mutation_percent) is not int or not 0 <= mutation_percent <= 100:
            raise ValueError(
                "mutation_percent must be an integer from 0 through 100 when "
                "mutation is enabled."
            )
        if type(mutation_max_change) is not int or mutation_max_change < 0:
            raise ValueError(
                "mutation_max_change must be a non-negative integer when mutation "
                "is enabled."
            )
        normalized_mutation_percent = mutation_percent
        normalized_mutation_max_change = mutation_max_change
    else:
        normalized_mutation_percent = 0
        normalized_mutation_max_change = 0

    if recombination_enabled:
        if (
            type(recombination_percent) is not int
            or not 0 <= recombination_percent <= 100
        ):
            raise ValueError(
                "recombination_percent must be an integer from 0 through 100 when "
                "recombination is enabled."
            )
        normalized_recombination_percent = recombination_percent
    else:
        normalized_recombination_percent = 0

    baseline = ReferenceEcologyConfig()
    return attrs.evolve(
        baseline,
        seed=seed,
        max_steps=max_steps,
        initial_population=initial_population,
        width=width,
        height=height,
        initial_energy=initial_energy,
        exploration_movement=exploration_movement,
        mutation_probability_ppm=normalized_mutation_percent * 10_000,
        mutation_max_change=normalized_mutation_max_change,
        recombination_probability_ppm=normalized_recombination_percent * 10_000,
        resource_generation_amount=resource_generation_amount,
        resource_deposits_per_step=resource_deposits_per_step,
        traits=attrs.evolve(baseline.traits, growth_rate=growth_rate),
    )


def _normalize_exploration_movement(
    *,
    kind: str,
    gaussian_standard_deviation: int | None,
) -> ReferenceExplorationMovement:
    if kind == "moore":
        return ReferenceMooreMovement()
    if kind == "von_neumann":
        return ReferenceVonNeumannMovement()
    if kind == "uniform":
        return ReferenceUniformMovement()
    if kind == "gaussian":
        if (
            type(gaussian_standard_deviation) is not int
            or gaussian_standard_deviation < 0
        ):
            raise ValueError(
                "gaussian_standard_deviation must be a non-negative integer when "
                "Gaussian exploration movement is selected."
            )
        return ReferenceGaussianMovement(
            standard_deviation=gaussian_standard_deviation,
        )
    raise ValueError(
        "exploration_movement_kind must be one of: moore, von_neumann, uniform, "
        "gaussian."
    )


def run_dashboard_reference(config: ReferenceEcologyConfig) -> DashboardRun:
    """Run the existing reference ecology and return committed presentation data."""
    if not isinstance(config, ReferenceEcologyConfig):
        raise TypeError("config must be a ReferenceEcologyConfig.")

    spatial = SpatialRecorder(every_n_steps=1)
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial,),
    )
    return _run_dashboard_ecology(
        ecology,
        spatial=spatial,
        scenario=REFERENCE_SCENARIO,
    )


def run_dashboard_flagship_max_intake() -> DashboardRun:
    """Run the canonical flagship demo and return committed presentation data."""
    specification = build_flagship_max_intake_specification()
    spatial = SpatialRecorder(every_n_steps=1)
    ecology = build_flagship_max_intake_ecology(
        specification,
        additional_observers=(spatial,),
    )
    return _run_dashboard_ecology(
        ecology,
        spatial=spatial,
        scenario=FLAGSHIP_MAX_INTAKE_SCENARIO,
    )


def _run_dashboard_ecology(
    ecology: ReferenceEcology,
    *,
    spatial: SpatialRecorder,
    scenario: str,
) -> DashboardRun:
    ecology.engine.run(ecology.simulation)
    return DashboardRun(
        config=ecology.config,
        completed_steps=ecology.simulation.state.step_index,
        population_history=ecology.recorder.observations,
        genetic_history=ecology.genetic_recorder.observations,
        spatial_history=spatial.observations,
        telemetry_steps=ecology.event_recorder.steps,
        life_histories=ecology.pedigree_recorder.records,
        scenario=scenario,
    )


def run_dashboard_experiment(
    config: ReferenceEcologyConfig,
    *,
    seeds: tuple[int, ...],
    scenario: str = REFERENCE_SCENARIO,
) -> ReferenceExperimentResult:
    """Run a multi-seed experiment through the existing experiment APIs."""
    if not isinstance(config, ReferenceEcologyConfig):
        raise TypeError("config must be a ReferenceEcologyConfig.")
    if scenario == FLAGSHIP_MAX_INTAKE_SCENARIO:
        return run_flagship_max_intake_replicates(seeds=seeds)
    if scenario == REFERENCE_SCENARIO:
        return run_reference_replicates(config, seeds=seeds)
    raise ValueError(f"Unsupported dashboard scenario: {scenario!r}.")


def parse_seed_list(value: str) -> tuple[int, ...]:
    """Parse a comma-separated unique seed list for the experiment control."""
    if not isinstance(value, str):
        raise TypeError("seed list must be a string.")
    pieces = tuple(piece.strip() for piece in value.split(",") if piece.strip())
    if not pieces:
        raise ValueError("Enter at least one integer seed.")
    try:
        seeds = tuple(int(piece) for piece in pieces)
    except ValueError as exc:
        raise ValueError("Seeds must be comma-separated integers.") from exc
    if len(seeds) != len(set(seeds)):
        raise ValueError("Seeds must be unique.")
    if len(seeds) > 8:
        raise ValueError("Use at most 8 seeds in the interactive dashboard.")
    return seeds
