"""Controlled E7 mutation-driven adaptation and convergence experiment."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

import attrs

from evo_engine.experiments.e3_performance import (
    E3_BODY_MASS,
    E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
    E3_FOUNDER_X,
    E3_FOUNDER_Y,
    E3_HEIGHT,
    E3_INITIAL_ENERGY,
    E3_LOCOMOTION_DISTANCE_EXPONENT,
    E3_REPRODUCTION_ENERGY_INVESTMENT,
    E3_REPRODUCTION_MINIMUM_ENERGY,
    E3_RESOURCE_REQUEST_AMOUNT,
    E3_WIDTH,
    build_e3_treatment,
)
from evo_engine.experiments.locomotion import measure_applied_movement
from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    RunRole,
    ScientificRunProvenance,
    canonical_treatment_specification,
)
from evo_engine.genetics import MAX_SPEED, UniformIntegerMutation
from evo_engine.observation import (
    EventRecorder,
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitRecorder,
    PedigreeRecorder,
    PopulationObservation,
    PopulationRecorder,
)
from evo_engine.presets.controlled_locomotion import (
    CONTROLLED_MAX_SPEED_MAXIMUM,
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.processes import Movement, ResourceConsumption
from evo_engine.validation import attrs_validators, validators

E7_STARTING_SPEEDS: tuple[int, int, int] = (1, 3, 7)
E7_DISCOVERY_SEEDS: tuple[int, ...] = (13, 31, 47, 73, 101, 127)
E7_CONFIRMATION_SEEDS: tuple[int, ...] = (
    677,
    683,
    691,
    701,
    709,
    719,
    727,
    733,
    739,
    743,
    751,
    757,
    761,
    769,
    773,
    787,
    797,
    809,
    811,
    821,
    823,
    827,
    829,
    839,
)
E7_FOUNDER_COUNT = 8
E7_RESOURCE_PER_FOUNDER = 420
E7_HORIZON = 60
E7_MUTATION_PROBABILITY_PPM = 1_000_000
E7_MUTATION_MAX_CHANGE = 1
E7_REFERENCE_REGION: tuple[int, int, int] = (2, 3, 4)
E7_SPEED_DOMAIN: tuple[int, ...] = tuple(range(CONTROLLED_MAX_SPEED_MAXIMUM + 1))


@attrs.frozen(slots=True, kw_only=True)
class E7TreatmentSpecification:
    """Define one monomorphic starting condition and explicit focal mutation assay."""

    starting_speed: int
    founder_count: int = attrs.field(
        default=E7_FOUNDER_COUNT,
        validator=attrs_validators.validate_int_ge(1),
    )
    resource_per_founder: int = attrs.field(
        default=E7_RESOURCE_PER_FOUNDER,
        validator=attrs_validators.validate_int_ge(1),
    )
    horizon: int = attrs.field(
        default=E7_HORIZON,
        validator=attrs_validators.validate_int_ge(1),
    )
    mutation_probability_ppm: int = attrs.field(
        default=E7_MUTATION_PROBABILITY_PPM,
        validator=attrs_validators.validate_int_in_range(0, 1_000_000),
    )
    mutation_max_change: int = attrs.field(
        default=E7_MUTATION_MAX_CHANGE,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate the predeclared E7 focal starting condition and resource split."""
        validators.validate_int(self.starting_speed, name="starting_speed")
        if self.starting_speed not in E7_STARTING_SPEEDS:
            raise ValueError(f"starting_speed must be one of {E7_STARTING_SPEEDS!r}.")
        if self.total_resources % 4 != 0:
            raise ValueError(
                "founder_count * resource_per_founder must divide equally across "
                "the four E3 corridor deposits."
            )
        if self.mutation_max_change != 1:
            raise ValueError("E7 mutation_max_change is frozen at exactly 1.")

    @property
    def treatment_id(self) -> str:
        """Return a stable treatment identity including mutation-supply settings."""
        return (
            f"separated-corridor-start-{self.starting_speed}"
            f"-n-{self.founder_count}-resource-{self.resource_per_founder}"
            f"-h-{self.horizon}-mutation-{self.mutation_probability_ppm}ppm-step-1"
        )

    @property
    def total_resources(self) -> int:
        """Return the explicit initial resource budget."""
        return self.founder_count * self.resource_per_founder

    @property
    def resource_deposits(self) -> tuple[tuple[int, int, int], ...]:
        """Return E3 corridor coordinates with the E7 per-founder resource scale."""
        amount = self.total_resources // 4
        corridor = build_e3_treatment(
            max_speed=3,
            environment="separated_corridor",
        ).resource_deposits
        return tuple((x, y, amount) for x, y, _ in corridor)

    @property
    def mutation_policy(self) -> UniformIntegerMutation:
        """Return the explicit one-locus E7 integer mutation policy."""
        return UniformIntegerMutation(
            probability_ppm=self.mutation_probability_ppm,
            max_change=self.mutation_max_change,
        )

    def to_config(self, *, seed: int) -> ControlledLocomotionConfig:
        """Build one controlled E2 configuration with only E7 declared changes."""
        validators.validate_int(seed, name="seed")
        return ControlledLocomotionConfig(
            width=E3_WIDTH,
            height=E3_HEIGHT,
            max_steps=self.horizon,
            seed=seed,
            founders=tuple(
                ControlledLocomotionFounder(
                    max_speed=self.starting_speed,
                    x=E3_FOUNDER_X,
                    y=E3_FOUNDER_Y,
                )
                for _ in range(self.founder_count)
            ),
            resource_deposits=tuple(
                ControlledResourceDeposit(x=x, y=y, amount=amount)
                for x, y, amount in self.resource_deposits
            ),
            initial_energy=E3_INITIAL_ENERGY,
            body_mass=E3_BODY_MASS,
            locomotion_cost_coefficient=E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
            locomotion_distance_exponent=E3_LOCOMOTION_DISTANCE_EXPONENT,
            resource_request_amount=E3_RESOURCE_REQUEST_AMOUNT,
            reproduction_minimum_energy=E3_REPRODUCTION_MINIMUM_ENERGY,
            reproduction_energy_investment=E3_REPRODUCTION_ENERGY_INVESTMENT,
        )


