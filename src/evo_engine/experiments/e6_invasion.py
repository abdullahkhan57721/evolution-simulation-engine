"""Controlled E6 rare-lineage invasion above E2/E5 scientific contracts."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections.abc import Sequence
from typing import Literal

import attrs

from evo_engine.engine import MaxSteps, Simulation, SimulationEngine, SimulationState, StepCoordinator
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
from evo_engine.experiments.e5_drift import E5_RESOURCE_PER_FOUNDER
from evo_engine.experiments.science import (
    FixedHorizonTimeToEvent,
    RunRole,
    ScientificRunProvenance,
    canonical_treatment_specification,
    validate_declared_treatment_difference,
)
from evo_engine.genetics import GENETIC_ARCHITECTURE, MAX_SPEED, GeneticArchitecture
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
    build_controlled_locomotion_founder_genome,
    build_controlled_locomotion_spec,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world import Organism, WorldState

E6ArmRole = Literal["neutral", "mutant"]
E6Lineage = Literal["resident", "rare"]
E6FixationWinner = Literal["resident", "rare"]

E6_DISCOVERY_SEEDS: tuple[int, ...] = (13, 31, 47, 73, 101, 127)
E6_CONFIRMATION_SEEDS: tuple[int, ...] = (
    367,
    373,
    379,
    383,
    389,
    397,
    401,
    409,
    419,
    421,
    431,
    433,
    439,
    443,
    449,
    457,
    461,
    463,
    467,
    479,
    487,
    491,
    499,
    503,
)
E6_RECIPROCAL_PAIRS: tuple[tuple[int, int], ...] = ((4, 3), (3, 4))
E6_RESIDENT_FOUNDER_COUNT = 8
E6_BURN_IN_STEPS = 20
E6_POST_INTRODUCTION_STEPS = 40
E6_HORIZON = E6_BURN_IN_STEPS + E6_POST_INTRODUCTION_STEPS
E6_ENTRANT_AGE = 0
E6_ENTRANT_ENERGY = E3_REPRODUCTION_ENERGY_INVESTMENT
E6_ENTRANT_BODY_MASS = E3_BODY_MASS
E6_ENTRANT_MATING_TYPE = "clonal"
E6_ENTRANT_X = E3_FOUNDER_X
E6_ENTRANT_Y = E3_FOUNDER_Y

_E6_RESIDENT_SPEEDS = frozenset(pair[0] for pair in E6_RECIPROCAL_PAIRS)
_E6_ROLES = frozenset({"neutral", "mutant"})


@attrs.frozen(slots=True, kw_only=True)
class E6TreatmentSpecification:
    """Define one matched neutral or mutant rare-lineage invasion arm."""

    role: E6ArmRole
    resident_speed: int
    entrant_speed: int

    def __attrs_post_init__(self) -> None:
        """Validate the frozen reciprocal E6 treatment space."""
        validated_role = validators.validate_str(self.role, name="role")
        if validated_role not in _E6_ROLES:
            raise ValueError("role must be 'neutral' or 'mutant'.")
        validators.validate_int(self.resident_speed, name="resident_speed")
        validators.validate_int(self.entrant_speed, name="entrant_speed")
        if self.resident_speed not in _E6_RESIDENT_SPEEDS:
            raise ValueError("resident_speed must be 3 or 4.")
        if self.role == "neutral":
            if self.entrant_speed != self.resident_speed:
                raise ValueError("neutral entrant_speed must equal resident_speed.")
            return
        if (self.resident_speed, self.entrant_speed) not in E6_RECIPROCAL_PAIRS:
            raise ValueError("mutant arm must use one frozen reciprocal 3↔4 pair.")

    @property
    def treatment_id(self) -> str:
        """Return a stable E6 treatment identifier."""
        return (
            f"{self.role}-resident-{self.resident_speed}-"
            f"entrant-{self.entrant_speed}"
        )

    @property
    def resource_deposits(self) -> tuple[tuple[int, int, int], ...]:
        """Return E3 corridor coordinates at E5's corrected per-founder scale."""
        canonical = build_e3_treatment(
            max_speed=self.resident_speed,
            environment="separated_corridor",
        ).resource_deposits
        total = E5_RESOURCE_PER_FOUNDER * E6_RESIDENT_FOUNDER_COUNT
        if total % len(canonical) != 0:
            raise ValueError("E6 resource budget must divide equally across deposits.")
        amount = total // len(canonical)
        return tuple((x, y, amount) for x, y, _ in canonical)

    def to_burn_in_config(self, *, seed: int) -> ControlledLocomotionConfig:
        """Build the monomorphic resident-only burn-in configuration."""
        validators.validate_int(seed, name="seed")
        return ControlledLocomotionConfig(
            width=E3_WIDTH,
            height=E3_HEIGHT,
            max_steps=E6_BURN_IN_STEPS,
            seed=seed,
            founders=tuple(
                ControlledLocomotionFounder(
                    max_speed=self.resident_speed,
                    x=E3_FOUNDER_X,
                    y=E3_FOUNDER_Y,
                )
                for _ in range(E6_RESIDENT_FOUNDER_COUNT)
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
class E6BurnInCheckpoint:
    """Record experiment-level provenance for one exact in-memory burn-in state."""

    seed: int
    resident_speed: int
    step_index: int
    population_size: int
    resource_total: int
    organism_ids: tuple[int, ...]
    world_state_sha256: str
    rng_state_sha256: str

    def __attrs_post_init__(self) -> None:
        """Validate burn-in checkpoint metadata."""
        validators.validate_int(self.seed, name="seed")
        validators.validate_int(self.resident_speed, name="resident_speed")
        if self.resident_speed not in _E6_RESIDENT_SPEEDS:
            raise ValueError("resident_speed must be 3 or 4.")
        validators.validate_int_ge(self.step_index, bound=0, name="step_index")
        if self.step_index != E6_BURN_IN_STEPS:
            raise ValueError("E6 burn-in checkpoint must use the frozen burn-in step.")
        validators.validate_int_ge(self.population_size, bound=1, name="population_size")
        validators.validate_int_ge(self.resource_total, bound=0, name="resource_total")
        validators.validate_tuple(self.organism_ids, name="organism_ids")
        if len(self.organism_ids) != self.population_size:
            raise ValueError("organism_ids must represent the complete burn-in population.")
        if tuple(sorted(self.organism_ids)) != self.organism_ids:
            raise ValueError("organism_ids must be in deterministic increasing order.")
        if len(set(self.organism_ids)) != len(self.organism_ids):
            raise ValueError("organism_ids must be unique.")
        _validate_sha256(self.world_state_sha256, name="world_state_sha256")
        _validate_sha256(self.rng_state_sha256, name="rng_state_sha256")


@attrs.frozen(slots=True, kw_only=True)
class E6InterventionRecord:
    """Describe the explicit external newborn-like admission used by E6."""

    mechanism: str
    step_index: int
    organism_id: int
    resident_population_size_before: int
    initial_rare_frequency: float
    role: E6ArmRole
    resident_speed: int
    entrant_speed: int
    age: int
    energy: int
    body_mass: int
    mating_type: str
    x: int
    y: int

    def __attrs_post_init__(self) -> None:
        """Validate explicit intervention semantics and fixed entrant state."""
        if self.mechanism != "experiment_external_newborn_like_admission":
            raise ValueError("E6 intervention mechanism is fixed and explicit.")
        if self.step_index != E6_BURN_IN_STEPS:
            raise ValueError("E6 intervention must occur at the burn-in boundary.")
        validators.validate_int_ge(self.organism_id, bound=0, name="organism_id")
        validators.validate_int_ge(
            self.resident_population_size_before,
            bound=1,
            name="resident_population_size_before",
        )
        expected_frequency = 1.0 / (self.resident_population_size_before + 1)
        if not math.isclose(self.initial_rare_frequency, expected_frequency):
            raise ValueError("initial_rare_frequency must match one admitted organism.")
        E6TreatmentSpecification(
            role=self.role,
            resident_speed=self.resident_speed,
            entrant_speed=self.entrant_speed,
        )
        fixed_values = (
            (self.age, E6_ENTRANT_AGE, "age"),
            (self.energy, E6_ENTRANT_ENERGY, "energy"),
            (self.body_mass, E6_ENTRANT_BODY_MASS, "body_mass"),
            (self.x, E6_ENTRANT_X, "x"),
            (self.y, E6_ENTRANT_Y, "y"),
        )
        for actual, expected, name in fixed_values:
            if actual != expected:
                raise ValueError(f"E6 entrant {name} must equal {expected}.")
        if self.mating_type != E6_ENTRANT_MATING_TYPE:
            raise ValueError("E6 entrant mating_type must be 'clonal'.")


@attrs.frozen(slots=True, kw_only=True)
class E6LineageCompositionPoint:
    """Record complete resident/rare composition at one committed state."""

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    counts: tuple[int, int]
    frequencies: tuple[float | None, float | None]

    def __attrs_post_init__(self) -> None:
        """Validate complete composition and extinction-aware frequencies."""
        if len(self.counts) != 2 or len(self.frequencies) != 2:
            raise ValueError("E6 composition must contain resident and rare lineages.")
        for index, count in enumerate(self.counts):
            validators.validate_int_ge(count, bound=0, name=f"counts[{index}]")
        if sum(self.counts) != self.population_size:
            raise ValueError("lineage counts must equal complete population size.")
        _validate_frequencies(
            population_size=self.population_size,
            frequencies=self.frequencies,
        )

    def count(self, lineage: E6Lineage) -> int:
        """Return one lineage count."""
        return self.counts[_lineage_index(lineage)]

    def frequency(self, lineage: E6Lineage) -> float | None:
        """Return one lineage frequency, undefined after extinction."""
        return self.frequencies[_lineage_index(lineage)]


@attrs.frozen(slots=True, kw_only=True)
class E6ReplicateOutcome:
    """Store one post-introduction E6 arm with explicit event censoring."""

    treatment: E6TreatmentSpecification
    provenance: ScientificRunProvenance
    burn_in_checkpoint: E6BurnInCheckpoint
    intervention: E6InterventionRecord
    trajectory: tuple[E6LineageCompositionPoint, ...]
    rare_expansion: FixedHorizonTimeToEvent
    rare_loss: FixedHorizonTimeToEvent
    fixation: FixedHorizonTimeToEvent
    fixation_winner: E6FixationWinner | None
    extinction: FixedHorizonTimeToEvent
    rare_birth_count: int

    def __attrs_post_init__(self) -> None:
        """Validate paired intervention, trajectory, and censoring semantics."""
        if not isinstance(self.treatment, E6TreatmentSpecification):
            raise TypeError("treatment must be an E6TreatmentSpecification.")
        if not isinstance(self.provenance, ScientificRunProvenance):
            raise TypeError("provenance must be a ScientificRunProvenance.")
        if not isinstance(self.burn_in_checkpoint, E6BurnInCheckpoint):
            raise TypeError("burn_in_checkpoint must be an E6BurnInCheckpoint.")
        if not isinstance(self.intervention, E6InterventionRecord):
            raise TypeError("intervention must be an E6InterventionRecord.")
        validators.validate_tuple(self.trajectory, name="trajectory")
        if not self.trajectory:
            raise ValueError("trajectory must include the post-introduction baseline.")
        if self.trajectory[0].step_index != E6_BURN_IN_STEPS:
            raise ValueError("trajectory must begin at the intervention baseline.")
        if self.trajectory[-1].step_index != E6_HORIZON:
            raise ValueError("trajectory must end at the frozen E6 horizon.")
        initial = self.trajectory[0]
        if initial.count("rare") != 1:
            raise ValueError("E6 must begin post-intervention with one rare organism.")
        if initial.count("resident") != self.intervention.resident_population_size_before:
            raise ValueError("initial resident count must match intervention provenance.")
        if not math.isclose(
            initial.frequency("rare") or 0.0,
            self.intervention.initial_rare_frequency,
        ):
            raise ValueError("initial rare frequency must match intervention provenance.")
        for name in ("rare_expansion", "rare_loss", "fixation", "extinction"):
            if not isinstance(getattr(self, name), FixedHorizonTimeToEvent):
                raise TypeError(f"{name} must be a FixedHorizonTimeToEvent.")
        if self.fixation.right_censored and self.fixation_winner is not None:
            raise ValueError("right-censored fixation must not have a winner.")
        if not self.fixation.right_censored and self.fixation_winner is None:
            raise ValueError("observed fixation must identify a winner.")
        validators.validate_int_ge(self.rare_birth_count, bound=0, name="rare_birth_count")

    @property
    def initial_composition(self) -> E6LineageCompositionPoint:
        """Return the immediate post-introduction baseline."""
        return self.trajectory[0]

    @property
    def final_composition(self) -> E6LineageCompositionPoint:
        """Return the fixed-horizon composition."""
        return self.trajectory[-1]

    @property
    def rare_frequency_change(self) -> float | None:
        """Return final-minus-initial rare frequency."""
        initial = self.initial_composition.frequency("rare")
        final = self.final_composition.frequency("rare")
        if initial is None or final is None:
            return None
        return final - initial

    @property
    def rare_count_change(self) -> int:
        """Return final-minus-initial rare-lineage count."""
        return self.final_composition.count("rare") - 1


@attrs.frozen(slots=True, kw_only=True)
class E6InvasionPairOutcome:
    """Store one exact burn-in checkpoint with matched neutral/mutant arms."""

    neutral: E6ReplicateOutcome
    mutant: E6ReplicateOutcome

    def __attrs_post_init__(self) -> None:
        """Validate exact matched-pair provenance and intervention state."""
        if not isinstance(self.neutral, E6ReplicateOutcome) or not isinstance(
            self.mutant, E6ReplicateOutcome
        ):
            raise TypeError("neutral and mutant must be E6ReplicateOutcome values.")
        validate_e6_matched_arm_integrity(
            self.neutral.treatment,
            self.mutant.treatment,
        )
        if self.neutral.burn_in_checkpoint != self.mutant.burn_in_checkpoint:
            raise ValueError("matched E6 arms must share one exact burn-in checkpoint.")
        if self.neutral.provenance.seed != self.mutant.provenance.seed:
            raise ValueError("matched E6 arms must share one seed.")
        _validate_matched_interventions(self.neutral.intervention, self.mutant.intervention)


@attrs.frozen(slots=True, kw_only=True)
class E6ArmSummary:
    """Summarize one E6 arm using simulation runs as replicates."""

    role: E6ArmRole
    resident_speed: int
    entrant_speed: int
    replicate_count: int
    seeds: tuple[int, ...]
    rare_frequency_changes: tuple[float | None, ...]
    defined_endpoint_count: int
    mean_rare_frequency_change: float | None
    median_rare_frequency_change: float | None
    rare_increase_proportion: float | None
    rare_decrease_proportion: float | None
    rare_unchanged_proportion: float | None
    rare_expansion_proportion: float
    rare_loss_proportion: float
    fixation_proportion: float
    extinction_proportion: float
    mean_rare_birth_count: float


@attrs.frozen(slots=True, kw_only=True)
class E6MatchedInvasionComparison:
    """Compare mutant invasion against the matched neutral rare-entry baseline."""

    resident_speed: int
    mutant_speed: int
    replicate_count: int
    seeds: tuple[int, ...]
    paired_frequency_contrasts: tuple[float | None, ...]
    defined_pair_count: int
    mean_paired_frequency_contrast: float | None
    median_paired_frequency_contrast: float | None
    positive_pair_proportion: float | None
    negative_pair_proportion: float | None
    unchanged_pair_proportion: float | None
    neutral_expansion_proportion: float
    mutant_expansion_proportion: float
    neutral_loss_proportion: float
    mutant_loss_proportion: float


def build_e6_treatment(
    *,
    role: E6ArmRole,
    resident_speed: int,
    entrant_speed: int,
) -> E6TreatmentSpecification:
    """Build one bounded E6 treatment specification."""
    return E6TreatmentSpecification(
        role=role,
        resident_speed=resident_speed,
        entrant_speed=entrant_speed,
    )


def validate_e6_matched_arm_integrity(
    neutral: E6TreatmentSpecification,
    mutant: E6TreatmentSpecification,
) -> None:
    """Require paired arms to differ only in admitted entrant speed/role."""
    _require_treatment(neutral)
    _require_treatment(mutant)
    if neutral.role != "neutral" or mutant.role != "mutant":
        raise ValueError("matched integrity requires neutral and mutant arms.")
    if neutral.resident_speed != mutant.resident_speed:
        raise ValueError("matched E6 arms must use the same resident speed.")
    validate_declared_treatment_difference(
        control=neutral,
        normalized_treatment=attrs.evolve(
            mutant,
            role="neutral",
            entrant_speed=neutral.entrant_speed,
        ),
        declared_difference="externally admitted entrant max_speed",
    )


def run_e6_invasion_pair(
    *,
    resident_speed: int,
    mutant_speed: int,
    seed: int,
    run_role: RunRole | None,
) -> E6InvasionPairOutcome:
    """Run one reciprocal invasion pair from a shared exact resident checkpoint."""
    validators.validate_int(seed, name="seed")
    neutral = build_e6_treatment(
        role="neutral",
        resident_speed=resident_speed,
        entrant_speed=resident_speed,
    )
    mutant = build_e6_treatment(
        role="mutant",
        resident_speed=resident_speed,
        entrant_speed=mutant_speed,
    )
    validate_e6_matched_arm_integrity(neutral, mutant)

    compiled = build_controlled_locomotion_spec(neutral.to_burn_in_config(seed=seed)).compile()
    compiled.engine.run(compiled.simulation)
    checkpoint_state = compiled.simulation.state.copy()
    checkpoint = _burn_in_checkpoint(
        checkpoint_state,
        seed=seed,
        resident_speed=resident_speed,
    )
    neutral_outcome = _run_from_checkpoint(
        checkpoint_state,
        checkpoint=checkpoint,
        step_coordinator=compiled.engine.step_coordinator,
        treatment=neutral,
        seed=seed,
        run_role=run_role,
    )
    mutant_outcome = _run_from_checkpoint(
        checkpoint_state,
        checkpoint=checkpoint,
        step_coordinator=compiled.engine.step_coordinator,
        treatment=mutant,
        seed=seed,
        run_role=run_role,
    )
    return E6InvasionPairOutcome(neutral=neutral_outcome, mutant=mutant_outcome)


def run_e6_seed_set(
    *,
    resident_speed: int,
    mutant_speed: int,
    seeds: Sequence[int],
    run_role: RunRole | None,
) -> tuple[E6InvasionPairOutcome, ...]:
    """Run one reciprocal resident/mutant pair across unique replicate seeds."""
    validated_seeds = _validated_unique_seeds(seeds)
    return tuple(
        run_e6_invasion_pair(
            resident_speed=resident_speed,
            mutant_speed=mutant_speed,
            seed=seed,
            run_role=run_role,
        )
        for seed in validated_seeds
    )


def summarize_e6_arm(outcomes: Sequence[E6ReplicateOutcome]) -> E6ArmSummary:
    """Summarize one E6 arm without organism-level pseudoreplication."""
    values = tuple(outcomes)
    treatment = _validate_arm_outcomes(values)
    changes = tuple(value.rare_frequency_change for value in values)
    defined = tuple(value for value in changes if value is not None)
    return E6ArmSummary(
        role=treatment.role,
        resident_speed=treatment.resident_speed,
        entrant_speed=treatment.entrant_speed,
        replicate_count=len(values),
        seeds=tuple(value.provenance.seed for value in values),
        rare_frequency_changes=changes,
        defined_endpoint_count=len(defined),
        mean_rare_frequency_change=_mean_or_none(defined),
        median_rare_frequency_change=_median_or_none(defined),
        rare_increase_proportion=_direction_proportion(defined, direction="increase"),
        rare_decrease_proportion=_direction_proportion(defined, direction="decrease"),
        rare_unchanged_proportion=_direction_proportion(defined, direction="unchanged"),
        rare_expansion_proportion=_proportion(
            values,
            lambda value: not value.rare_expansion.right_censored,
        ),
        rare_loss_proportion=_proportion(
            values,
            lambda value: not value.rare_loss.right_censored,
        ),
        fixation_proportion=_proportion(
            values,
            lambda value: not value.fixation.right_censored,
        ),
        extinction_proportion=_proportion(
            values,
            lambda value: not value.extinction.right_censored,
        ),
        mean_rare_birth_count=statistics.fmean(value.rare_birth_count for value in values),
    )


def compare_e6_matched_invasion(
    neutral: E6ArmSummary,
    mutant: E6ArmSummary,
) -> E6MatchedInvasionComparison:
    """Compare mutant rare-lineage change against its exact matched neutral baseline."""
    if not isinstance(neutral, E6ArmSummary) or not isinstance(mutant, E6ArmSummary):
        raise TypeError("neutral and mutant must be E6ArmSummary values.")
    if neutral.role != "neutral" or mutant.role != "mutant":
        raise ValueError("comparison requires neutral and mutant summaries.")
    if neutral.resident_speed != mutant.resident_speed:
        raise ValueError("comparison requires one resident background.")
    if neutral.seeds != mutant.seeds:
        raise ValueError("matched comparison requires identical ordered seed sets.")
    contrasts = tuple(
        _paired_difference(neutral_value, mutant_value)
        for neutral_value, mutant_value in zip(
            neutral.rare_frequency_changes,
            mutant.rare_frequency_changes,
            strict=True,
        )
    )
    defined = tuple(value for value in contrasts if value is not None)
    return E6MatchedInvasionComparison(
        resident_speed=neutral.resident_speed,
        mutant_speed=mutant.entrant_speed,
        replicate_count=neutral.replicate_count,
        seeds=neutral.seeds,
        paired_frequency_contrasts=contrasts,
        defined_pair_count=len(defined),
        mean_paired_frequency_contrast=_mean_or_none(defined),
        median_paired_frequency_contrast=_median_or_none(defined),
        positive_pair_proportion=_direction_proportion(defined, direction="increase"),
        negative_pair_proportion=_direction_proportion(defined, direction="decrease"),
        unchanged_pair_proportion=_direction_proportion(defined, direction="unchanged"),
        neutral_expansion_proportion=neutral.rare_expansion_proportion,
        mutant_expansion_proportion=mutant.rare_expansion_proportion,
        neutral_loss_proportion=neutral.rare_loss_proportion,
        mutant_loss_proportion=mutant.rare_loss_proportion,
    )


def _run_from_checkpoint(
    checkpoint_state: SimulationState,
    *,
    checkpoint: E6BurnInCheckpoint,
    step_coordinator: StepCoordinator,
    treatment: E6TreatmentSpecification,
    seed: int,
    run_role: RunRole | None,
) -> E6ReplicateOutcome:
    simulation = Simulation(
        checkpoint_state.domain_state,
        context=checkpoint_state.context,
    )
    simulation.state = checkpoint_state.copy()
    intervention = _admit_rare_entrant(simulation.state, treatment=treatment)

    trait_recorder = IndividualGeneticTraitRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=False,
    )
    pedigree_recorder = PedigreeRecorder()
    engine = SimulationEngine(
        step_coordinator,
        MaxSteps(max_steps=E6_HORIZON),
        observers=(trait_recorder, pedigree_recorder),
        telemetry_observers=(pedigree_recorder,),
    )
    engine.run(simulation)

    observations = _validated_trait_observations(trait_recorder.observations)
    lineage_by_id = _resolve_lineages(
        pedigree_recorder.records,
        rare_baseline_id=intervention.organism_id,
    )
    trajectory = tuple(
        _composition_point(
            observation,
            lineage_by_id=lineage_by_id,
            treatment=treatment,
        )
        for observation in observations
    )
    fixation, winner = _fixation_outcome(trajectory)
    outcome = E6ReplicateOutcome(
        treatment=treatment,
        provenance=_scientific_provenance(treatment, seed=seed, run_role=run_role),
        burn_in_checkpoint=checkpoint,
        intervention=intervention,
        trajectory=trajectory,
        rare_expansion=_time_to_event(
            trajectory,
            predicate=lambda point: point.count("rare") >= 2,
        ),
        rare_loss=_time_to_event(
            trajectory,
            predicate=lambda point: point.count("rare") == 0
            and point.count("resident") > 0,
        ),
        fixation=fixation,
        fixation_winner=winner,
        extinction=_time_to_event(
            trajectory,
            predicate=lambda point: point.population_size == 0,
        ),
        rare_birth_count=_rare_birth_count(
            pedigree_recorder.records,
            lineage_by_id=lineage_by_id,
        ),
    )
    _validate_outcome_event_consistency(outcome)
    return outcome


def _burn_in_checkpoint(
    state: SimulationState,
    *,
    seed: int,
    resident_speed: int,
) -> E6BurnInCheckpoint:
    if state.step_index != E6_BURN_IN_STEPS:
        raise ValueError("resident burn-in did not reach the frozen E6 step.")
    world = _world_state(state)
    organism_ids = tuple(sorted(world.organisms))
    if not organism_ids:
        raise ValueError("resident burn-in population must remain nonempty.")
    _validate_world_resident_speed(world, state=state, resident_speed=resident_speed)
    return E6BurnInCheckpoint(
        seed=seed,
        resident_speed=resident_speed,
        step_index=state.step_index,
        population_size=len(organism_ids),
        resource_total=sum(world.resources.values()),
        organism_ids=organism_ids,
        world_state_sha256=_world_state_sha256(world, state=state),
        rng_state_sha256=_sha256(repr(state.rng.getstate()).encode("utf-8")),
    )


def _admit_rare_entrant(
    state: SimulationState,
    *,
    treatment: E6TreatmentSpecification,
) -> E6InterventionRecord:
    world = _world_state(state)
    resident_population_size_before = len(world.organisms)
    if resident_population_size_before < 1:
        raise ValueError("E6 cannot admit a rare lineage into an empty resident world.")
    architecture = state.context.require(GENETIC_ARCHITECTURE)
    if not isinstance(architecture, GeneticArchitecture):
        raise TypeError("controlled locomotion context must contain GeneticArchitecture.")
    genome = build_controlled_locomotion_founder_genome(
        architecture,
        max_speed=treatment.entrant_speed,
    )
    entrant = Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
        age=E6_ENTRANT_AGE,
        energy=E6_ENTRANT_ENERGY,
        body_mass=E6_ENTRANT_BODY_MASS,
        mating_type=E6_ENTRANT_MATING_TYPE,
        x=E6_ENTRANT_X,
        y=E6_ENTRANT_Y,
    )
    world.add_organism(entrant)
    return E6InterventionRecord(
        mechanism="experiment_external_newborn_like_admission",
        step_index=state.step_index,
        organism_id=entrant.id,
        resident_population_size_before=resident_population_size_before,
        initial_rare_frequency=1.0 / (resident_population_size_before + 1),
        role=treatment.role,
        resident_speed=treatment.resident_speed,
        entrant_speed=treatment.entrant_speed,
        age=entrant.age,
        energy=entrant.energy,
        body_mass=entrant.body_mass,
        mating_type=entrant.mating_type,
        x=entrant.x,
        y=entrant.y,
    )


