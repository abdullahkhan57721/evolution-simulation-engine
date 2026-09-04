"""Controlled E4 standing-variation selection experiment above E2/E3 evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence

import attrs

from evo_engine.experiments.e3_performance import (
    E3_BODY_MASS,
    E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
    E3_FOUNDER_X,
    E3_FOUNDER_Y,
    E3_HEIGHT,
    E3_HORIZON,
    E3_INITIAL_ENERGY,
    E3_LOCOMOTION_DISTANCE_EXPONENT,
    E3_REPRODUCTION_ENERGY_INVESTMENT,
    E3_REPRODUCTION_MINIMUM_ENERGY,
    E3_RESOURCE_REQUEST_AMOUNT,
    E3_WIDTH,
    E3Environment,
    build_e3_treatment,
)
from evo_engine.experiments.locomotion import measure_applied_movement
from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    RunRole,
    ScientificRunProvenance,
    canonical_treatment_specification,
    validate_declared_treatment_difference,
)
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import (
    EventRecorder,
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitRecorder,
    PopulationObservation,
    PopulationRecorder,
)
from evo_engine.presets.controlled_locomotion import (
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.processes import Movement, Reproduction, ResourceConsumption
from evo_engine.telemetry import AppliedEvent
from evo_engine.validation import attrs_validators, validators

E4_FOCAL_SPEEDS: tuple[int, int, int] = (1, 3, 9)
E4_FOUNDER_ORDERS: tuple[tuple[int, int, int], ...] = (
    (1, 3, 9),
    (3, 9, 1),
    (9, 1, 3),
)
E4_REVERSED_FOUNDER_ORDER: tuple[int, int, int] = (9, 3, 1)
E4_DISCOVERY_SEEDS: tuple[int, ...] = (7, 19, 31, 47, 73, 101)
E4_CONFIRMATION_SEEDS: tuple[int, ...] = (5, 17, 29, 43, 61, 79, 97, 113, 137)
E4_LABEL_SANITY_SEEDS: tuple[int, ...] = (17, 61, 113)


@attrs.frozen(slots=True, kw_only=True)
class E4TreatmentSpecification:
    """Define one E4 environment and founder-ID counterbalance assignment."""

    environment: E3Environment
    founder_speed_order: tuple[int, int, int] = E4_FOCAL_SPEEDS

    def __attrs_post_init__(self) -> None:
        """Validate environment and exact standing-variation composition."""
        if self.environment not in ("local_resource", "separated_corridor"):
            raise ValueError(
                "environment must be 'local_resource' or 'separated_corridor'."
            )
        validators.validate_tuple(self.founder_speed_order, name="founder_speed_order")
        if len(self.founder_speed_order) != len(E4_FOCAL_SPEEDS):
            raise ValueError("founder_speed_order must contain exactly three speeds.")
        for index, speed in enumerate(self.founder_speed_order):
            validators.validate_int(speed, name=f"founder_speed_order[{index}]")
        if tuple(sorted(self.founder_speed_order)) != E4_FOCAL_SPEEDS:
            raise ValueError(
                "founder_speed_order must contain each focal speed 1, 3, and 9 once."
            )

    @property
    def treatment_id(self) -> str:
        """Return a stable treatment identifier including founder-ID assignment."""
        order = "-".join(str(speed) for speed in self.founder_speed_order)
        return f"{self.environment}-standing-1-3-9-order-{order}"

    @property
    def resource_deposits(self) -> tuple[tuple[int, int, int], ...]:
        """Return the exact frozen E3 resource geography for this environment."""
        return build_e3_treatment(
            max_speed=3,
            environment=self.environment,
        ).resource_deposits

    def to_config(self, *, seed: int) -> ControlledLocomotionConfig:
        """Build one E2 configuration with E3 biology and E4 standing variation."""
        validators.validate_int(seed, name="seed")
        return ControlledLocomotionConfig(
            width=E3_WIDTH,
            height=E3_HEIGHT,
            max_steps=E3_HORIZON,
            seed=seed,
            founders=tuple(
                ControlledLocomotionFounder(
                    max_speed=speed,
                    x=E3_FOUNDER_X,
                    y=E3_FOUNDER_Y,
                )
                for speed in self.founder_speed_order
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
class E4FocalCompositionPoint:
    """Record the complete committed focal strategy composition at one step."""

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    counts: tuple[int, int, int]
    frequencies: tuple[float | None, float | None, float | None]

    def __attrs_post_init__(self) -> None:
        """Validate count/frequency widths and explicit extinct semantics."""
        if len(self.counts) != len(E4_FOCAL_SPEEDS):
            raise ValueError("counts must contain one value for each E4 focal speed.")
        if len(self.frequencies) != len(E4_FOCAL_SPEEDS):
            raise ValueError(
                "frequencies must contain one value for each E4 focal speed."
            )
        for index, count in enumerate(self.counts):
            validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
        if sum(self.counts) != self.population_size:
            raise ValueError("focal counts must equal the complete population size.")
        if self.population_size == 0:
            if any(value is not None for value in self.frequencies):
                raise ValueError("extinct composition frequencies must be undefined.")
            return
        for index, frequency in enumerate(self.frequencies):
            if frequency is None:
                raise ValueError("nonempty composition frequencies must be defined.")
            if not 0.0 <= frequency <= 1.0:
                raise ValueError(f"frequencies[{index}] must lie in [0, 1].")
        if not math.isclose(sum(value or 0.0 for value in self.frequencies), 1.0):
            raise ValueError("defined focal frequencies must sum to one.")

    def count(self, max_speed: int) -> int:
        """Return the committed count for one focal speed."""
        return self.counts[_focal_speed_index(max_speed)]

    def frequency(self, max_speed: int) -> float | None:
        """Return the committed frequency for one focal speed."""
        return self.frequencies[_focal_speed_index(max_speed)]


@attrs.frozen(slots=True, kw_only=True)
class E4StrategyMechanismEvidence:
    """Store strategy-specific ecological mechanism evidence for one run."""

    max_speed: int
    applied_movement_count: int
    total_realized_distance: float
    total_locomotion_energy_expenditure: int
    total_resource_consumed: int
    cumulative_birth_count: int

    def __attrs_post_init__(self) -> None:
        """Validate focal identity and nonnegative mechanism outcomes."""
        _focal_speed_index(self.max_speed)
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
class E4ReplicateOutcome:
    """Store one run-level evolutionary outcome and separate mechanism evidence."""

    treatment: E4TreatmentSpecification
    provenance: ScientificRunProvenance
    focal_trajectory: tuple[E4FocalCompositionPoint, ...]
    mechanisms: tuple[E4StrategyMechanismEvidence, ...]
    final_total_population_energy: int
    extinction: FixedHorizonTimeToEvent
    boundary_clipping_event_count: int

    def __attrs_post_init__(self) -> None:
        """Validate complete trajectory, strategy ordering, and run-level outcomes."""
        if not isinstance(self.treatment, E4TreatmentSpecification):
            raise TypeError("treatment must be an E4TreatmentSpecification.")
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        validators.validate_tuple(self.focal_trajectory, name="focal_trajectory")
        if not self.focal_trajectory:
            raise ValueError("focal_trajectory must include committed step zero.")
        if self.focal_trajectory[0].step_index != 0:
            raise ValueError("focal_trajectory must begin at committed step zero.")
        if self.focal_trajectory[-1].step_index != E3_HORIZON:
            raise ValueError("focal_trajectory must end at the frozen E4 horizon.")
        validators.validate_tuple(self.mechanisms, name="mechanisms")
        if tuple(item.max_speed for item in self.mechanisms) != E4_FOCAL_SPEEDS:
            raise ValueError("mechanisms must follow focal speed order 1, 3, 9.")
        validators.validate_int_ge(
            self.final_total_population_energy,
            bound=0,
            name="final_total_population_energy",
        )
        if not isinstance(self.extinction, FixedHorizonTimeToEvent):
            raise TypeError("extinction must be a FixedHorizonTimeToEvent.")
        validators.validate_int_ge(
            self.boundary_clipping_event_count,
            bound=0,
            name="boundary_clipping_event_count",
        )

    @property
    def initial_composition(self) -> E4FocalCompositionPoint:
        """Return the committed founder composition."""
        return self.focal_trajectory[0]

    @property
    def final_composition(self) -> E4FocalCompositionPoint:
        """Return the committed fixed-horizon composition."""
        return self.focal_trajectory[-1]

    @property
    def energy_budget_residual(self) -> int:
        """Return the E4 controlled whole-population energy-accounting residual."""
        total_resource_consumed = sum(
            item.total_resource_consumed for item in self.mechanisms
        )
        total_locomotion_expenditure = sum(
            item.total_locomotion_energy_expenditure for item in self.mechanisms
        )
        expected = (
            len(E4_FOCAL_SPEEDS) * E3_INITIAL_ENERGY
            + total_resource_consumed
            - total_locomotion_expenditure
        )
        return self.final_total_population_energy - expected

    def frequency_change(self, max_speed: int) -> float | None:
        """Return final-minus-initial focal frequency, preserving extinction undefinedness."""
        initial = self.initial_composition.frequency(max_speed)
        final = self.final_composition.frequency(max_speed)
        if initial is None or final is None:
            return None
        return final - initial

    def mechanism(self, max_speed: int) -> E4StrategyMechanismEvidence:
        """Return mechanism evidence for one focal speed."""
        return self.mechanisms[_focal_speed_index(max_speed)]


@attrs.frozen(slots=True, kw_only=True)
class E4EnvironmentSummary:
    """Summarize E4 run-level outcomes without treating organisms as replicates."""

    environment: E3Environment
    replicate_count: int
    seeds: tuple[int, ...]
    founder_speed_orders: tuple[tuple[int, int, int], ...]
    mean_final_frequencies: tuple[float | None, float | None, float | None]
    mean_frequency_changes: tuple[float | None, float | None, float | None]
    defined_endpoint_count: int
    extinction_count: int
    mean_births_by_speed: tuple[float, float, float]
    mean_resources_by_speed: tuple[float, float, float]
    mean_realized_distance_by_speed: tuple[float, float, float]
    mean_locomotion_energy_by_speed: tuple[float, float, float]

    def mean_final_frequency(self, max_speed: int) -> float | None:
        """Return the mean defined final frequency for one focal speed."""
        return self.mean_final_frequencies[_focal_speed_index(max_speed)]

    def mean_frequency_change(self, max_speed: int) -> float | None:
        """Return the mean defined frequency change for one focal speed."""
        return self.mean_frequency_changes[_focal_speed_index(max_speed)]


@attrs.define(slots=True)
class _MutableStrategyMechanism:
    """Accumulate one strategy's event-derived mechanism evidence within a run."""

    movement_count: int = 0
    realized_distance: float = 0.0
    locomotion_energy: int = 0
    resource_consumed: int = 0
    birth_count: int = 0


