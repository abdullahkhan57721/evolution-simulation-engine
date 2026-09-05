"""Controlled E5 drift and weak-selection experiments above E2 pedigree evidence."""

from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Sequence
from typing import Literal

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
from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    RunRole,
    ScientificRunProvenance,
    canonical_treatment_specification,
    validate_declared_treatment_difference,
)
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import (
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitRecorder,
    IndividualLifeHistory,
    PedigreeRecorder,
)
from evo_engine.presets.controlled_locomotion import (
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.validation import attrs_validators, validators

E5Mode = Literal["neutral", "weak_selection"]
E5Group = Literal["A", "B"]
E5FixationWinner = Literal["A", "B"]

E5_FOUNDER_COUNTS: tuple[int, ...] = (2, 8, 32)
E5_DISCOVERY_SEEDS: tuple[int, ...] = (11, 23, 37, 53, 71, 89)
E5_CONFIRMATION_SEEDS: tuple[int, ...] = (
    149,
    157,
    167,
    179,
    191,
    199,
    211,
    223,
    227,
    239,
    251,
    263,
    269,
    277,
    281,
    293,
    307,
    311,
    317,
    331,
    337,
    347,
    353,
    359,
)
E5_HORIZON = 60
E5_NEUTRAL_SPEED = 3
E5_WEAK_PAIR: tuple[int, int] = (3, 4)
E5_WEAK_PAIR_ALTERNATIVE: tuple[int, int] = (3, 2)
E5_RESOURCE_PER_FOUNDER = 420

_E5_MODES: frozenset[str] = frozenset({"neutral", "weak_selection"})
_E5_WEAK_PAIRS: frozenset[tuple[int, int]] = frozenset(
    {E5_WEAK_PAIR, E5_WEAK_PAIR_ALTERNATIVE}
)


@attrs.frozen(slots=True, kw_only=True)
class E5TreatmentSpecification:
    """Define one E5 population-size and neutral/weak-selection treatment."""

    mode: E5Mode
    founder_count: int
    assignment_phase: int = 0
    weak_pair: tuple[int, int] = E5_WEAK_PAIR

    def __attrs_post_init__(self) -> None:
        """Validate the deliberately bounded E5 treatment design."""
        validated_mode = validators.validate_str(self.mode, name="mode")
        if validated_mode not in _E5_MODES:
            raise ValueError("mode must be 'neutral' or 'weak_selection'.")
        validators.validate_int(self.founder_count, name="founder_count")
        if self.founder_count not in E5_FOUNDER_COUNTS:
            raise ValueError(
                f"founder_count must be one of {E5_FOUNDER_COUNTS!r}."
            )
        validators.validate_int_in_range(
            self.assignment_phase,
            0,
            1,
            name="assignment_phase",
        )
        validators.validate_tuple(self.weak_pair, name="weak_pair")
        if self.weak_pair not in _E5_WEAK_PAIRS:
            raise ValueError(
                "weak_pair must be the predeclared (3, 4) candidate or bounded "
                "alternative (3, 2)."
            )

    @property
    def group_speeds(self) -> tuple[int, int]:
        """Return modeled speeds associated with analysis groups A and B."""
        if self.mode == "neutral":
            return (E5_NEUTRAL_SPEED, E5_NEUTRAL_SPEED)
        return self.weak_pair

    @property
    def founder_groups(self) -> tuple[E5Group, ...]:
        """Return counterbalanced analysis-group assignment in founder-ID order."""
        first: E5Group = "A" if self.assignment_phase == 0 else "B"
        second: E5Group = "B" if first == "A" else "A"
        return tuple(
            first if index % 2 == 0 else second
            for index in range(self.founder_count)
        )

    @property
    def founder_speeds(self) -> tuple[int, ...]:
        """Return modeled founder speeds in caller/ID order."""
        speed_by_group = {"A": self.group_speeds[0], "B": self.group_speeds[1]}
        return tuple(speed_by_group[group] for group in self.founder_groups)

    @property
    def resource_deposits(self) -> tuple[tuple[int, int, int], ...]:
        """Return E3 corridor coordinates with resources scaled per founder."""
        canonical = build_e3_treatment(
            max_speed=E5_NEUTRAL_SPEED,
            environment="separated_corridor",
        ).resource_deposits
        total_resources = E5_RESOURCE_PER_FOUNDER * self.founder_count
        if total_resources % len(canonical) != 0:
            raise ValueError("E5 resource budget must divide equally across deposits.")
        amount = total_resources // len(canonical)
        return tuple((x, y, amount) for x, y, _ in canonical)

    @property
    def treatment_id(self) -> str:
        """Return a stable treatment identifier."""
        speed_pair = f"{self.group_speeds[0]}-{self.group_speeds[1]}"
        return (
            f"{self.mode}-founders-{self.founder_count}-speeds-{speed_pair}-"
            f"phase-{self.assignment_phase}"
        )

    def to_config(self, *, seed: int) -> ControlledLocomotionConfig:
        """Build one E2 configuration while leaving neutral labels outside biology."""
        validators.validate_int(seed, name="seed")
        return ControlledLocomotionConfig(
            width=E3_WIDTH,
            height=E3_HEIGHT,
            max_steps=E5_HORIZON,
            seed=seed,
            founders=tuple(
                ControlledLocomotionFounder(
                    max_speed=speed,
                    x=E3_FOUNDER_X,
                    y=E3_FOUNDER_Y,
                )
                for speed in self.founder_speeds
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
class E5LineageCompositionPoint:
    """Record complete committed A/B lineage composition at one step."""

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    counts: tuple[int, int]
    frequencies: tuple[float | None, float | None]

    def __attrs_post_init__(self) -> None:
        """Validate complete composition and explicit extinction semantics."""
        if len(self.counts) != 2 or len(self.frequencies) != 2:
            raise ValueError("E5 composition must contain exactly two groups.")
        for index, count in enumerate(self.counts):
            validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
        if sum(self.counts) != self.population_size:
            raise ValueError("lineage counts must equal complete population size.")
        if self.population_size == 0:
            if any(value is not None for value in self.frequencies):
                raise ValueError("extinct lineage frequencies must be undefined.")
            return
        if any(value is None for value in self.frequencies):
            raise ValueError("nonempty lineage frequencies must be defined.")
        defined = tuple(value for value in self.frequencies if value is not None)
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in defined):
            raise ValueError("defined lineage frequencies must be finite in [0, 1].")
        if not math.isclose(sum(defined), 1.0):
            raise ValueError("defined lineage frequencies must sum to one.")

    def count(self, group: E5Group) -> int:
        """Return the committed count for one analysis group."""
        return self.counts[_group_index(group)]

    def frequency(self, group: E5Group) -> float | None:
        """Return the committed frequency for one analysis group."""
        return self.frequencies[_group_index(group)]


@attrs.frozen(slots=True, kw_only=True)
class E5ReplicateOutcome:
    """Store one run-level E5 lineage outcome with explicit censoring."""

    treatment: E5TreatmentSpecification
    provenance: ScientificRunProvenance
    trajectory: tuple[E5LineageCompositionPoint, ...]
    group_a_loss: FixedHorizonTimeToEvent
    group_b_loss: FixedHorizonTimeToEvent
    fixation: FixedHorizonTimeToEvent
    fixation_winner: E5FixationWinner | None
    extinction: FixedHorizonTimeToEvent

    def __attrs_post_init__(self) -> None:
        """Validate trajectory and mutually consistent event semantics."""
        if not isinstance(self.treatment, E5TreatmentSpecification):
            raise TypeError("treatment must be an E5TreatmentSpecification.")
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        validators.validate_tuple(self.trajectory, name="trajectory")
        if not self.trajectory:
            raise ValueError("trajectory must include committed step zero.")
        if self.trajectory[0].step_index != 0:
            raise ValueError("trajectory must begin at committed step zero.")
        if self.trajectory[-1].step_index != E5_HORIZON:
            raise ValueError("trajectory must end at the frozen E5 horizon.")
        if self.trajectory[0].counts[0] != self.trajectory[0].counts[1]:
            raise ValueError("E5 must begin with equal A/B founder counts.")
        for name in ("group_a_loss", "group_b_loss", "fixation", "extinction"):
            if not isinstance(getattr(self, name), FixedHorizonTimeToEvent):
                raise TypeError(f"{name} must be a FixedHorizonTimeToEvent.")
        if self.fixation.right_censored and self.fixation_winner is not None:
            raise ValueError("right-censored fixation must not have a winner.")
        if not self.fixation.right_censored and self.fixation_winner not in ("A", "B"):
            raise ValueError("observed fixation must identify winner A or B.")

    @property
    def initial_composition(self) -> E5LineageCompositionPoint:
        """Return the committed founder composition."""
        return self.trajectory[0]

    @property
    def final_composition(self) -> E5LineageCompositionPoint:
        """Return the committed fixed-horizon composition."""
        return self.trajectory[-1]

    @property
    def final_population_size(self) -> int:
        """Return fixed-horizon population size."""
        return self.final_composition.population_size

    @property
    def group_a_frequency_change(self) -> float | None:
        """Return final-minus-initial A frequency, preserving extinction undefinedness."""
        initial = self.initial_composition.frequency("A")
        final = self.final_composition.frequency("A")
        if initial is None or final is None:
            return None
        return final - initial


@attrs.frozen(slots=True, kw_only=True)
class E5RegimeSummary:
    """Summarize run-level E5 outcomes without organism-level pseudoreplication."""

    mode: E5Mode
    founder_count: int
    weak_pair: tuple[int, int]
    replicate_count: int
    seeds: tuple[int, ...]
    assignment_phases: tuple[int, ...]
    group_a_frequency_changes: tuple[float | None, ...]
    defined_endpoint_count: int
    mean_group_a_frequency_change: float | None
    median_group_a_frequency_change: float | None
    variance_group_a_frequency_change: float | None
    stddev_group_a_frequency_change: float | None
    group_a_increase_proportion: float | None
    group_a_decrease_proportion: float | None
    group_a_unchanged_proportion: float | None
    group_a_loss_proportion: float
    group_b_loss_proportion: float
    any_fixation_proportion: float
    group_a_fixation_proportion: float
    group_b_fixation_proportion: float
    fixation_censored_count: int
    observed_fixation_steps: tuple[int, ...]
    extinction_proportion: float


@attrs.frozen(slots=True, kw_only=True)
class E5WeakVsNeutralComparison:
    """Compare weak-selection shift with matched neutral stochastic spread."""

    founder_count: int
    weak_pair: tuple[int, int]
    neutral_mean_change: float | None
    neutral_stddev: float | None
    weak_mean_change: float | None
    weak_group_a_decrease_proportion: float | None
    weak_group_a_loss_proportion: float
    signal_to_neutral_sd: float | None


def build_e5_treatment(
    *,
    mode: E5Mode,
    founder_count: int,
    assignment_phase: int = 0,
    weak_pair: tuple[int, int] = E5_WEAK_PAIR,
) -> E5TreatmentSpecification:
    """Build one bounded E5 treatment specification."""
    return E5TreatmentSpecification(
        mode=mode,
        founder_count=founder_count,
        assignment_phase=assignment_phase,
        weak_pair=weak_pair,
    )


def assignment_phase_for_replicate(index: int) -> int:
    """Return the predeclared alternating founder-ID assignment phase."""
    validators.validate_int_ge(index, bound=0, name="index")
    return index % 2


def validate_e5_founder_size_integrity(
    control: E5TreatmentSpecification,
    treatment: E5TreatmentSpecification,
) -> None:
    """Require size arms to differ only in founder count/resource scaling."""
    _require_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            founder_count=control.founder_count,
        ),
        declared_difference="founder count with proportional resource scaling",
    )