def _validated_trait_observations(
    observations: tuple[IndividualGeneticTraitObservation, ...],
) -> tuple[IndividualGeneticTraitObservation, ...]:
    validators.validate_tuple(observations, name="observations")
    expected_steps = tuple(range(E6_BURN_IN_STEPS, E6_HORIZON + 1))
    actual_steps = tuple(observation.step_index for observation in observations)
    if actual_steps != expected_steps:
        raise ValueError("E6 requires every post-introduction committed state.")
    for observation in observations:
        if observation.trait_names != (MAX_SPEED,):
            raise ValueError("E6 individual evidence must contain only max_speed.")
    return observations


def _resolve_lineages(
    records: tuple[IndividualLifeHistory, ...],
    *,
    rare_baseline_id: int,
) -> dict[int, E6Lineage]:
    record_by_id = {record.organism_id: record for record in records}
    if len(record_by_id) != len(records):
        raise ValueError("pedigree records must contain unique organism IDs.")
    baseline_ids = tuple(record.organism_id for record in records if record.is_founder)
    if rare_baseline_id not in baseline_ids:
        raise ValueError("rare admitted organism must belong to recorder baseline.")
    resolved: dict[int, E6Lineage] = {
        organism_id: "rare" if organism_id == rare_baseline_id else "resident"
        for organism_id in baseline_ids
    }
    visiting: set[int] = set()

    def resolve(organism_id: int) -> E6Lineage:
        if organism_id in resolved:
            return resolved[organism_id]
        if organism_id in visiting:
            raise ValueError("pedigree ancestry contains a cycle.")
        try:
            record = record_by_id[organism_id]
        except KeyError as error:
            raise ValueError(f"organism {organism_id} is absent from pedigree.") from error
        if record.is_founder:
            raise ValueError("baseline organism is missing E6 lineage assignment.")
        if len(record.parent_ids) != 1:
            raise ValueError("E6 clonal descendants must have exactly one parent.")
        visiting.add(organism_id)
        lineage = resolve(record.parent_ids[0])
        visiting.remove(organism_id)
        resolved[organism_id] = lineage
        return lineage

    for organism_id in record_by_id:
        resolve(organism_id)
    return resolved