MechanismAccumulators = dict[int, _MutableStrategyMechanism]
TraitLookup = dict[int, dict[int, int]]


def build_e4_treatment(
    *,
    environment: E3Environment,
    founder_speed_order: tuple[int, int, int] = E4_FOCAL_SPEEDS,
) -> E4TreatmentSpecification:
    """Build one frozen E4 treatment."""
    return E4TreatmentSpecification(
        environment=environment,
        founder_speed_order=founder_speed_order,
    )


def founder_order_for_replicate(index: int) -> tuple[int, int, int]:
    """Return the predeclared cyclic founder-ID counterbalance order."""
    validators.validate_int_ge(index, bound=0, name="index")
    return E4_FOUNDER_ORDERS[index % len(E4_FOUNDER_ORDERS)]


def validate_e4_environment_treatment_integrity(
    control: E4TreatmentSpecification,
    treatment: E4TreatmentSpecification,
) -> None:
    """Require matched E4 arms to differ only in E3 resource environment."""
    _require_e4_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            environment=control.environment,
        ),
        declared_difference="E3 resource environment",
    )


def validate_e4_founder_order_integrity(
    control: E4TreatmentSpecification,
    treatment: E4TreatmentSpecification,
) -> None:
    """Require counterbalance treatments to differ only in speed-to-ID order."""
    _require_e4_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            founder_speed_order=control.founder_speed_order,
        ),
        declared_difference="founder speed-to-ID order",
    )