def validate_e5_mode_integrity(
    neutral: E5TreatmentSpecification,
    weak: E5TreatmentSpecification,
) -> None:
    """Require matched neutral/weak arms to differ only in focal speed composition."""
    _require_treatments(neutral, weak)
    if neutral.mode != "neutral" or weak.mode != "weak_selection":
        raise ValueError("mode integrity requires neutral control and weak treatment.")
    validate_declared_treatment_difference(
        control=neutral,
        normalized_treatment=attrs.evolve(weak, mode="neutral"),
        declared_difference="focal inherited speed composition",
    )


def validate_e5_assignment_phase_integrity(
    control: E5TreatmentSpecification,
    treatment: E5TreatmentSpecification,
) -> None:
    """Require counterbalance arms to differ only in founder assignment phase."""
    _require_treatments(control, treatment)
    validate_declared_treatment_difference(
        control=control,
        normalized_treatment=attrs.evolve(
            treatment,
            assignment_phase=control.assignment_phase,
        ),
        declared_difference="founder analysis-group/strategy assignment phase",
    )


def run_e5_replicate(
    treatment: E5TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None,
) -> E5ReplicateOutcome:
    """Run one E5 replicate and derive lineage dynamics from committed pedigree."""
    _require_treatment(treatment)
    validators.validate_int(seed, name="seed")
    trait_recorder, pedigree_recorder = _run_recorders(treatment, seed=seed)
    observations = _validated_trait_observations(trait_recorder.observations)
    founder_groups = _founder_group_map(pedigree_recorder, treatment=treatment)
    ancestry_groups = _resolve_ancestry_groups(
        pedigree_recorder.records,
        founder_group_map=founder_groups,
    )
    trajectory = tuple(
        _composition_point(
            observation,
            ancestry_groups=ancestry_groups,
            treatment=treatment,
        )
        for observation in observations
    )
    fixation, winner = _fixation_outcome(trajectory)
    outcome = E5ReplicateOutcome(
        treatment=treatment,
        provenance=_scientific_provenance(treatment, seed=seed, run_role=run_role),
        trajectory=trajectory,
        group_a_loss=_group_loss_outcome(trajectory, group="A"),
        group_b_loss=_group_loss_outcome(trajectory, group="B"),
        fixation=fixation,
        fixation_winner=winner,
        extinction=_extinction_outcome(trajectory),
    )
    _validate_loss_fixation_consistency(outcome)
    return outcome