def _composition_point(
    observation: IndividualGeneticTraitObservation,
    *,
    lineage_by_id: dict[int, E6Lineage],
    treatment: E6TreatmentSpecification,
) -> E6LineageCompositionPoint:
    resident_count = 0
    rare_count = 0
    for individual in observation.individuals:
        try:
            lineage = lineage_by_id[individual.organism_id]
        except KeyError as error:
            raise ValueError("trait observation contains organism absent from pedigree.") from error
        observed_speed = individual.trait_values[0]
        expected_speed = (
            treatment.resident_speed if lineage == "resident" else treatment.entrant_speed
        )
        if observed_speed != expected_speed:
            raise ValueError("committed max_speed disagrees with resolved E6 ancestry.")
        if lineage == "resident":
            resident_count += 1
        else:
            rare_count += 1
    population_size = resident_count + rare_count
    frequencies: tuple[float | None, float | None]
    if population_size == 0:
        frequencies = (None, None)
    else:
        frequencies = (
            resident_count / population_size,
            rare_count / population_size,
        )
    return E6LineageCompositionPoint(
        step_index=observation.step_index,
        population_size=population_size,
        counts=(resident_count, rare_count),
        frequencies=frequencies,
    )


def _rare_birth_count(
    records: tuple[IndividualLifeHistory, ...],
    *,
    lineage_by_id: dict[int, E6Lineage],
) -> int:
    return sum(
        1
        for record in records
        if not record.is_founder and lineage_by_id[record.organism_id] == "rare"
    )