def run_e4_replicate(
    treatment: E4TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None = "confirmation",
) -> E4ReplicateOutcome:
    """Run one E4 replicate and derive selection/mechanism evidence from records."""
    _require_e4_treatment(treatment)
    validators.validate_int(seed, name="seed")
    trait_recorder, population_recorder, event_recorder = _run_e4_recorders(
        treatment,
        seed=seed,
    )
    trait_observations, population_observations = _validated_observations(
        trait_recorder.observations,
        population_recorder.observations,
    )
    _validate_founder_id_assignment(trait_observations[0], treatment=treatment)
    focal_trajectory = tuple(
        _composition_point(observation) for observation in trait_observations
    )
    mechanisms, clipping_count = _measure_mechanisms(
        events=event_recorder.events,
        traits_by_step=_trait_lookup_by_step(trait_observations),
    )
    _require_no_boundary_clipping(clipping_count)
    outcome = E4ReplicateOutcome(
        treatment=treatment,
        provenance=_scientific_provenance(treatment, seed=seed, run_role=run_role),
        focal_trajectory=focal_trajectory,
        mechanisms=mechanisms,
        final_total_population_energy=population_observations[-1].energy.total,
        extinction=_extinction_outcome(focal_trajectory),
        boundary_clipping_event_count=clipping_count,
    )
    _require_closed_energy_budget(outcome)
    return outcome