@attrs.frozen(slots=True, kw_only=True)
class E7TraitDistributionPoint:
    """Store the full committed `max_speed` distribution at one state index."""

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    counts: tuple[int, ...]
    frequencies: tuple[float | None, ...]
    total_population_energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    total_resources: int = attrs.field(validator=attrs_validators.validate_int_ge(0))

    def __attrs_post_init__(self) -> None:
        """Validate complete-domain counts and explicit extinction semantics."""
        _validate_distribution_shape(self)
        if self.population_size == 0:
            _validate_extinct_distribution(self)
        else:
            _validate_living_distribution(self)

    def count(self, max_speed: int) -> int:
        """Return the committed count at one legal focal speed."""
        _validate_legal_speed(max_speed)
        return self.counts[max_speed]

    def frequency(self, max_speed: int) -> float | None:
        """Return the committed frequency at one legal focal speed."""
        _validate_legal_speed(max_speed)
        return self.frequencies[max_speed]

    @property
    def mean_speed(self) -> float | None:
        """Return the secondary population-mean location summary."""
        if self.population_size == 0:
            return None
        return (
            sum(speed * count for speed, count in enumerate(self.counts))
            / self.population_size
        )

    @property
    def median_speed(self) -> float | None:
        """Return the population median derived from the full integer distribution."""
        if self.population_size == 0:
            return None
        lower_rank = (self.population_size - 1) // 2
        upper_rank = self.population_size // 2
        cumulative = 0
        lower_value: int | None = None
        for speed, count in enumerate(self.counts):
            cumulative += count
            if lower_value is None and cumulative > lower_rank:
                lower_value = speed
            if cumulative > upper_rank:
                if lower_value is None:
                    raise AssertionError("median lower value must be resolved first.")
                return (lower_value + speed) / 2
        raise AssertionError("nonempty distribution must resolve a median.")

    @property
    def reference_region_frequency(self) -> float | None:
        """Return population mass in the predeclared E3–E6 reference region 2..4."""
        if self.population_size == 0:
            return None
        return (
            sum(self.count(speed) for speed in E7_REFERENCE_REGION)
            / self.population_size
        )

    @property
    def boundary_frequency(self) -> float | None:
        """Return combined mass at the lower and upper legal speed boundaries."""
        if self.population_size == 0:
            return None
        return (
            self.count(0) + self.count(CONTROLLED_MAX_SPEED_MAXIMUM)
        ) / self.population_size

    @property
    def modal_speeds(self) -> tuple[int, ...]:
        """Return all tied modal speeds, or an empty tuple after extinction."""
        if self.population_size == 0:
            return ()
        maximum_count = max(self.counts)
        return tuple(
            speed for speed, count in enumerate(self.counts) if count == maximum_count
        )

    @property
    def occupied_support(self) -> tuple[int, int] | None:
        """Return minimum/maximum occupied speed, or None after extinction."""
        occupied = tuple(speed for speed, count in enumerate(self.counts) if count)
        if not occupied:
            return None
        return (occupied[0], occupied[-1])


