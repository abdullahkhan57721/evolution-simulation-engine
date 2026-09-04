"""Run and summarize the frozen B3 environment-dependent selection scenario."""

from __future__ import annotations

import math

import attrs

from evo_engine.engine import Simulation
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
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_PATCH_CENTERS,
    B3_PRIMARY_STEP,
    B3FlagshipSpecification,
    build_b3_flagship_specification,
    build_b3_flagship_world,
    validate_b3_treatment_integrity,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.telemetry import AppliedEvent


@attrs.frozen(slots=True, kw_only=True)
class B3GeneticPoint:
    """Record focal genetic composition at one committed timestep."""

    step_index: int
    population_size: int
    high_speed_allele_frequency: float | None
    genotype_frequencies: tuple[tuple[tuple[int, ...], float], ...]


@attrs.frozen(slots=True, kw_only=True)
class B3PopulationPoint:
    """Record small B3 demographic/ecological diagnostics at one timestep."""

    step_index: int
    population_size: int
    total_resources: int
    mean_energy: float | None
    mean_max_speed_capacity: float | None


@attrs.frozen(slots=True, kw_only=True)
class B3FounderReproductiveSuccess:
    """Summarize realized direct reproductive contribution of B3 founders."""

    low_speed_count: int
    low_speed_mean: float
    high_speed_count: int
    high_speed_mean: float


@attrs.frozen(slots=True, kw_only=True)
class B3ResourceGeography:
    """Summarize committed resource-cell occupancy relative to compact support."""

    resource_cell_observations: int
    compact_support_cell_observations: int
    compact_support_fraction: float | None
    unique_resource_cells: int


@attrs.frozen(slots=True, kw_only=True)
class B3MovementConsumptionEpisode:
    """Record one authoritative targeted-movement/resource-consumption episode."""

    completed_step_index: int
    organism_id: int
    max_speed_capacity: int
    start: tuple[int, int]
    end: tuple[int, int]
    target: tuple[int, int]
    realized_displacement: float
    movement_energy_cost: int
    resource_consumed_same_step: int
    energy_before_step: int | None
    energy_after_step: int | None


@attrs.frozen(slots=True, kw_only=True)
class B3RunEvidence:
    """Retain immutable committed evidence for one completed B3 simulation."""

    specification: B3FlagshipSpecification
    population_observations: tuple[PopulationObservation, ...]
    genetic_observations: tuple[GeneticCompositionObservation, ...]
    spatial_observations: tuple[SpatialObservation, ...]
    individual_trait_observations: tuple[IndividualGeneticTraitObservation, ...]
    events: tuple[AppliedEvent, ...]
    pedigree_records: tuple[IndividualLifeHistory, ...]


@attrs.frozen(slots=True, kw_only=True)
class B3RunSummary:
    """Store the focused scientific summary needed for B3 confirmation."""

    seed: int
    environment: str
    founder_assignment: str
    extinction_step: int | None
    genetic_trajectory: tuple[B3GeneticPoint, ...]
    population_trajectory: tuple[B3PopulationPoint, ...]
    founder_reproductive_success: B3FounderReproductiveSuccess
    resource_geography: B3ResourceGeography
    mechanism_episodes: tuple[B3MovementConsumptionEpisode, ...]

    def high_speed_frequency_at(self, step_index: int) -> float | None:
        """Return the focal high-speed allele frequency at a committed timestep."""
        for point in self.genetic_trajectory:
            if point.step_index == step_index:
                return point.high_speed_allele_frequency
        raise KeyError(f"No B3 genetic observation for step {step_index}.")

    @property
    def primary_high_speed_frequency(self) -> float | None:
        """Return the predeclared step-30 high-speed allele frequency."""
        return self.high_speed_frequency_at(B3_PRIMARY_STEP)


@attrs.frozen(slots=True, kw_only=True)
class B3MatchedPairSummary:
    """Store one seed-blocked uniform/compact B3 comparison."""

    seed: int
    founder_assignment: str
    control: B3RunSummary
    treatment: B3RunSummary

    @property
    def primary_effect(self) -> float | None:
        """Return compact minus uniform high-speed allele frequency at step 30."""
        control_frequency = self.control.primary_high_speed_frequency
        treatment_frequency = self.treatment.primary_high_speed_frequency
        if control_frequency is None or treatment_frequency is None:
            return None
        return treatment_frequency - control_frequency


