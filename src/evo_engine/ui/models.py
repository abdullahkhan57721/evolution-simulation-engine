"""Build immutable presentation results from committed reference-ecology data."""

from __future__ import annotations

from collections import Counter

import attrs

from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch
from evo_engine.engine import Simulation
from evo_engine.experiments import (
    ReferenceExperimentResult,
    run_flagship_max_intake_replicates,
    run_reference_replicates,
)
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitRecorder,
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
from evo_engine.presets.reference_ecology.genetics import (
    build_balanced_reference_trait_world,
)
from evo_engine.telemetry import StepTelemetry

REFERENCE_SCENARIO = "reference_ecology"
FLAGSHIP_MAX_INTAKE_SCENARIO = "flagship_max_intake"
SCIENCE_AWARE_MAX_SPEED_SCENARIO = "science_aware_max_speed"
SCIENCE_AWARE_MAX_SPEED_SEED = 17
SCIENCE_AWARE_LOW_SPEED = 1
SCIENCE_AWARE_HIGH_SPEED = 4


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
    individual_trait_history: tuple[IndividualGeneticTraitObservation, ...] = (
        attrs.field(factory=tuple)
    )
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


def run_dashboard_reference(
    config: ReferenceEcologyConfig,
    *,
    individual_trait_names: tuple[str, ...] = (),
) -> DashboardRun:
    """Run the reference ecology and return immutable committed presentation data.

    Args:
        config: Validated reference-ecology configuration.
        individual_trait_names: Optional explicitly selected integer genetic-
            phenotype traits to record for active organisms at each committed step.

    Returns:
        Completed immutable dashboard result.
    """
    if not isinstance(config, ReferenceEcologyConfig):
        raise TypeError("config must be a ReferenceEcologyConfig.")

    spatial = SpatialRecorder(every_n_steps=1)
    individual_traits = _individual_trait_recorder(individual_trait_names)
    ecology = build_reference_ecology(
        config,
        additional_observers=_dashboard_observers(
            spatial=spatial,
            individual_traits=individual_traits,
        ),
    )
    return _run_dashboard_ecology(
        ecology,
        spatial=spatial,
        individual_traits=individual_traits,
        scenario=REFERENCE_SCENARIO,
    )


def run_dashboard_flagship_max_intake(
    *,
    individual_trait_names: tuple[str, ...] = (),
) -> DashboardRun:
    """Run the canonical flagship demo and return committed presentation data."""
    specification = build_flagship_max_intake_specification()
    spatial = SpatialRecorder(every_n_steps=1)
    individual_traits = _individual_trait_recorder(individual_trait_names)
    ecology = build_flagship_max_intake_ecology(
        specification,
        additional_observers=_dashboard_observers(
            spatial=spatial,
            individual_traits=individual_traits,
        ),
    )
    return _run_dashboard_ecology(
        ecology,
        spatial=spatial,
        individual_traits=individual_traits,
        scenario=FLAGSHIP_MAX_INTAKE_SCENARIO,
    )


def run_dashboard_science_aware_max_speed() -> DashboardRun:
    """Run a deterministic B1/B2 mechanism preview for interactive encoding.

    This is a presentation integration proof, not the final B3 treatment/control
    scenario. It composes existing patchy resources with balanced standing
    variation at the already-established speed-1/speed-4 performance tradeoff.
    """
    baseline = ReferenceEcologyConfig()
    config = attrs.evolve(
        baseline,
        width=12,
        height=12,
        initial_population=20,
        initial_energy=30,
        max_steps=30,
        seed=SCIENCE_AWARE_MAX_SPEED_SEED,
        mutation_probability_ppm=0,
        resource_generation_amount=6,
        resource_deposits_per_step=16,
        resource_placement_model=PatchyResourcePlacement(
            patches=(
                ResourcePatch(center_x=2, center_y=2, radius=2),
                ResourcePatch(center_x=9, center_y=9, radius=2),
            )
        ),
        mating_radius=1,
        traits=attrs.evolve(
            baseline.traits,
            attack_strength=0,
            defense=1,
        ),
    )
    spatial = SpatialRecorder(every_n_steps=1)
    individual_traits = IndividualGeneticTraitRecorder(trait_names=(MAX_SPEED,))
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial, individual_traits),
    )
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    founder_world = build_balanced_reference_trait_world(
        architecture,
        trait_name=MAX_SPEED,
        variant_values=(SCIENCE_AWARE_LOW_SPEED, SCIENCE_AWARE_HIGH_SPEED),
        config=config,
    )
    ecology = attrs.evolve(
        ecology,
        simulation=Simulation(
            initial_domain_state=founder_world,
            seed=config.seed,
            context=ecology.simulation.context,
        ),
    )
    return _run_dashboard_ecology(
        ecology,
        spatial=spatial,
        individual_traits=individual_traits,
        scenario=SCIENCE_AWARE_MAX_SPEED_SCENARIO,
    )


def _individual_trait_recorder(
    trait_names: tuple[str, ...],
) -> IndividualGeneticTraitRecorder | None:
    if not isinstance(trait_names, tuple):
        raise TypeError("individual_trait_names must be a tuple of trait names.")
    if not trait_names:
        return None
    return IndividualGeneticTraitRecorder(trait_names=trait_names)


def _dashboard_observers(
    *,
    spatial: SpatialRecorder,
    individual_traits: IndividualGeneticTraitRecorder | None,
) -> tuple[SpatialRecorder | IndividualGeneticTraitRecorder, ...]:
    if individual_traits is None:
        return (spatial,)
    return (spatial, individual_traits)


def _run_dashboard_ecology(
    ecology: ReferenceEcology,
    *,
    spatial: SpatialRecorder,
    individual_traits: IndividualGeneticTraitRecorder | None,
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
        individual_trait_history=(
            () if individual_traits is None else individual_traits.observations
        ),
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