@attrs.frozen(slots=True, kw_only=True)
class E7MutationTransition:
    """Count committed parent-to-offspring focal inheritance transitions."""

    parent_speed: int
    offspring_speed: int
    count: int = attrs.field(validator=attrs_validators.validate_int_ge(1))

    def __attrs_post_init__(self) -> None:
        """Validate legal focal values and declared E7 step size."""
        _validate_legal_speed(self.parent_speed)
        _validate_legal_speed(self.offspring_speed)
        if abs(self.offspring_speed - self.parent_speed) > E7_MUTATION_MAX_CHANGE:
            raise ValueError(
                "observed focal inheritance change exceeds E7 max_change=1."
            )

    @property
    def changed(self) -> bool:
        """Return whether the committed offspring differs from its genetic parent."""
        return self.parent_speed != self.offspring_speed


@attrs.frozen(slots=True, kw_only=True)
class E7SpeedMechanismEvidence:
    """Store speed-specific ecological mechanism evidence for one replicate."""

    max_speed: int
    applied_movement_count: int = 0
    total_realized_distance: float = 0.0
    total_locomotion_energy_expenditure: int = 0
    total_resource_consumed: int = 0
    cumulative_birth_count: int = 0

    def __attrs_post_init__(self) -> None:
        """Validate one legal speed and nonnegative evidence totals."""
        _validate_legal_speed(self.max_speed)
        validators.validate_int_ge(
            self.applied_movement_count,
            bound=0,
            name="applied_movement_count",
        )
        if self.total_realized_distance < 0.0 or not math.isfinite(
            self.total_realized_distance
        ):
            raise ValueError("total_realized_distance must be finite and nonnegative.")
        validators.validate_int_ge(
            self.total_locomotion_energy_expenditure,
            bound=0,
            name="total_locomotion_energy_expenditure",
        )
        validators.validate_int_ge(
            self.total_resource_consumed,
            bound=0,
            name="total_resource_consumed",
        )
        validators.validate_int_ge(
            self.cumulative_birth_count,
            bound=0,
            name="cumulative_birth_count",
        )


@attrs.frozen(slots=True, kw_only=True)
class E7ReplicateOutcome:
    """Store one run-level mutation-driven evolutionary trajectory and diagnostics."""

    treatment: E7TreatmentSpecification
    provenance: ScientificRunProvenance
    trait_trajectory: tuple[E7TraitDistributionPoint, ...]
    mutation_transitions: tuple[E7MutationTransition, ...]
    mechanisms: tuple[E7SpeedMechanismEvidence, ...]
    extinction: FixedHorizonTimeToEvent

    def __attrs_post_init__(self) -> None:
        """Validate complete state coverage and deterministic mechanism ordering."""
        if not isinstance(self.treatment, E7TreatmentSpecification):
            raise TypeError("treatment must be an E7TreatmentSpecification.")
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        validators.validate_tuple(self.trait_trajectory, name="trait_trajectory")
        if not self.trait_trajectory:
            raise ValueError("trait_trajectory must include committed step zero.")
        expected_steps = tuple(range(self.treatment.horizon + 1))
        observed_steps = tuple(point.step_index for point in self.trait_trajectory)
        if observed_steps != expected_steps:
            raise ValueError("trait_trajectory must contain every committed E7 step.")
        validators.validate_tuple(
            self.mutation_transitions,
            name="mutation_transitions",
        )
        validators.validate_tuple(self.mechanisms, name="mechanisms")
        if tuple(item.max_speed for item in self.mechanisms) != E7_SPEED_DOMAIN:
            raise ValueError("mechanisms must follow the complete legal speed domain.")
        if not isinstance(self.extinction, FixedHorizonTimeToEvent):
            raise TypeError("extinction must be a FixedHorizonTimeToEvent.")

    @property
    def initial_distribution(self) -> E7TraitDistributionPoint:
        """Return the founder baseline distribution."""
        return self.trait_trajectory[0]

    @property
    def final_distribution(self) -> E7TraitDistributionPoint:
        """Return the fixed-horizon endpoint distribution."""
        return self.trait_trajectory[-1]

    @property
    def realized_mutation_count(self) -> int:
        """Return observed births whose focal value differs from their parent."""
        return sum(item.count for item in self.mutation_transitions if item.changed)

    @property
    def birth_count(self) -> int:
        """Return total committed births represented by pedigree transitions."""
        return sum(item.count for item in self.mutation_transitions)