def _time_to_event(
    trajectory: tuple[E6LineageCompositionPoint, ...],
    *,
    predicate: object,
) -> FixedHorizonTimeToEvent:
    if not callable(predicate):
        raise TypeError("predicate must be callable.")
    observed_step: int | None = None
    for point in trajectory:
        if predicate(point):
            observed_step = point.step_index
            break
    return FixedHorizonTimeToEvent(
        start_step_index=E6_BURN_IN_STEPS,
        horizon_step_index=E6_HORIZON,
        observed_step_index=observed_step,
    )


def _fixation_outcome(
    trajectory: tuple[E6LineageCompositionPoint, ...],
) -> tuple[FixedHorizonTimeToEvent, E6FixationWinner | None]:
    for point in trajectory:
        resident_count, rare_count = point.counts
        if point.population_size == 0:
            continue
        if rare_count == 0 and resident_count > 0:
            return (
                FixedHorizonTimeToEvent(
                    start_step_index=E6_BURN_IN_STEPS,
                    horizon_step_index=E6_HORIZON,
                    observed_step_index=point.step_index,
                ),
                "resident",
            )
        if resident_count == 0 and rare_count > 0:
            return (
                FixedHorizonTimeToEvent(
                    start_step_index=E6_BURN_IN_STEPS,
                    horizon_step_index=E6_HORIZON,
                    observed_step_index=point.step_index,
                ),
                "rare",
            )
    return (
        FixedHorizonTimeToEvent(
            start_step_index=E6_BURN_IN_STEPS,
            horizon_step_index=E6_HORIZON,
        ),
        None,
    )