def run_e5_seed_set(
    *,
    mode: E5Mode,
    founder_count: int,
    seeds: Sequence[int],
    run_role: RunRole | None,
    weak_pair: tuple[int, int] = E5_WEAK_PAIR,
) -> tuple[E5ReplicateOutcome, ...]:
    """Run one E5 regime with founder assignment counterbalanced across seeds."""
    validated_seeds = _validated_unique_seeds(seeds)
    return tuple(
        run_e5_replicate(
            build_e5_treatment(
                mode=mode,
                founder_count=founder_count,
                assignment_phase=assignment_phase_for_replicate(index),
                weak_pair=weak_pair,
            ),
            seed=seed,
            run_role=run_role,
        )
        for index, seed in enumerate(validated_seeds)
    )


def summarize_e5_regime(
    outcomes: Sequence[E5ReplicateOutcome],
) -> E5RegimeSummary:
    """Summarize one E5 treatment using simulation runs as replicates."""
    values = tuple(outcomes)
    mode, founder_count, weak_pair = _validate_regime_outcomes(values)
    changes = tuple(outcome.group_a_frequency_change for outcome in values)
    defined_changes = tuple(value for value in changes if value is not None)
    fixation_steps = tuple(
        outcome.fixation.observed_step_index
        for outcome in values
        if outcome.fixation.observed_step_index is not None
    )
    return E5RegimeSummary(
        mode=mode,
        founder_count=founder_count,
        weak_pair=weak_pair,
        replicate_count=len(values),
        seeds=tuple(outcome.provenance.seed for outcome in values),
        assignment_phases=tuple(
            outcome.treatment.assignment_phase for outcome in values
        ),
        group_a_frequency_changes=changes,
        defined_endpoint_count=len(defined_changes),
        mean_group_a_frequency_change=_mean_or_none(defined_changes),
        median_group_a_frequency_change=_median_or_none(defined_changes),
        variance_group_a_frequency_change=_variance_or_none(defined_changes),
        stddev_group_a_frequency_change=_stddev_or_none(defined_changes),
        group_a_increase_proportion=_direction_proportion(
            defined_changes,
            direction="increase",
        ),
        group_a_decrease_proportion=_direction_proportion(
            defined_changes,
            direction="decrease",
        ),
        group_a_unchanged_proportion=_direction_proportion(
            defined_changes,
            direction="unchanged",
        ),
        group_a_loss_proportion=_proportion(
            values,
            lambda outcome: not outcome.group_a_loss.right_censored,
        ),
        group_b_loss_proportion=_proportion(
            values,
            lambda outcome: not outcome.group_b_loss.right_censored,
        ),
        any_fixation_proportion=_proportion(
            values,
            lambda outcome: not outcome.fixation.right_censored,
        ),
        group_a_fixation_proportion=_proportion(
            values,
            lambda outcome: outcome.fixation_winner == "A",
        ),
        group_b_fixation_proportion=_proportion(
            values,
            lambda outcome: outcome.fixation_winner == "B",
        ),
        fixation_censored_count=len(values) - len(fixation_steps),
        observed_fixation_steps=fixation_steps,
        extinction_proportion=_proportion(
            values,
            lambda outcome: not outcome.extinction.right_censored,
        ),
    )