def run_b3_flagship(
    specification: B3FlagshipSpecification,
) -> B3RunEvidence:
    """Execute one B3 run using ordinary reference ecology and committed recorders.

    Args:
        specification: Frozen B3 run specification.

    Returns:
        Immutable committed evidence from the completed run.
    """
    spatial_recorder = SpatialRecorder(every_n_steps=1, include_step_zero=True)
    trait_recorder = IndividualGeneticTraitRecorder(
        trait_names=(MAX_SPEED,),
        every_n_steps=1,
        include_step_zero=True,
    )
    ecology = build_reference_ecology(
        specification.config,
        additional_observers=(spatial_recorder, trait_recorder),
    )
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    founder_world = build_b3_flagship_world(architecture, specification)
    simulation = Simulation(
        initial_domain_state=founder_world,
        seed=specification.seed,
        context=ecology.simulation.context,
    )
    ecology.engine.run(simulation)

    return B3RunEvidence(
        specification=specification,
        population_observations=ecology.recorder.observations,
        genetic_observations=ecology.genetic_recorder.observations,
        spatial_observations=spatial_recorder.observations,
        individual_trait_observations=trait_recorder.observations,
        events=ecology.event_recorder.events,
        pedigree_records=ecology.pedigree_recorder.records,
    )


def summarize_b3_run(evidence: B3RunEvidence) -> B3RunSummary:
    """Derive the focused B3 scientific summary from committed run evidence."""
    founder_speed = _founder_speed_by_id(evidence.individual_trait_observations)
    extinction_step = next(
        (
            observation.step_index
            for observation in evidence.population_observations
            if observation.population_size == 0
        ),
        None,
    )
    return B3RunSummary(
        seed=evidence.specification.seed,
        environment=evidence.specification.environment,
        founder_assignment=evidence.specification.founder_assignment,
        extinction_step=extinction_step,
        genetic_trajectory=tuple(
            _genetic_point(observation) for observation in evidence.genetic_observations
        ),
        population_trajectory=tuple(
            _population_point(observation)
            for observation in evidence.population_observations
        ),
        founder_reproductive_success=_founder_reproductive_success(
            evidence.pedigree_records,
            founder_speed=founder_speed,
        ),
        resource_geography=_resource_geography(evidence.spatial_observations),
        mechanism_episodes=_mechanism_episodes(evidence),
    )


def run_b3_matched_pair(
    *,
    seed: int,
    founder_assignment: str = "standard",
) -> B3MatchedPairSummary:
    """Run one predeclared same-seed uniform/compact B3 matched comparison."""
    control = build_b3_flagship_specification(
        seed=seed,
        environment="uniform",
        founder_assignment=founder_assignment,  # type: ignore[arg-type]
    )
    treatment = build_b3_flagship_specification(
        seed=seed,
        environment="compact_patch",
        founder_assignment=founder_assignment,  # type: ignore[arg-type]
    )
    validate_b3_treatment_integrity(control, treatment)
    return B3MatchedPairSummary(
        seed=seed,
        founder_assignment=founder_assignment,
        control=summarize_b3_run(run_b3_flagship(control)),
        treatment=summarize_b3_run(run_b3_flagship(treatment)),
    )


def _genetic_point(observation: GeneticCompositionObservation) -> B3GeneticPoint:
    locus = observation.locus(MAX_SPEED)
    high_frequency = (
        None
        if observation.population_size == 0
        else locus.allele_frequency(B3_HIGH_MAX_SPEED)
    )
    genotype_frequencies: list[tuple[tuple[int, ...], float]] = []
    for genotype in locus.genotypes:
        values = tuple(int(value) for value in genotype.allele_values)
        genotype_frequencies.append((values, genotype.frequency))
    return B3GeneticPoint(
        step_index=observation.step_index,
        population_size=observation.population_size,
        high_speed_allele_frequency=high_frequency,
        genotype_frequencies=tuple(genotype_frequencies),
    )


def _population_point(observation: PopulationObservation) -> B3PopulationPoint:
    mean_max_speed = None
    for trait in observation.traits:
        if trait.trait_name == MAX_SPEED:
            mean_max_speed = trait.summary.mean
            break
    return B3PopulationPoint(
        step_index=observation.step_index,
        population_size=observation.population_size,
        total_resources=observation.total_resources,
        mean_energy=observation.energy.mean,
        mean_max_speed_capacity=mean_max_speed,
    )


def _founder_speed_by_id(
    observations: tuple[IndividualGeneticTraitObservation, ...],
) -> dict[int, int]:
    step_zero = next(
        observation for observation in observations if observation.step_index == 0
    )
    return {
        individual.organism_id: step_zero.trait_value(individual.organism_id, MAX_SPEED)
        for individual in step_zero.individuals
    }