@attrs.frozen(slots=True, kw_only=True)
class E7StartingConditionSummary:
    """Summarize equal-run-weighted endpoints for one monomorphic starting speed."""

    starting_speed: int
    replicate_count: int
    seeds: tuple[int, ...]
    defined_endpoint_count: int
    extinction_count: int
    mean_final_mean_speed: float | None
    mean_final_median_speed: float | None
    mean_reference_region_frequency: float | None
    mean_boundary_frequency: float | None
    mean_realized_mutation_count: float
    endpoint_distribution: tuple[float | None, ...]

    def __attrs_post_init__(self) -> None:
        """Validate summary identity and full-domain endpoint distribution."""
        if self.starting_speed not in E7_STARTING_SPEEDS:
            raise ValueError("starting_speed must be a predeclared E7 start.")
        validators.validate_int_ge(
            self.replicate_count, bound=1, name="replicate_count"
        )
        validators.validate_int_ge(
            self.defined_endpoint_count,
            bound=0,
            name="defined_endpoint_count",
        )
        validators.validate_int_ge(
            self.extinction_count, bound=0, name="extinction_count"
        )
        if self.defined_endpoint_count + self.extinction_count != self.replicate_count:
            raise ValueError(
                "defined endpoints plus extinctions must equal replicates."
            )
        if len(self.endpoint_distribution) != len(E7_SPEED_DOMAIN):
            raise ValueError("endpoint_distribution must cover every legal speed.")


def build_e7_treatment(
    *,
    starting_speed: int,
    founder_count: int = E7_FOUNDER_COUNT,
    resource_per_founder: int = E7_RESOURCE_PER_FOUNDER,
    horizon: int = E7_HORIZON,
    mutation_probability_ppm: int = E7_MUTATION_PROBABILITY_PPM,
) -> E7TreatmentSpecification:
    """Build one predeclared E7 starting-condition treatment."""
    return E7TreatmentSpecification(
        starting_speed=starting_speed,
        founder_count=founder_count,
        resource_per_founder=resource_per_founder,
        horizon=horizon,
        mutation_probability_ppm=mutation_probability_ppm,
    )


def run_e7_replicate(
    treatment: E7TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None = "confirmation",
) -> E7ReplicateOutcome:
    """Run one E7 replicate and derive all outcomes from committed evidence."""
    if not isinstance(treatment, E7TreatmentSpecification):
        raise TypeError("treatment must be an E7TreatmentSpecification.")
    validators.validate_int(seed, name="seed")

    trait_recorder = IndividualGeneticTraitRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=True,
    )
    population_recorder = PopulationRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=True,
    )
    event_recorder = EventRecorder()
    pedigree_recorder = PedigreeRecorder()
    spec = build_controlled_locomotion_spec(
        treatment.to_config(seed=seed),
        observers=(trait_recorder, population_recorder, pedigree_recorder),
        telemetry_observers=(event_recorder, pedigree_recorder),
        max_speed_mutation=treatment.mutation_policy,
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)

    trait_observations = trait_recorder.observations
    population_observations = population_recorder.observations
    _validate_observation_alignment(
        trait_observations,
        population_observations,
        horizon=treatment.horizon,
    )
    traits_by_step = _build_trait_lookup(trait_observations)
    trajectory = tuple(
        _build_distribution_point(trait_observation, population_observation)
        for trait_observation, population_observation in zip(
            trait_observations,
            population_observations,
            strict=True,
        )
    )
    transitions = _derive_mutation_transitions(
        pedigree_recorder,
        traits_by_step=traits_by_step,
    )
    mechanisms = _derive_mechanisms(
        event_recorder,
        transitions=transitions,
        traits_by_step=traits_by_step,
    )
    return E7ReplicateOutcome(
        treatment=treatment,
        provenance=_build_provenance(
            treatment,
            seed=seed,
            run_role=run_role,
        ),
        trait_trajectory=trajectory,
        mutation_transitions=transitions,
        mechanisms=mechanisms,
        extinction=_extinction_outcome(trajectory, horizon=treatment.horizon),
    )