def run_e4_seed_set(
    *,
    environment: E3Environment,
    seeds: Sequence[int],
    run_role: RunRole | None,
) -> tuple[E4ReplicateOutcome, ...]:
    """Run E4 replicates with the predeclared cyclic founder-ID counterbalance."""
    validated_seeds = _validated_unique_seeds(seeds)
    return tuple(
        run_e4_replicate(
            build_e4_treatment(
                environment=environment,
                founder_speed_order=founder_order_for_replicate(index),
            ),
            seed=seed,
            run_role=run_role,
        )
        for index, seed in enumerate(validated_seeds)
    )


def summarize_e4_environment(
    outcomes: Sequence[E4ReplicateOutcome],
) -> E4EnvironmentSummary:
    """Summarize one environment from run-level replicate outcomes only."""
    values = tuple(outcomes)
    environment = _validate_environment_outcomes(values)
    count = len(values)
    defined_count = sum(
        outcome.final_composition.population_size > 0 for outcome in values
    )
    return E4EnvironmentSummary(
        environment=environment,
        replicate_count=count,
        seeds=tuple(outcome.provenance.seed for outcome in values),
        founder_speed_orders=tuple(
            outcome.treatment.founder_speed_order for outcome in values
        ),
        mean_final_frequencies=(
            _mean_final_frequency(values, 1),
            _mean_final_frequency(values, 3),
            _mean_final_frequency(values, 9),
        ),
        mean_frequency_changes=(
            _mean_frequency_change(values, 1),
            _mean_frequency_change(values, 3),
            _mean_frequency_change(values, 9),
        ),
        defined_endpoint_count=defined_count,
        extinction_count=count - defined_count,
        mean_births_by_speed=(
            _mean_births(values, 1),
            _mean_births(values, 3),
            _mean_births(values, 9),
        ),
        mean_resources_by_speed=(
            _mean_resources(values, 1),
            _mean_resources(values, 3),
            _mean_resources(values, 9),
        ),
        mean_realized_distance_by_speed=(
            _mean_realized_distance(values, 1),
            _mean_realized_distance(values, 3),
            _mean_realized_distance(values, 9),
        ),
        mean_locomotion_energy_by_speed=(
            _mean_locomotion_energy(values, 1),
            _mean_locomotion_energy(values, 3),
            _mean_locomotion_energy(values, 9),
        ),
    )


def _run_e4_recorders(
    treatment: E4TreatmentSpecification,
    *,
    seed: int,
) -> tuple[IndividualGeneticTraitRecorder, PopulationRecorder, EventRecorder]:
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
    spec = build_controlled_locomotion_spec(
        treatment.to_config(seed=seed),
        observers=(trait_recorder, population_recorder),
        telemetry_observers=(event_recorder,),
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)
    return trait_recorder, population_recorder, event_recorder


def _validated_observations(
    trait_observations: Sequence[IndividualGeneticTraitObservation],
    population_observations: Sequence[PopulationObservation],
) -> tuple[
    tuple[IndividualGeneticTraitObservation, ...],
    tuple[PopulationObservation, ...],
]:
    traits = tuple(trait_observations)
    populations = tuple(population_observations)
    if not traits or not populations:
        raise RuntimeError("E4 committed observation recorders produced no evidence.")
    trait_steps = tuple(item.step_index for item in traits)
    population_steps = tuple(item.step_index for item in populations)
    if trait_steps != population_steps:
        raise RuntimeError("E4 trait/population observation steps are misaligned.")
    return traits, populations