def compare_e5_weak_to_neutral(
    neutral: E5RegimeSummary,
    weak: E5RegimeSummary,
) -> E5WeakVsNeutralComparison:
    """Compare weak-selection shift with neutral stochastic spread at one size."""
    if not isinstance(neutral, E5RegimeSummary) or not isinstance(weak, E5RegimeSummary):
        raise TypeError("neutral and weak must be E5RegimeSummary values.")
    if neutral.mode != "neutral" or weak.mode != "weak_selection":
        raise ValueError("comparison requires neutral and weak_selection summaries.")
    if neutral.founder_count != weak.founder_count:
        raise ValueError("neutral and weak summaries must use the same founder count.")
    ratio: float | None = None
    if (
        neutral.stddev_group_a_frequency_change is not None
        and neutral.stddev_group_a_frequency_change > 0.0
        and weak.mean_group_a_frequency_change is not None
    ):
        ratio = (
            abs(weak.mean_group_a_frequency_change)
            / neutral.stddev_group_a_frequency_change
        )
    return E5WeakVsNeutralComparison(
        founder_count=neutral.founder_count,
        weak_pair=weak.weak_pair,
        neutral_mean_change=neutral.mean_group_a_frequency_change,
        neutral_stddev=neutral.stddev_group_a_frequency_change,
        weak_mean_change=weak.mean_group_a_frequency_change,
        weak_group_a_decrease_proportion=weak.group_a_decrease_proportion,
        weak_group_a_loss_proportion=weak.group_a_loss_proportion,
        signal_to_neutral_sd=ratio,
    )