def run_e7_seed_set(
    treatment: E7TreatmentSpecification,
    *,
    seeds: Sequence[int],
    run_role: RunRole | None,
) -> tuple[E7ReplicateOutcome, ...]:
    """Run one E7 starting condition over independent seed-level replicates."""
    validators.validate_tuple(tuple(seeds), name="seeds")
    return tuple(
        run_e7_replicate(treatment, seed=seed, run_role=run_role) for seed in seeds
    )


def summarize_e7_starting_condition(
    outcomes: Sequence[E7ReplicateOutcome],
) -> E7StartingConditionSummary:
    """Summarize endpoint distributions with equal weight per run/seed."""
    runs = tuple(outcomes)
    if not runs:
        raise ValueError("outcomes must contain at least one E7 replicate.")
    starting_speed = runs[0].treatment.starting_speed
    if any(run.treatment.starting_speed != starting_speed for run in runs):
        raise ValueError("all outcomes must share one E7 starting speed.")

    defined = tuple(run for run in runs if run.final_distribution.population_size > 0)
    endpoint_distribution: tuple[float | None, ...]
    if defined:
        endpoint_distribution = tuple(
            sum(_defined_frequency(run.final_distribution, speed) for run in defined)
            / len(defined)
            for speed in E7_SPEED_DOMAIN
        )
    else:
        endpoint_distribution = tuple(None for _ in E7_SPEED_DOMAIN)

    return E7StartingConditionSummary(
        starting_speed=starting_speed,
        replicate_count=len(runs),
        seeds=tuple(run.provenance.seed for run in runs),
        defined_endpoint_count=len(defined),
        extinction_count=len(runs) - len(defined),
        mean_final_mean_speed=_mean_optional(
            tuple(run.final_distribution.mean_speed for run in runs)
        ),
        mean_final_median_speed=_mean_optional(
            tuple(run.final_distribution.median_speed for run in runs)
        ),
        mean_reference_region_frequency=_mean_optional(
            tuple(run.final_distribution.reference_region_frequency for run in runs)
        ),
        mean_boundary_frequency=_mean_optional(
            tuple(run.final_distribution.boundary_frequency for run in runs)
        ),
        mean_realized_mutation_count=(
            sum(run.realized_mutation_count for run in runs) / len(runs)
        ),
        endpoint_distribution=endpoint_distribution,
    )


def e7_distribution_overlap(
    left: E7StartingConditionSummary,
    right: E7StartingConditionSummary,
) -> float | None:
    """Return simple equal-run endpoint distribution overlap in [0, 1]."""
    if not isinstance(left, E7StartingConditionSummary) or not isinstance(
        right,
        E7StartingConditionSummary,
    ):
        raise TypeError("left and right must be E7StartingConditionSummary values.")
    left_distribution = _defined_endpoint_distribution(left)
    right_distribution = _defined_endpoint_distribution(right)
    if left_distribution is None or right_distribution is None:
        return None
    return sum(
        min(left_value, right_value)
        for left_value, right_value in zip(
            left_distribution,
            right_distribution,
            strict=True,
        )
    )


def _build_distribution_point(
    trait_observation: IndividualGeneticTraitObservation,
    population_observation: PopulationObservation,
) -> E7TraitDistributionPoint:
    counts = [0] * len(E7_SPEED_DOMAIN)
    for individual in trait_observation.individuals:
        speed = trait_observation.trait_value(individual.organism_id, MAX_SPEED)
        _validate_legal_speed(speed)
        counts[speed] += 1
    population_size = population_observation.population_size
    if sum(counts) != population_size:
        raise ValueError("individual trait evidence must cover the whole population.")
    frequencies: tuple[float | None, ...]
    if population_size == 0:
        frequencies = tuple(None for _ in E7_SPEED_DOMAIN)
    else:
        frequencies = tuple(count / population_size for count in counts)
    recorded_counts = population_observation.trait(MAX_SPEED).value_counts
    if (
        tuple((speed, count) for speed, count in enumerate(counts) if count)
        != recorded_counts
    ):
        raise ValueError("individual and population max_speed evidence disagree.")
    return E7TraitDistributionPoint(
        step_index=trait_observation.step_index,
        population_size=population_size,
        counts=tuple(counts),
        frequencies=frequencies,
        total_population_energy=population_observation.energy.total,
        total_resources=population_observation.total_resources,
    )


