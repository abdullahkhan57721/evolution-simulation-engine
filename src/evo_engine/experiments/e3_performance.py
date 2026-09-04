"""Controlled E3 ecological-performance assays above committed E2 evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

import attrs

from evo_engine.experiments.locomotion import (
    LocomotionReplicateMeasurements,
    measure_applied_movement,
    summarize_locomotion_replicate,
)
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
from evo_engine.validation import attrs_validators, validators

E3Environment = Literal["local_resource", "separated_corridor"]
_E3_ENVIRONMENTS: frozenset[str] = frozenset({"local_resource", "separated_corridor"})

E3_SPEED_GRID: tuple[int, ...] = tuple(range(1, 11))
E3_DISCOVERY_SEEDS: tuple[int, ...] = (3, 11, 23)
E3_CONFIRMATION_SEEDS: tuple[int, ...] = (17, 29, 41, 53, 67, 79, 97, 109)
E3_SENSITIVITY_SEEDS: tuple[int, ...] = (17, 41, 67, 97)

E3_WIDTH = 69
E3_HEIGHT = 31
E3_HORIZON = 30
E3_FOUNDER_X = 10
E3_FOUNDER_Y = 15
E3_INITIAL_ENERGY = 100
E3_BODY_MASS = 1
E3_RESOURCE_REQUEST_AMOUNT = 10
E3_REPRODUCTION_MINIMUM_ENERGY = 140
E3_REPRODUCTION_ENERGY_INVESTMENT = 20
E3_LOCOMOTION_DISTANCE_EXPONENT = 2
E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT = 1
E3_TOTAL_INITIAL_RESOURCES = 480

_LOCAL_RESOURCE_DEPOSITS: tuple[tuple[int, int, int], ...] = (
    (E3_FOUNDER_X, E3_FOUNDER_Y, E3_TOTAL_INITIAL_RESOURCES),
)
_SEPARATED_CORRIDOR_DEPOSITS: tuple[tuple[int, int, int], ...] = (
    (22, E3_FOUNDER_Y, 120),
    (34, E3_FOUNDER_Y, 120),
    (46, E3_FOUNDER_Y, 120),
    (58, E3_FOUNDER_Y, 120),
)


@attrs.frozen(slots=True, kw_only=True)
class E3TreatmentSpecification:
    """Define one scientifically relevant E3 speed/environment treatment."""

    environment: E3Environment
    max_speed: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(1, 10),
    )
    locomotion_cost_coefficient: int = attrs.field(
        default=E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
        validator=attrs_validators.validate_int_ge(0),
    )
    resource_deposits: tuple[tuple[int, int, int], ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate environment identity, resource geometry, and total amount."""
        validated_environment = validators.validate_str(
            self.environment,
            name="environment",
        )
        if validated_environment not in _E3_ENVIRONMENTS:
            raise ValueError(
                "environment must be 'local_resource' or 'separated_corridor'."
            )
        validators.validate_tuple(self.resource_deposits, name="resource_deposits")
        if not self.resource_deposits:
            raise ValueError("resource_deposits must not be empty.")

        total_resources = 0
        coordinates: set[tuple[int, int]] = set()
        for index, deposit in enumerate(self.resource_deposits):
            if type(deposit) is not tuple or len(deposit) != 3:
                raise TypeError(
                    f"resource_deposits[{index}] must be a three-integer tuple."
                )
            x = validators.validate_int_ge(
                deposit[0],
                bound=0,
                name=f"resource_deposits[{index}][0]",
            )
            y = validators.validate_int_ge(
                deposit[1],
                bound=0,
                name=f"resource_deposits[{index}][1]",
            )
            amount = validators.validate_int_gt(
                deposit[2],
                bound=0,
                name=f"resource_deposits[{index}][2]",
            )
            if x >= E3_WIDTH or y >= E3_HEIGHT:
                raise ValueError(
                    f"resource_deposits[{index}] must lie inside the E3 world."
                )
            if (x, y) in coordinates:
                raise ValueError("resource_deposits must use unique coordinates.")
            coordinates.add((x, y))
            total_resources += amount

        if total_resources != E3_TOTAL_INITIAL_RESOURCES:
            raise ValueError(
                "E3 treatments must preserve the canonical total initial resource "
                f"amount {E3_TOTAL_INITIAL_RESOURCES}."
            )

    @property
    def treatment_id(self) -> str:
        """Return a stable treatment identifier."""
        return (
            f"{self.environment}-speed-{self.max_speed}-"
            f"cost-{self.locomotion_cost_coefficient}"
        )

    def to_config(self, *, seed: int) -> ControlledLocomotionConfig:
        """Build the E2 controlled-locomotion configuration for one replicate."""
        validators.validate_int(seed, name="seed")
        return ControlledLocomotionConfig(
            width=E3_WIDTH,
            height=E3_HEIGHT,
            max_steps=E3_HORIZON,
            seed=seed,
            founders=(
                ControlledLocomotionFounder(
                    max_speed=self.max_speed,
                    x=E3_FOUNDER_X,
                    y=E3_FOUNDER_Y,
                ),
            ),
            resource_deposits=tuple(
                ControlledResourceDeposit(x=x, y=y, amount=amount)
                for x, y, amount in self.resource_deposits
            ),
            initial_energy=E3_INITIAL_ENERGY,
            body_mass=E3_BODY_MASS,
            locomotion_cost_coefficient=self.locomotion_cost_coefficient,
            locomotion_distance_exponent=E3_LOCOMOTION_DISTANCE_EXPONENT,
            resource_request_amount=E3_RESOURCE_REQUEST_AMOUNT,
            reproduction_minimum_energy=E3_REPRODUCTION_MINIMUM_ENERGY,
            reproduction_energy_investment=E3_REPRODUCTION_ENERGY_INVESTMENT,
        )