def _run_recorders(
    treatment: E5TreatmentSpecification,
    *,
    seed: int,
) -> tuple[IndividualGeneticTraitRecorder, PedigreeRecorder]:
    trait_recorder = IndividualGeneticTraitRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=True,
    )
    pedigree_recorder = PedigreeRecorder()
    spec = build_controlled_locomotion_spec(
        treatment.to_config(seed=seed),
        observers=(trait_recorder, pedigree_recorder),
        telemetry_observers=(pedigree_recorder,),
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)
    return trait_recorder, pedigree_recorder


def _validated_trait_observations(
    observations: tuple[IndividualGeneticTraitObservation, ...],
) -> tuple[IndividualGeneticTraitObservation, ...]:
    validators.validate_tuple(observations, name="observations")
    if not observations:
        raise ValueError("E5 requires committed individual-trait observations.")
    expected_steps = tuple(range(E5_HORIZON + 1))
    actual_steps = tuple(observation.step_index for observation in observations)
    if actual_steps != expected_steps:
        raise ValueError("E5 requires every committed step from zero through horizon.")
    for observation in observations:
        if observation.trait_names != (MAX_SPEED,):
            raise ValueError("E5 individual evidence must contain only max_speed.")
    return observations


def _founder_group_map(
    pedigree: PedigreeRecorder,
    *,
    treatment: E5TreatmentSpecification,
) -> dict[int, E5Group]:
    founder_ids = pedigree.founder_ids
    if len(founder_ids) != treatment.founder_count:
        raise ValueError("pedigree founder count does not match E5 treatment.")
    return dict(zip(founder_ids, treatment.founder_groups, strict=True))