def _derive_mutation_transitions(
    pedigree: PedigreeRecorder,
    *,
    traits_by_step: dict[int, dict[int, int]],
) -> tuple[E7MutationTransition, ...]:
    counts: Counter[tuple[int, int]] = Counter()
    for record in pedigree.records:
        if record.is_founder:
            continue
        if len(record.parent_ids) != 1:
            raise ValueError(
                "E7 descendants must have exactly one clonal genetic parent."
            )
        if record.entry_step < 1:
            raise ValueError("E7 biological offspring must enter after step zero.")
        parent_id = record.parent_ids[0]
        parent_speed = _trait_at(
            traits_by_step,
            step_index=record.entry_step - 1,
            organism_id=parent_id,
        )
        offspring_speed = _trait_at(
            traits_by_step,
            step_index=record.entry_step,
            organism_id=record.organism_id,
        )
        if abs(offspring_speed - parent_speed) > E7_MUTATION_MAX_CHANGE:
            raise ValueError(
                "offspring focal transition exceeds declared E7 step size."
            )
        counts[(parent_speed, offspring_speed)] += 1
    return tuple(
        E7MutationTransition(
            parent_speed=parent_speed,
            offspring_speed=offspring_speed,
            count=count,
        )
        for (parent_speed, offspring_speed), count in sorted(counts.items())
    )


@attrs.define(slots=True)
class _MutableMechanism:
    movement_count: int = 0
    realized_distance: float = 0.0
    locomotion_energy: int = 0
    resource_consumed: int = 0
    birth_count: int = 0


def _derive_mechanisms(
    recorder: EventRecorder,
    *,
    transitions: tuple[E7MutationTransition, ...],
    traits_by_step: dict[int, dict[int, int]],
) -> tuple[E7SpeedMechanismEvidence, ...]:
    accumulators = {speed: _MutableMechanism() for speed in E7_SPEED_DOMAIN}
    for applied in recorder.events:
        event = applied.event
        if isinstance(event, Movement.Event):
            measurement = measure_applied_movement(applied)
            speed = _trait_at(
                traits_by_step,
                step_index=applied.event_step_index,
                organism_id=measurement.organism_id,
            )
            item = accumulators[speed]
            item.movement_count += 1
            item.realized_distance += measurement.realized_distance
            item.locomotion_energy += measurement.locomotion_energy_expenditure
        elif isinstance(event, ResourceConsumption.Event):
            speed = _trait_at(
                traits_by_step,
                step_index=applied.event_step_index,
                organism_id=event.organism_id,
            )
            accumulators[speed].resource_consumed += event.amount

    for transition in transitions:
        accumulators[transition.parent_speed].birth_count += transition.count

    return tuple(
        E7SpeedMechanismEvidence(
            max_speed=speed,
            applied_movement_count=accumulators[speed].movement_count,
            total_realized_distance=accumulators[speed].realized_distance,
            total_locomotion_energy_expenditure=accumulators[speed].locomotion_energy,
            total_resource_consumed=accumulators[speed].resource_consumed,
            cumulative_birth_count=accumulators[speed].birth_count,
        )
        for speed in E7_SPEED_DOMAIN
    )


def _build_trait_lookup(
    observations: Sequence[IndividualGeneticTraitObservation],
) -> dict[int, dict[int, int]]:
    return {
        observation.step_index: {
            individual.organism_id: observation.trait_value(
                individual.organism_id,
                MAX_SPEED,
            )
            for individual in observation.individuals
        }
        for observation in observations
    }


def _trait_at(
    traits_by_step: dict[int, dict[int, int]],
    *,
    step_index: int,
    organism_id: int,
) -> int:
    try:
        value = traits_by_step[step_index][organism_id]
    except KeyError as error:
        raise ValueError(
            f"missing committed max_speed evidence for organism {organism_id} "
            f"at step {step_index}."
        ) from error
    _validate_legal_speed(value)
    return value