def _scientific_provenance(
    treatment: E4TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None,
) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="e4-standing-variation-selection",
        scenario_id="controlled-clonal-locomotion-e4-v1",
        treatment_id=treatment.treatment_id,
        treatment_specification_json=canonical_treatment_specification(
            _treatment_provenance_mapping(treatment)
        ),
        seed=seed,
        horizon_step_index=E3_HORIZON,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=(
            "max_speed_focal_counts",
            "max_speed_focal_frequencies",
            "realized_movement_by_speed",
            "locomotion_energy_by_speed",
            "resource_consumption_by_speed",
            "reproduction_by_speed",
            "extinction",
        ),
        run_role=run_role,
    )


def _measure_mechanisms(
    *,
    events: Sequence[AppliedEvent],
    traits_by_step: TraitLookup,
) -> tuple[tuple[E4StrategyMechanismEvidence, ...], int]:
    accumulators = {speed: _MutableStrategyMechanism() for speed in E4_FOCAL_SPEEDS}
    clipping_count = 0
    for applied in events:
        clipping_count += _measure_applied_event(
            applied,
            accumulators=accumulators,
            traits_by_step=traits_by_step,
        )
    return _frozen_mechanisms(accumulators), clipping_count


def _measure_applied_event(
    applied: AppliedEvent,
    *,
    accumulators: MechanismAccumulators,
    traits_by_step: TraitLookup,
) -> int:
    event = applied.event
    if isinstance(event, Movement.Event):
        return _measure_movement_event(
            applied,
            accumulators=accumulators,
            traits_by_step=traits_by_step,
        )
    if isinstance(event, ResourceConsumption.Event):
        _measure_resource_event(
            event,
            accumulators=accumulators,
            traits_by_step=traits_by_step,
        )
    elif isinstance(event, Reproduction.Event):
        _measure_reproduction_event(
            event,
            accumulators=accumulators,
            traits_by_step=traits_by_step,
        )
    return 0


def _measure_movement_event(
    applied: AppliedEvent,
    *,
    accumulators: MechanismAccumulators,
    traits_by_step: TraitLookup,
) -> int:
    event = applied.event
    if not isinstance(event, Movement.Event):
        raise TypeError("applied event must contain Movement.Event.")
    speed = _event_actor_speed(
        step_index=event.step_index,
        organism_id=event.organism_id,
        traits_by_step=traits_by_step,
    )
    measurement = measure_applied_movement(applied)
    accumulator = accumulators[speed]
    accumulator.movement_count += 1
    accumulator.realized_distance += measurement.realized_distance
    accumulator.locomotion_energy += measurement.locomotion_energy_expenditure
    return int(
        not math.isclose(
            measurement.attempted_distance,
            measurement.realized_distance,
        )
    )


def _measure_resource_event(
    event: ResourceConsumption.Event,
    *,
    accumulators: MechanismAccumulators,
    traits_by_step: TraitLookup,
) -> None:
    speed = _event_actor_speed(
        step_index=event.step_index,
        organism_id=event.organism_id,
        traits_by_step=traits_by_step,
    )
    accumulators[speed].resource_consumed += event.amount


def _measure_reproduction_event(
    event: Reproduction.Event,
    *,
    accumulators: MechanismAccumulators,
    traits_by_step: TraitLookup,
) -> None:
    offspring_speed = event.offspring_genetic_phenotype.int_value(MAX_SPEED)
    _focal_speed_index(offspring_speed)
    if len(event.parent_ids) != 1:
        raise RuntimeError("E4 clonal reproduction must have exactly one parent.")
    parent_speed = _event_actor_speed(
        step_index=event.step_index,
        organism_id=event.parent_ids[0],
        traits_by_step=traits_by_step,
    )
    if parent_speed != offspring_speed:
        raise RuntimeError(
            "E4 clonal offspring max_speed differs from its genetic parent."
        )
    accumulators[offspring_speed].birth_count += 1


def _frozen_mechanisms(
    accumulators: MechanismAccumulators,
) -> tuple[
    E4StrategyMechanismEvidence,
    E4StrategyMechanismEvidence,
    E4StrategyMechanismEvidence,
]:
    return (
        _frozen_mechanism(1, accumulators[1]),
        _frozen_mechanism(3, accumulators[3]),
        _frozen_mechanism(9, accumulators[9]),
    )