def _resolve_ancestry_groups(
    records: tuple[IndividualLifeHistory, ...],
    *,
    founder_group_map: dict[int, E5Group],
) -> dict[int, E5Group]:
    """Resolve every organism to one analysis-only founder ancestry group."""
    record_by_id = {record.organism_id: record for record in records}
    if len(record_by_id) != len(records):
        raise ValueError("pedigree records must contain unique organism IDs.")
    resolved: dict[int, E5Group] = dict(founder_group_map)
    visiting: set[int] = set()

    def resolve(organism_id: int) -> E5Group:
        if organism_id in resolved:
            return resolved[organism_id]
        if organism_id in visiting:
            raise ValueError("pedigree ancestry contains a cycle.")
        try:
            record = record_by_id[organism_id]
        except KeyError as error:
            raise ValueError(
                f"organism {organism_id} is absent from pedigree records."
            ) from error
        if record.is_founder:
            raise ValueError(
                f"founder {organism_id} is missing its analysis-only group assignment."
            )
        if len(record.parent_ids) != 1:
            raise ValueError(
                "E5 controlled clonal descendants must have exactly one recorded parent."
            )
        visiting.add(organism_id)
        group = resolve(record.parent_ids[0])
        visiting.remove(organism_id)
        resolved[organism_id] = group
        return group

    for organism_id in record_by_id:
        resolve(organism_id)
    return resolved


def _composition_point(
    observation: IndividualGeneticTraitObservation,
    *,
    ancestry_groups: dict[int, E5Group],
    treatment: E5TreatmentSpecification,
) -> E5LineageCompositionPoint:
    counts: dict[E5Group, int] = {"A": 0, "B": 0}
    expected_speed: dict[E5Group, int] = {
        "A": treatment.group_speeds[0],
        "B": treatment.group_speeds[1],
    }
    for individual in observation.individuals:
        try:
            group = ancestry_groups[individual.organism_id]
        except KeyError as error:
            raise ValueError(
                f"active organism {individual.organism_id} has no resolved ancestry group."
            ) from error
        observed_speed = observation.trait_value(individual.organism_id, MAX_SPEED)
        if observed_speed != expected_speed[group]:
            raise ValueError(
                "E5 clonal descendant speed does not match its founder-group speed."
            )
        counts[group] += 1
    population_size = len(observation.individuals)
    frequencies: tuple[float | None, float | None]
    if population_size == 0:
        frequencies = (None, None)
    else:
        frequencies = (
            counts["A"] / population_size,
            counts["B"] / population_size,
        )
    return E5LineageCompositionPoint(
        step_index=observation.step_index,
        population_size=population_size,
        counts=(counts["A"], counts["B"]),
        frequencies=frequencies,
    )


def _group_loss_outcome(
    trajectory: tuple[E5LineageCompositionPoint, ...],
    *,
    group: E5Group,
) -> FixedHorizonTimeToEvent:
    observed = next(
        (point.step_index for point in trajectory[1:] if point.count(group) == 0),
        None,
    )
    return FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=E5_HORIZON,
        observed_step_index=observed,
    )


def _fixation_outcome(
    trajectory: tuple[E5LineageCompositionPoint, ...],
) -> tuple[FixedHorizonTimeToEvent, E5FixationWinner | None]:
    for point in trajectory[1:]:
        if point.population_size == 0:
            continue
        if point.counts[0] == 0:
            return (
                FixedHorizonTimeToEvent(
                    start_step_index=0,
                    horizon_step_index=E5_HORIZON,
                    observed_step_index=point.step_index,
                ),
                "B",
            )
        if point.counts[1] == 0:
            return (
                FixedHorizonTimeToEvent(
                    start_step_index=0,
                    horizon_step_index=E5_HORIZON,
                    observed_step_index=point.step_index,
                ),
                "A",
            )
    return (
        FixedHorizonTimeToEvent(
            start_step_index=0,
            horizon_step_index=E5_HORIZON,
        ),
        None,
    )


def _extinction_outcome(
    trajectory: tuple[E5LineageCompositionPoint, ...],
) -> FixedHorizonTimeToEvent:
    observed = next(
        (point.step_index for point in trajectory[1:] if point.population_size == 0),
        None,
    )
    return FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=E5_HORIZON,
        observed_step_index=observed,
    )


def _validate_loss_fixation_consistency(outcome: E5ReplicateOutcome) -> None:
    fixation_step = outcome.fixation.observed_step_index
    if fixation_step is None:
        return
    losing_loss = (
        outcome.group_b_loss
        if outcome.fixation_winner == "A"
        else outcome.group_a_loss
    )
    if losing_loss.observed_step_index != fixation_step:
        raise ValueError("fixation must coincide with first loss of losing lineage.")