def _scientific_provenance(
    treatment: E6TreatmentSpecification,
    *,
    seed: int,
    run_role: RunRole | None,
) -> ScientificRunProvenance:
    specification = {
        "role": treatment.role,
        "resident_speed": treatment.resident_speed,
        "entrant_speed": treatment.entrant_speed,
        "resident_founder_count": E6_RESIDENT_FOUNDER_COUNT,
        "resource_per_resident_founder": E5_RESOURCE_PER_FOUNDER,
        "burn_in_step": E6_BURN_IN_STEPS,
        "horizon_step": E6_HORIZON,
        "entrant_age": E6_ENTRANT_AGE,
        "entrant_energy": E6_ENTRANT_ENERGY,
        "entrant_body_mass": E6_ENTRANT_BODY_MASS,
        "entrant_mating_type": E6_ENTRANT_MATING_TYPE,
        "entrant_x": E6_ENTRANT_X,
        "entrant_y": E6_ENTRANT_Y,
        "environment": "separated_corridor",
    }
    return ScientificRunProvenance(
        experiment_id="e6-rare-lineage-invasion",
        scenario_id="e6-established-resident-separated-corridor",
        treatment_id=treatment.treatment_id,
        treatment_specification_json=canonical_treatment_specification(specification),
        seed=seed,
        horizon_step_index=E6_HORIZON,
        observation_every_n_steps=1,
        observation_include_step_zero=False,
        focal_variables=(
            "rare_lineage_frequency",
            "rare_lineage_count",
            MAX_SPEED,
            "pedigree",
        ),
        run_role=run_role,
    )