@attrs.frozen(slots=True, kw_only=True)
class E3EnergyPoint:
    """Record one committed whole-population energy observation."""

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    total_population_energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0)
    )


@attrs.frozen(slots=True, kw_only=True)
class E3ReplicateOutcome:
    """Store separated mechanics and ecological outcomes for one run/seed."""

    treatment: E3TreatmentSpecification
    provenance: ScientificRunProvenance
    locomotion: LocomotionReplicateMeasurements
    total_resource_consumed: int
    energy_trajectory: tuple[E3EnergyPoint, ...]
    final_population_size: int
    final_total_population_energy: int
    cumulative_birth_count: int
    extinction: FixedHorizonTimeToEvent
    boundary_clipping_event_count: int

    def __attrs_post_init__(self) -> None:
        """Validate typed replicate evidence and nonnegative run-level outcomes."""
        if not isinstance(self.treatment, E3TreatmentSpecification):
            raise TypeError("treatment must be an E3TreatmentSpecification.")
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        if not isinstance(self.locomotion, LocomotionReplicateMeasurements):
            raise TypeError("locomotion must be LocomotionReplicateMeasurements.")
        validators.validate_int_ge(
            self.total_resource_consumed,
            bound=0,
            name="total_resource_consumed",
        )
        validators.validate_tuple(self.energy_trajectory, name="energy_trajectory")
        if not self.energy_trajectory:
            raise ValueError("energy_trajectory must include committed step zero.")
        validators.validate_int_ge(
            self.final_population_size,
            bound=0,
            name="final_population_size",
        )
        validators.validate_int_ge(
            self.final_total_population_energy,
            bound=0,
            name="final_total_population_energy",
        )
        validators.validate_int_ge(
            self.cumulative_birth_count,
            bound=0,
            name="cumulative_birth_count",
        )
        if not isinstance(self.extinction, FixedHorizonTimeToEvent):
            raise TypeError("extinction must be a FixedHorizonTimeToEvent.")
        validators.validate_int_ge(
            self.boundary_clipping_event_count,
            bound=0,
            name="boundary_clipping_event_count",
        )

    @property
    def energy_budget_residual(self) -> int:
        """Return controlled whole-population energy-accounting residual."""
        expected_final_energy = (
            E3_INITIAL_ENERGY
            + self.total_resource_consumed
            - self.locomotion.total_locomotion_energy_expenditure
        )
        return self.final_total_population_energy - expected_final_energy


@attrs.frozen(slots=True, kw_only=True)
class E3TreatmentSummary:
    """Summarize replicate-level E3 outcomes for one frozen treatment."""

    treatment: E3TreatmentSpecification
    replicate_count: int
    seeds: tuple[int, ...]
    birth_counts: tuple[int, ...]
    mean_cumulative_birth_count: float
    mean_final_population_size: float
    mean_total_resource_consumed: float
    mean_total_realized_distance: float
    mean_total_locomotion_energy_expenditure: float
    extinction_count: int


def build_e3_treatment(
    *,
    max_speed: int,
    environment: E3Environment,
    locomotion_cost_coefficient: int = E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
) -> E3TreatmentSpecification:
    """Build one frozen E3 treatment from the predeclared scientific design."""
    deposits = (
        _LOCAL_RESOURCE_DEPOSITS
        if environment == "local_resource"
        else _SEPARATED_CORRIDOR_DEPOSITS
    )
    return E3TreatmentSpecification(
        environment=environment,
        max_speed=max_speed,
        locomotion_cost_coefficient=locomotion_cost_coefficient,
        resource_deposits=deposits,
    )