def _founder_reproductive_success(
    records: tuple[IndividualLifeHistory, ...],
    *,
    founder_speed: dict[int, int],
) -> B3FounderReproductiveSuccess:
    low: list[int] = []
    high: list[int] = []
    for record in records:
        if not record.is_founder:
            continue
        speed = founder_speed[record.organism_id]
        if speed == B3_LOW_MAX_SPEED:
            low.append(record.realized_reproductive_success)
        elif speed == B3_HIGH_MAX_SPEED:
            high.append(record.realized_reproductive_success)
    if not low or not high:
        raise ValueError("B3 founder reproductive-success groups must be nonempty.")
    return B3FounderReproductiveSuccess(
        low_speed_count=len(low),
        low_speed_mean=sum(low) / len(low),
        high_speed_count=len(high),
        high_speed_mean=sum(high) / len(high),
    )


def _resource_geography(
    observations: tuple[SpatialObservation, ...],
) -> B3ResourceGeography:
    compact_support = {
        (x, y)
        for center_x, center_y in B3_PATCH_CENTERS
        for y in range(center_y - 1, center_y + 2)
        for x in range(center_x - 1, center_x + 2)
        if (x - center_x) ** 2 + (y - center_y) ** 2 <= 1
    }
    all_coordinates: list[tuple[int, int]] = []
    compact_count = 0
    for observation in observations:
        if observation.step_index == 0:
            continue
        for resource in observation.resources:
            coordinate = (resource.x, resource.y)
            all_coordinates.append(coordinate)
            if coordinate in compact_support:
                compact_count += 1
    total = len(all_coordinates)
    return B3ResourceGeography(
        resource_cell_observations=total,
        compact_support_cell_observations=compact_count,
        compact_support_fraction=(compact_count / total if total else None),
        unique_resource_cells=len(set(all_coordinates)),
    )


def _mechanism_episodes(evidence: B3RunEvidence) -> tuple[B3MovementConsumptionEpisode, ...]:
    speed_by_id: dict[int, int] = {}
    for observation in evidence.individual_trait_observations:
        for individual in observation.individuals:
            speed_by_id[individual.organism_id] = observation.trait_value(
                individual.organism_id,
                MAX_SPEED,
            )

    spatial_by_step = {
        observation.step_index: observation for observation in evidence.spatial_observations
    }
    consumption: dict[tuple[int, int], int] = {}
    for applied in evidence.events:
        if applied.process_name != "ResourceConsumption":
            continue
        event = applied.event
        organism_id = getattr(event, "organism_id", None)
        amount = getattr(event, "amount", None)
        if type(organism_id) is int and type(amount) is int and amount > 0:
            key = (applied.event_step_index + 1, organism_id)
            consumption[key] = consumption.get(key, 0) + amount

    episodes: list[B3MovementConsumptionEpisode] = []
    for applied in evidence.events:
        if applied.process_name != "Movement":
            continue
        event = applied.event
        organism_id = getattr(event, "organism_id", None)
        target_x = getattr(event, "target_x", None)
        target_y = getattr(event, "target_y", None)
        if type(organism_id) is not int or target_x is None or target_y is None:
            continue
        completed_step = applied.event_step_index + 1
        consumed = consumption.get((completed_step, organism_id), 0)
        if consumed <= 0:
            continue
        dx = getattr(event, "dx")
        dy = getattr(event, "dy")
        new_x = getattr(event, "new_x")
        new_y = getattr(event, "new_y")
        before = _spatial_energy(
            spatial_by_step.get(completed_step - 1),
            organism_id,
        )
        after = _spatial_energy(
            spatial_by_step.get(completed_step),
            organism_id,
        )
        episodes.append(
            B3MovementConsumptionEpisode(
                completed_step_index=completed_step,
                organism_id=organism_id,
                max_speed_capacity=speed_by_id[organism_id],
                start=(new_x - dx, new_y - dy),
                end=(new_x, new_y),
                target=(target_x, target_y),
                realized_displacement=math.hypot(dx, dy),
                movement_energy_cost=getattr(event, "energy_cost"),
                resource_consumed_same_step=consumed,
                energy_before_step=before,
                energy_after_step=after,
            )
        )
    return tuple(episodes)


def _spatial_energy(
    observation: SpatialObservation | None,
    organism_id: int,
) -> int | None:
    if observation is None:
        return None
    for organism in observation.organisms:
        if organism.organism_id == organism_id:
            return organism.energy
    return None


__all__ = [
    "B3FounderReproductiveSuccess",
    "B3GeneticPoint",
    "B3MatchedPairSummary",
    "B3MovementConsumptionEpisode",
    "B3PopulationPoint",
    "B3ResourceGeography",
    "B3RunEvidence",
    "B3RunSummary",
    "run_b3_flagship",
    "run_b3_matched_pair",
    "summarize_b3_run",
]