def _world_state_sha256(world: WorldState, *, state: SimulationState) -> str:
    architecture = state.context.require(GENETIC_ARCHITECTURE)
    if not isinstance(architecture, GeneticArchitecture):
        raise TypeError("controlled locomotion context must contain GeneticArchitecture.")
    payload = {
        "step_index": state.step_index,
        "organisms": [
            {
                "id": organism_id,
                "age": organism.age,
                "energy": organism.energy,
                "body_mass": organism.body_mass,
                "x": organism.x,
                "y": organism.y,
                "max_speed": organism.genetic_phenotype.int_value(MAX_SPEED),
            }
            for organism_id, organism in sorted(world.organisms.items())
        ],
        "resources": [
            [x, y, amount]
            for (x, y), amount in sorted(world.resources.items())
        ],
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _sha256(encoded)


def _validate_world_resident_speed(
    world: WorldState,
    *,
    state: SimulationState,
    resident_speed: int,
) -> None:
    del state
    for organism in world.organisms.values():
        if organism.genetic_phenotype.int_value(MAX_SPEED) != resident_speed:
            raise ValueError("resident burn-in must remain monomorphic for max_speed.")


def _validate_matched_interventions(
    neutral: E6InterventionRecord,
    mutant: E6InterventionRecord,
) -> None:
    if neutral.role != "neutral" or mutant.role != "mutant":
        raise ValueError("matched interventions require neutral and mutant roles.")
    if neutral.organism_id != mutant.organism_id:
        raise ValueError("copied allocator state must produce the same entrant ID.")
    normalized = attrs.evolve(
        mutant,
        role="neutral",
        entrant_speed=neutral.entrant_speed,
    )
    if normalized != neutral:
        raise ValueError("matched interventions differ outside entrant max_speed/role.")


def _validate_outcome_event_consistency(outcome: E6ReplicateOutcome) -> None:
    if not outcome.rare_loss.right_censored:
        step = outcome.rare_loss.observed_step_index
        point = _point_at_step(outcome.trajectory, step)
        if point.count("rare") != 0 or point.count("resident") == 0:
            raise ValueError("rare loss must leave a nonempty resident lineage.")
    if not outcome.rare_expansion.right_censored:
        step = outcome.rare_expansion.observed_step_index
        if _point_at_step(outcome.trajectory, step).count("rare") < 2:
            raise ValueError("rare expansion must first observe at least two rare organisms.")
    if not outcome.extinction.right_censored:
        step = outcome.extinction.observed_step_index
        if _point_at_step(outcome.trajectory, step).population_size != 0:
            raise ValueError("extinction must observe an empty population.")


def _point_at_step(
    trajectory: tuple[E6LineageCompositionPoint, ...],
    step_index: int | None,
) -> E6LineageCompositionPoint:
    if step_index is None:
        raise ValueError("observed event must have a step index.")
    for point in trajectory:
        if point.step_index == step_index:
            return point
    raise ValueError("event step is absent from E6 trajectory.")


def _validate_frequencies(
    *,
    population_size: int,
    frequencies: tuple[float | None, float | None],
) -> None:
    if population_size == 0:
        if frequencies != (None, None):
            raise ValueError("extinct lineage frequencies must be undefined.")
        return
    if frequencies[0] is None or frequencies[1] is None:
        raise ValueError("nonempty lineage frequencies must be defined.")
    defined = (frequencies[0], frequencies[1])
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in defined):
        raise ValueError("defined lineage frequencies must be finite in [0, 1].")
    if not math.isclose(sum(defined), 1.0):
        raise ValueError("defined lineage frequencies must sum to one.")