def _frozen_mechanism(
    speed: int,
    accumulator: _MutableStrategyMechanism,
) -> E4StrategyMechanismEvidence:
    return E4StrategyMechanismEvidence(
        max_speed=speed,
        applied_movement_count=accumulator.movement_count,
        total_realized_distance=accumulator.realized_distance,
        total_locomotion_energy_expenditure=accumulator.locomotion_energy,
        total_resource_consumed=accumulator.resource_consumed,
        cumulative_birth_count=accumulator.birth_count,
    )


def _require_no_boundary_clipping(clipping_count: int) -> None:
    if clipping_count:
        raise RuntimeError(
            "Canonical E4 geometry produced unexpected attempted/realized movement "
            "mismatch; boundary clipping or another movement artifact is present."
        )


def _require_closed_energy_budget(outcome: E4ReplicateOutcome) -> None:
    if outcome.energy_budget_residual != 0:
        raise RuntimeError(
            "Controlled E4 whole-population energy budget did not close; "
            f"residual={outcome.energy_budget_residual}."
        )


def _extinction_outcome(
    focal_trajectory: Sequence[E4FocalCompositionPoint],
) -> FixedHorizonTimeToEvent:
    extinction_step = next(
        (point.step_index for point in focal_trajectory if point.population_size == 0),
        None,
    )
    return FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=E3_HORIZON,
        observed_step_index=extinction_step,
    )


def _composition_point(
    observation: IndividualGeneticTraitObservation,
) -> E4FocalCompositionPoint:
    if observation.trait_names != (MAX_SPEED,):
        raise RuntimeError("E4 trait evidence must record exactly max_speed.")
    counts = {speed: 0 for speed in E4_FOCAL_SPEEDS}
    for individual in observation.individuals:
        speed = individual.trait_values[0]
        _focal_speed_index(speed)
        counts[speed] += 1
    population_size = len(observation.individuals)
    ordered_counts: tuple[int, int, int] = (counts[1], counts[3], counts[9])
    frequencies = _composition_frequencies(ordered_counts, population_size)
    return E4FocalCompositionPoint(
        step_index=observation.step_index,
        population_size=population_size,
        counts=ordered_counts,
        frequencies=frequencies,
    )


def _composition_frequencies(
    counts: tuple[int, int, int],
    population_size: int,
) -> tuple[float | None, float | None, float | None]:
    if population_size == 0:
        return (None, None, None)
    return (
        counts[0] / population_size,
        counts[1] / population_size,
        counts[2] / population_size,
    )


def _validate_founder_id_assignment(
    observation: IndividualGeneticTraitObservation,
    *,
    treatment: E4TreatmentSpecification,
) -> None:
    if observation.step_index != 0:
        raise ValueError("founder assignment audit requires committed step zero.")
    observed_order = tuple(
        individual.trait_values[0] for individual in observation.individuals
    )
    if observed_order != treatment.founder_speed_order:
        raise RuntimeError(
            "E4 founder ID order does not match the declared speed counterbalance."
        )
    if len({individual.organism_id for individual in observation.individuals}) != 3:
        raise RuntimeError("E4 must begin with exactly three unique founder IDs.")


def _trait_lookup_by_step(
    observations: Sequence[IndividualGeneticTraitObservation],
) -> TraitLookup:
    result: TraitLookup = {}
    for observation in observations:
        result[observation.step_index] = {
            individual.organism_id: individual.trait_values[0]
            for individual in observation.individuals
        }
    return result


def _event_actor_speed(
    *,
    step_index: int,
    organism_id: int,
    traits_by_step: TraitLookup,
) -> int:
    try:
        speed = traits_by_step[step_index][organism_id]
    except KeyError as error:
        raise RuntimeError(
            "E4 event actor is absent from same-step committed trait evidence."
        ) from error
    _focal_speed_index(speed)
    return speed


def _validate_environment_outcomes(
    values: tuple[E4ReplicateOutcome, ...],
) -> E3Environment:
    if not values:
        raise ValueError("outcomes must contain at least one replicate.")
    environment = values[0].treatment.environment
    seen_seeds: set[int] = set()
    for index, outcome in enumerate(values):
        _validate_environment_outcome(
            outcome,
            index=index,
            environment=environment,
            seen_seeds=seen_seeds,
        )
    return environment