def validate_e3_speed_treatment_integrity(
    control: E3TreatmentSpecification,
    treatment: E3TreatmentSpecification,
) -> None:
    """Require two same-environment treatments to differ only in max speed."""
    _require_e3_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(treatment, max_speed=control.max_speed),
        declared_difference="monomorphic max_speed",
    )


def validate_e3_environment_treatment_integrity(
    control: E3TreatmentSpecification,
    treatment: E3TreatmentSpecification,
) -> None:
    """Require matched-speed treatments to differ only in resource geography."""
    _require_e3_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            environment=control.environment,
            resource_deposits=control.resource_deposits,
        ),
        declared_difference="resource geography",
    )


def validate_e3_cost_sensitivity_integrity(
    control: E3TreatmentSpecification,
    treatment: E3TreatmentSpecification,
) -> None:
    """Require sensitivity treatments to differ only in locomotion-use cost."""
    _require_e3_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            locomotion_cost_coefficient=control.locomotion_cost_coefficient,
        ),
        declared_difference="locomotion cost coefficient",
    )


def run_e3_replicate(
    treatment: E3TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None = "confirmation",
) -> E3ReplicateOutcome:
    """Run one monomorphic E3 replicate and derive outcomes from committed evidence."""
    if not isinstance(treatment, E3TreatmentSpecification):
        raise TypeError("treatment must be an E3TreatmentSpecification.")
    validators.validate_int(seed, name="seed")

    population_recorder = PopulationRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=True,
    )
    event_recorder = EventRecorder()
    spec = build_controlled_locomotion_spec(
        treatment.to_config(seed=seed),
        observers=(population_recorder,),
        telemetry_observers=(event_recorder,),
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)

    provenance = ScientificRunProvenance(
        experiment_id="e3-ecological-performance-landscape",
        scenario_id="controlled-clonal-locomotion-e3-v1",
        treatment_id=treatment.treatment_id,
        treatment_specification_json=canonical_treatment_specification(
            _treatment_provenance_mapping(treatment)
        ),
        seed=seed,
        horizon_step_index=E3_HORIZON,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=(
            "max_speed",
            "realized_movement",
            "locomotion_energy_expenditure",
            "resource_consumption",
            "population_energy",
            "cumulative_birth_count",
            "final_population_size",
            "extinction",
        ),
        run_role=run_role,
    )
    locomotion = summarize_locomotion_replicate(
        provenance=provenance,
        events=event_recorder.events,
    )

    movement_measurements = tuple(
        measure_applied_movement(applied)
        for applied in event_recorder.events
        if isinstance(applied.event, Movement.Event)
    )
    clipping_count = sum(
        not math.isclose(
            measurement.attempted_distance,
            measurement.realized_distance,
        )
        for measurement in movement_measurements
    )
    if clipping_count:
        raise RuntimeError(
            "Canonical E3 geometry produced unexpected attempted/realized movement "
            "mismatch; boundary clipping or another movement artifact is present."
        )

    total_resource_consumed = sum(
        applied.event.amount
        for applied in event_recorder.events
        if isinstance(applied.event, ResourceConsumption.Event)
    )
    cumulative_birth_count = sum(
        1
        for applied in event_recorder.events
        if isinstance(applied.event, Reproduction.Event)
    )

    observations = population_recorder.observations
    if not observations:
        raise RuntimeError("E3 population recorder produced no committed observations.")
    _validate_monomorphic_trait_history(observations, max_speed=treatment.max_speed)
    energy_trajectory = tuple(
        E3EnergyPoint(
            step_index=observation.step_index,
            population_size=observation.population_size,
            total_population_energy=observation.energy.total,
        )
        for observation in observations
    )
    final = observations[-1]
    extinction_step = next(
        (
            observation.step_index
            for observation in observations
            if observation.population_size == 0
        ),
        None,
    )
    outcome = E3ReplicateOutcome(
        treatment=treatment,
        provenance=provenance,
        locomotion=locomotion,
        total_resource_consumed=total_resource_consumed,
        energy_trajectory=energy_trajectory,
        final_population_size=final.population_size,
        final_total_population_energy=final.energy.total,
        cumulative_birth_count=cumulative_birth_count,
        extinction=FixedHorizonTimeToEvent(
            start_step_index=0,
            horizon_step_index=E3_HORIZON,
            observed_step_index=extinction_step,
        ),
        boundary_clipping_event_count=clipping_count,
    )
    if outcome.energy_budget_residual != 0:
        raise RuntimeError(
            "Controlled E3 whole-population energy budget did not close; "
            f"residual={outcome.energy_budget_residual}."
        )
    return outcome