def _scientific_provenance(
    treatment: E5TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None,
) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="e5-drift-population-size-weak-selection",
        scenario_id="e2-controlled-separated-corridor",
        treatment_id=treatment.treatment_id,
        treatment_specification_json=canonical_treatment_specification(
            {
                "mode": treatment.mode,
                "founder_count": treatment.founder_count,
                "assignment_phase": treatment.assignment_phase,
                "group_speeds": treatment.group_speeds,
                "resource_deposits": treatment.resource_deposits,
                "resource_per_founder": E5_RESOURCE_PER_FOUNDER,
                "horizon": E5_HORIZON,
            }
        ),
        seed=seed,
        horizon_step_index=E5_HORIZON,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=(
            "group_a_frequency",
            "group_b_frequency",
            "lineage_loss",
            "fixation",
            "extinction",
        ),
        run_role=run_role,
    )


def _validated_unique_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    values = tuple(seeds)
    if not values:
        raise ValueError("seeds must not be empty.")
    for index, seed in enumerate(values):
        validators.validate_int(seed, name=f"seeds[{index}]")
    if len(values) != len(set(values)):
        raise ValueError("seeds must not contain duplicates.")
    return values


def _validate_regime_outcomes(
    values: tuple[E5ReplicateOutcome, ...],
) -> tuple[E5Mode, int, tuple[int, int]]:
    if not values:
        raise ValueError("outcomes must not be empty.")
    if any(not isinstance(value, E5ReplicateOutcome) for value in values):
        raise TypeError("outcomes must contain only E5ReplicateOutcome values.")
    first = values[0].treatment
    for outcome in values[1:]:
        treatment = outcome.treatment
        if treatment.mode != first.mode:
            raise ValueError("regime outcomes must share one mode.")
        if treatment.founder_count != first.founder_count:
            raise ValueError("regime outcomes must share one founder count.")
        if treatment.weak_pair != first.weak_pair:
            raise ValueError("regime outcomes must share one weak pair.")
    seeds = tuple(outcome.provenance.seed for outcome in values)
    if len(seeds) != len(set(seeds)):
        raise ValueError("regime outcomes must have unique replicate seeds.")
    return first.mode, first.founder_count, first.weak_pair


def _mean_or_none(values: tuple[float, ...]) -> float | None:
    return statistics.fmean(values) if values else None


def _median_or_none(values: tuple[float, ...]) -> float | None:
    return float(statistics.median(values)) if values else None


def _variance_or_none(values: tuple[float, ...]) -> float | None:
    return statistics.variance(values) if len(values) >= 2 else None


def _stddev_or_none(values: tuple[float, ...]) -> float | None:
    return statistics.stdev(values) if len(values) >= 2 else None


def _direction_proportion(
    values: tuple[float, ...],
    *,
    direction: Literal["increase", "decrease", "unchanged"],
) -> float | None:
    if not values:
        return None
    if direction == "increase":
        count = sum(value > 0.0 for value in values)
    elif direction == "decrease":
        count = sum(value < 0.0 for value in values)
    else:
        count = sum(math.isclose(value, 0.0, abs_tol=1e-12) for value in values)
    return count / len(values)


def _proportion(
    values: tuple[E5ReplicateOutcome, ...],
    predicate: Callable[[E5ReplicateOutcome], bool],
) -> float:
    if not values:
        raise ValueError("values must not be empty.")
    return sum(predicate(value) for value in values) / len(values)


def _group_index(group: E5Group) -> int:
    validated = validators.validate_str(group, name="group")
    if validated == "A":
        return 0
    if validated == "B":
        return 1
    raise ValueError("group must be 'A' or 'B'.")


def _require_treatment(value: object) -> E5TreatmentSpecification:
    if not isinstance(value, E5TreatmentSpecification):
        raise TypeError("treatment must be an E5TreatmentSpecification.")
    return value


def _require_treatments(
    first: object,
    second: object,
) -> tuple[E5TreatmentSpecification, E5TreatmentSpecification]:
    return _require_treatment(first), _require_treatment(second)