def _lineage_index(lineage: E6Lineage) -> int:
    if lineage == "resident":
        return 0
    if lineage == "rare":
        return 1
    raise ValueError("lineage must be 'resident' or 'rare'.")


def _world_state(state: SimulationState) -> WorldState:
    if not isinstance(state, SimulationState):
        raise TypeError("state must be a SimulationState.")
    world = state.domain_state
    if not isinstance(world, WorldState):
        raise TypeError("E6 controlled composition requires a WorldState.")
    return world


def _validate_arm_outcomes(
    values: tuple[E6ReplicateOutcome, ...],
) -> E6TreatmentSpecification:
    if not values:
        raise ValueError("outcomes must contain at least one replicate.")
    treatment = values[0].treatment
    seeds: list[int] = []
    for value in values:
        if not isinstance(value, E6ReplicateOutcome):
            raise TypeError("outcomes must contain E6ReplicateOutcome values.")
        if value.treatment != treatment:
            raise ValueError("arm summary cannot mix E6 treatments.")
        seeds.append(value.provenance.seed)
    if len(seeds) != len(set(seeds)):
        raise ValueError("arm summary cannot pseudoreplicate duplicate seeds.")
    return treatment


def _validated_unique_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    values = tuple(seeds)
    if not values:
        raise ValueError("seeds must contain at least one replicate seed.")
    for index, seed in enumerate(values):
        validators.validate_int(seed, name=f"seeds[{index}]")
    if len(values) != len(set(values)):
        raise ValueError("seeds must be unique; one run/seed is one replicate.")
    return values