def _validate_environment_outcome(
    outcome: E4ReplicateOutcome,
    *,
    index: int,
    environment: E3Environment,
    seen_seeds: set[int],
) -> None:
    if not isinstance(outcome, E4ReplicateOutcome):
        raise TypeError(f"outcomes[{index}] must be an E4ReplicateOutcome.")
    if outcome.treatment.environment != environment:
        raise ValueError("all outcomes must belong to the same E4 environment.")
    if outcome.provenance.seed in seen_seeds:
        raise ValueError("outcomes must not contain duplicate replicate seeds.")
    seen_seeds.add(outcome.provenance.seed)


def _mean_final_frequency(
    values: Sequence[E4ReplicateOutcome],
    speed: int,
) -> float | None:
    return _mean_optional(
        tuple(outcome.final_composition.frequency(speed) for outcome in values)
    )


def _mean_frequency_change(
    values: Sequence[E4ReplicateOutcome],
    speed: int,
) -> float | None:
    return _mean_optional(tuple(outcome.frequency_change(speed) for outcome in values))


def _mean_births(values: Sequence[E4ReplicateOutcome], speed: int) -> float:
    return sum(
        outcome.mechanism(speed).cumulative_birth_count for outcome in values
    ) / len(values)


def _mean_resources(values: Sequence[E4ReplicateOutcome], speed: int) -> float:
    return sum(
        outcome.mechanism(speed).total_resource_consumed for outcome in values
    ) / len(values)


def _mean_realized_distance(
    values: Sequence[E4ReplicateOutcome],
    speed: int,
) -> float:
    return sum(
        outcome.mechanism(speed).total_realized_distance for outcome in values
    ) / len(values)


def _mean_locomotion_energy(
    values: Sequence[E4ReplicateOutcome],
    speed: int,
) -> float:
    return sum(
        outcome.mechanism(speed).total_locomotion_energy_expenditure
        for outcome in values
    ) / len(values)


def _treatment_provenance_mapping(
    treatment: E4TreatmentSpecification,
) -> dict[str, object]:
    return {
        "environment": treatment.environment,
        "founder_speed_order": list(treatment.founder_speed_order),
        "focal_speeds": list(E4_FOCAL_SPEEDS),
        "initial_frequency_each": 1 / 3,
        "founder_position": {"x": E3_FOUNDER_X, "y": E3_FOUNDER_Y},
        "founder_initial_energy": E3_INITIAL_ENERGY,
        "body_mass": E3_BODY_MASS,
        "width": E3_WIDTH,
        "height": E3_HEIGHT,
        "horizon_step_index": E3_HORIZON,
        "resource_deposits": [
            {"x": x, "y": y, "amount": amount}
            for x, y, amount in treatment.resource_deposits
        ],
        "resource_request_amount": E3_RESOURCE_REQUEST_AMOUNT,
        "reproduction_minimum_energy": E3_REPRODUCTION_MINIMUM_ENERGY,
        "reproduction_energy_investment": E3_REPRODUCTION_ENERGY_INVESTMENT,
        "locomotion_cost_coefficient": E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
        "locomotion_distance_exponent": E3_LOCOMOTION_DISTANCE_EXPONENT,
        "focal_mutation": "off",
        "assimilation": "full",
    }


def _validated_unique_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    values = tuple(seeds)
    if not values:
        raise ValueError("seeds must contain at least one replicate seed.")
    validated: list[int] = []
    for index, seed in enumerate(values):
        validated.append(validators.validate_int(seed, name=f"seeds[{index}]"))
    if len(validated) != len(set(validated)):
        raise ValueError("seeds must not contain duplicates.")
    return tuple(validated)


def _mean_optional(values: Sequence[float | None]) -> float | None:
    defined = tuple(value for value in values if value is not None)
    if not defined:
        return None
    return sum(defined) / len(defined)


def _focal_speed_index(max_speed: int) -> int:
    validated = validators.validate_int(max_speed, name="max_speed")
    try:
        return E4_FOCAL_SPEEDS.index(validated)
    except ValueError as error:
        raise ValueError(
            f"max_speed must be one of the E4 focal speeds {E4_FOCAL_SPEEDS}."
        ) from error


def _require_e4_treatment(treatment: E4TreatmentSpecification) -> None:
    if not isinstance(treatment, E4TreatmentSpecification):
        raise TypeError("treatment must be an E4TreatmentSpecification.")


def _require_e4_treatments(
    control: E4TreatmentSpecification,
    treatment: E4TreatmentSpecification,
) -> None:
    if not isinstance(control, E4TreatmentSpecification):
        raise TypeError("control must be an E4TreatmentSpecification.")
    _require_e4_treatment(treatment)