def _validate_observation_alignment(
    trait_observations: Sequence[IndividualGeneticTraitObservation],
    population_observations: Sequence[PopulationObservation],
    *,
    horizon: int,
) -> None:
    expected = tuple(range(horizon + 1))
    trait_steps = tuple(observation.step_index for observation in trait_observations)
    population_steps = tuple(
        observation.step_index for observation in population_observations
    )
    if trait_steps != expected or population_steps != expected:
        raise ValueError("E7 recorders must contain every committed state 0..horizon.")
    for trait_observation, population_observation in zip(
        trait_observations,
        population_observations,
        strict=True,
    ):
        if len(trait_observation.individuals) != population_observation.population_size:
            raise ValueError("E7 individual/population recorder counts disagree.")


def _build_provenance(
    treatment: E7TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None,
) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="e7-mutation-driven-adaptation",
        scenario_id="controlled-clonal-locomotion-e7-v1",
        treatment_id=treatment.treatment_id,
        treatment_specification_json=canonical_treatment_specification(
            {
                "environment": "separated_corridor",
                "starting_speed": treatment.starting_speed,
                "founder_count": treatment.founder_count,
                "resource_per_founder": treatment.resource_per_founder,
                "horizon": treatment.horizon,
                "mutation_probability_ppm": treatment.mutation_probability_ppm,
                "mutation_max_change": treatment.mutation_max_change,
                "speed_domain_minimum": 0,
                "speed_domain_maximum": CONTROLLED_MAX_SPEED_MAXIMUM,
                "reference_region": list(E7_REFERENCE_REGION),
            }
        ),
        seed=seed,
        horizon_step_index=treatment.horizon,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=(
            MAX_SPEED,
            "max_speed_distribution",
            "parent_offspring_max_speed_transition",
        ),
        run_role=run_role,
    )


def _extinction_outcome(
    trajectory: Sequence[E7TraitDistributionPoint],
    *,
    horizon: int,
) -> FixedHorizonTimeToEvent:
    observed = next(
        (point.step_index for point in trajectory if point.population_size == 0),
        None,
    )
    return FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=horizon,
        observed_step_index=observed,
    )


def _mean_optional(values: Sequence[float | None]) -> float | None:
    defined = tuple(value for value in values if value is not None)
    if not defined:
        return None
    return sum(defined) / len(defined)


def _defined_endpoint_distribution(
    summary: E7StartingConditionSummary,
) -> tuple[float, ...] | None:
    values: list[float] = []
    for value in summary.endpoint_distribution:
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def _defined_frequency(point: E7TraitDistributionPoint, speed: int) -> float:
    value = point.frequency(speed)
    if value is None:
        raise ValueError("frequency is undefined after extinction.")
    return value


def _validate_distribution_shape(point: E7TraitDistributionPoint) -> None:
    if len(point.counts) != len(E7_SPEED_DOMAIN):
        raise ValueError("counts must contain one value for every legal speed.")
    if len(point.frequencies) != len(E7_SPEED_DOMAIN):
        raise ValueError("frequencies must contain one value for every legal speed.")
    for index, count in enumerate(point.counts):
        validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
    if sum(point.counts) != point.population_size:
        raise ValueError("speed counts must sum to population_size.")


def _validate_extinct_distribution(point: E7TraitDistributionPoint) -> None:
    if any(value is not None for value in point.frequencies):
        raise ValueError("extinct trait frequencies must be undefined.")
    if point.total_population_energy != 0:
        raise ValueError("extinct population energy must be zero.")


def _validate_living_distribution(point: E7TraitDistributionPoint) -> None:
    total = 0.0
    for index, frequency in enumerate(point.frequencies):
        if frequency is None:
            raise ValueError("nonempty trait frequencies must be defined.")
        if not 0.0 <= frequency <= 1.0:
            raise ValueError(f"frequencies[{index}] must lie in [0, 1].")
        total += frequency
    if not math.isclose(total, 1.0):
        raise ValueError("defined speed frequencies must sum to one.")


def _validate_legal_speed(value: int) -> None:
    validators.validate_int_in_range(
        value,
        lower=0,
        upper=CONTROLLED_MAX_SPEED_MAXIMUM,
        name="max_speed",
    )