def run_e3_replicates(
    treatment: E3TreatmentSpecification,
    *,
    seeds: Sequence[int],
    run_role: RunRole | None = "confirmation",
) -> tuple[E3ReplicateOutcome, ...]:
    """Run independent E3 replicates in caller-supplied seed order."""
    if not isinstance(treatment, E3TreatmentSpecification):
        raise TypeError("treatment must be an E3TreatmentSpecification.")
    validated_seeds = _validated_unique_seeds(seeds)
    return tuple(
        run_e3_replicate(treatment, seed=seed, run_role=run_role)
        for seed in validated_seeds
    )


def summarize_e3_treatment(
    outcomes: Sequence[E3ReplicateOutcome],
) -> E3TreatmentSummary:
    """Summarize one treatment only after preserving run-level replicate outcomes."""
    values = tuple(outcomes)
    if not values:
        raise ValueError("outcomes must contain at least one replicate.")
    treatment = values[0].treatment
    seeds: list[int] = []
    for index, outcome in enumerate(values):
        if not isinstance(outcome, E3ReplicateOutcome):
            raise TypeError(f"outcomes[{index}] must be an E3ReplicateOutcome.")
        if outcome.treatment != treatment:
            raise ValueError("all outcomes must belong to the same E3 treatment.")
        if outcome.provenance.seed in seeds:
            raise ValueError("outcomes must not contain duplicate replicate seeds.")
        seeds.append(outcome.provenance.seed)

    count = len(values)
    birth_counts = tuple(outcome.cumulative_birth_count for outcome in values)
    return E3TreatmentSummary(
        treatment=treatment,
        replicate_count=count,
        seeds=tuple(seeds),
        birth_counts=birth_counts,
        mean_cumulative_birth_count=sum(birth_counts) / count,
        mean_final_population_size=(
            sum(outcome.final_population_size for outcome in values) / count
        ),
        mean_total_resource_consumed=(
            sum(outcome.total_resource_consumed for outcome in values) / count
        ),
        mean_total_realized_distance=(
            sum(outcome.locomotion.total_realized_distance for outcome in values)
            / count
        ),
        mean_total_locomotion_energy_expenditure=(
            sum(
                outcome.locomotion.total_locomotion_energy_expenditure
                for outcome in values
            )
            / count
        ),
        extinction_count=sum(
            not outcome.extinction.right_censored for outcome in values
        ),
    )


def _treatment_provenance_mapping(
    treatment: E3TreatmentSpecification,
) -> dict[str, object]:
    return {
        "environment": treatment.environment,
        "max_speed": treatment.max_speed,
        "locomotion_cost_coefficient": treatment.locomotion_cost_coefficient,
        "locomotion_distance_exponent": E3_LOCOMOTION_DISTANCE_EXPONENT,
        "width": E3_WIDTH,
        "height": E3_HEIGHT,
        "horizon_step_index": E3_HORIZON,
        "founder": {
            "x": E3_FOUNDER_X,
            "y": E3_FOUNDER_Y,
            "initial_energy": E3_INITIAL_ENERGY,
            "body_mass": E3_BODY_MASS,
        },
        "resource_deposits": [
            {"x": x, "y": y, "amount": amount}
            for x, y, amount in treatment.resource_deposits
        ],
        "resource_request_amount": E3_RESOURCE_REQUEST_AMOUNT,
        "reproduction_minimum_energy": E3_REPRODUCTION_MINIMUM_ENERGY,
        "reproduction_energy_investment": E3_REPRODUCTION_ENERGY_INVESTMENT,
        "focal_mutation": "off",
        "assimilation": "full",
    }


def _validate_monomorphic_trait_history(
    observations: Sequence[PopulationObservation],
    *,
    max_speed: int,
) -> None:
    for observation in observations:
        trait_summary = observation.trait(MAX_SPEED)
        unexpected = tuple(
            (value, count)
            for value, count in trait_summary.value_counts
            if value != max_speed
        )
        if unexpected:
            raise RuntimeError(
                "E3 focal trait changed despite monomorphic NoMutation design; "
                f"observed {unexpected!r}."
            )


def _validated_unique_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    values = tuple(seeds)
    if not values:
        raise ValueError("seeds must contain at least one replicate seed.")
    result: list[int] = []
    for index, seed in enumerate(values):
        validated = validators.validate_int(seed, name=f"seeds[{index}]")
        if validated in result:
            raise ValueError("seeds must not contain duplicates.")
        result.append(validated)
    return tuple(result)


def _require_e3_treatments(
    control: object,
    treatment: object,
) -> None:
    if not isinstance(control, E3TreatmentSpecification):
        raise TypeError("control must be an E3TreatmentSpecification.")
    if not isinstance(treatment, E3TreatmentSpecification):
        raise TypeError("treatment must be an E3TreatmentSpecification.")