def _require_treatment(value: object) -> E6TreatmentSpecification:
    if not isinstance(value, E6TreatmentSpecification):
        raise TypeError("value must be an E6TreatmentSpecification.")
    return value


def _paired_difference(neutral: float | None, mutant: float | None) -> float | None:
    if neutral is None or mutant is None:
        return None
    return mutant - neutral


def _mean_or_none(values: tuple[float, ...]) -> float | None:
    return None if not values else statistics.fmean(values)


def _median_or_none(values: tuple[float, ...]) -> float | None:
    return None if not values else statistics.median(values)


def _direction_proportion(
    values: tuple[float, ...],
    *,
    direction: Literal["increase", "decrease", "unchanged"],
) -> float | None:
    if not values:
        return None
    predicates = {
        "increase": lambda value: value > 0.0,
        "decrease": lambda value: value < 0.0,
        "unchanged": lambda value: value == 0.0,
    }
    return sum(1 for value in values if predicates[direction](value)) / len(values)


def _proportion(values: Sequence[object], predicate: object) -> float:
    if not values:
        raise ValueError("values must contain at least one replicate.")
    if not callable(predicate):
        raise TypeError("predicate must be callable.")
    return sum(1 for value in values if predicate(value)) / len(values)


def _validate_sha256(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if len(validated) != 64 or any(
        character not in "0123456789abcdef" for character in validated
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 hexadecimal digest.")
    return validated


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
