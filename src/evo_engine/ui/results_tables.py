"""Presentation-only row shaping for WU4 Results tables and charts.

Every value in this module is copied or relabeled from an authoritative evidence,
measurement, replicate-outcome, or treatment-summary contract.  These helpers do
not estimate statistics, expand experiments, infer missing evidence, or become a
scientific dataframe source of truth.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunSummary,
)
from evo_engine.experiments.e3_performance import E3ReplicateOutcome, E3TreatmentSummary
from evo_engine.experiments.e4_selection import (
    E4_FOCAL_SPEEDS,
    E4EnvironmentSummary,
    E4ReplicateOutcome,
)
from evo_engine.experiments.locomotion import LocomotionReplicateMeasurements
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent
from evo_engine.workbench.results import (
    EnvironmentSelectionReplicateView,
    MaxSpeedSweepReplicateView,
)
from evo_engine.workbench.study import WorkbenchRunProvenance

TableRow = dict[str, Any]


def population_rows(observations: Sequence[PopulationObservation]) -> list[TableRow]:
    """Copy committed population observations into readable table rows."""
    return [
        {
            "Step": item.step_index,
            "Population size": item.population_size,
            "Carcasses": item.carcass_count,
            "Total resources": item.total_resources,
            "Mean age": item.age.mean,
            "Mean energy": item.energy.mean,
            "Mean body mass": item.body_mass.mean,
        }
        for item in observations
    ]


def locomotion_rows(value: LocomotionReplicateMeasurements) -> list[TableRow]:
    """Copy the existing E1 locomotion replicate measurement."""
    return [
        {
            "Applied movements": value.applied_movement_count,
            "Total attempted distance": value.total_attempted_distance,
            "Total realized distance": value.total_realized_distance,
            "Mean realized distance / applied movement": (
                value.mean_realized_distance_per_applied_movement
            ),
            "Total locomotion energy": value.total_locomotion_energy_expenditure,
            "Mean locomotion energy / applied movement": (
                value.mean_locomotion_energy_expenditure_per_applied_movement
            ),
        }
    ]


def event_rows(events: Sequence[AppliedEvent]) -> list[TableRow]:
    """Expose committed event identity without reconstructing simulation intent."""
    return [
        {
            "Event step": item.event_step_index,
            "Committed step": item.completed_step_index,
            "Stage": item.stage_index,
            "Process": item.process_name,
            "Event": item.event_name,
            "Effects recorded": len(item.effects),
        }
        for item in events
    ]


def pedigree_rows(records: Sequence[IndividualLifeHistory]) -> list[TableRow]:
    """Expose existing observed life-history records without genealogy inference."""
    return [
        {
            "Organism": item.organism_id,
            "Founder": item.is_founder,
            "Parents": _id_list(item.parent_ids),
            "Entry step": item.entry_step,
            "Birth step": item.birth_step,
            "Death step": item.death_step,
            "Death cause": item.death_cause,
            "Offspring": _id_list(item.offspring_ids),
            "Observed offspring count": item.realized_reproductive_success,
            "Lifetime offspring count": item.lifetime_reproductive_success,
        }
        for item in records
    ]


def genetic_allele_rows(
    observations: Sequence[GeneticCompositionObservation],
) -> list[TableRow]:
    """Flatten recorded allele frequencies for inspection only."""
    rows: list[TableRow] = []
    for observation in observations:
        for locus in observation.loci:
            for allele in locus.alleles:
                rows.append(
                    {
                        "Step": observation.step_index,
                        "Population size": observation.population_size,
                        "Locus": locus.locus_name,
                        "Allele": str(allele.value),
                        "Allele copies": allele.count,
                        "Frequency": allele.frequency,
                    }
                )
    return rows


def genetic_genotype_rows(
    observations: Sequence[GeneticCompositionObservation],
) -> list[TableRow]:
    """Flatten recorded unphased genotype frequencies for inspection only."""
    rows: list[TableRow] = []
    for observation in observations:
        for locus in observation.loci:
            for genotype in locus.genotypes:
                rows.append(
                    {
                        "Step": observation.step_index,
                        "Population size": observation.population_size,
                        "Locus": locus.locus_name,
                        "Genotype": "/".join(
                            str(value) for value in genotype.allele_values
                        ),
                        "Organisms": genotype.count,
                        "Frequency": genotype.frequency,
                    }
                )
    return rows


def spatial_frame_rows(observations: Sequence[SpatialObservation]) -> list[TableRow]:
    """Describe the recorded spatial frames without synthesizing world replay."""
    return [
        {
            "Step": item.step_index,
            "World width": item.world_width,
            "World height": item.world_height,
            "Organism snapshots": len(item.organisms),
            "Resource sites": len(item.resources),
            "Carcass snapshots": len(item.carcasses),
        }
        for item in observations
    ]


def spatial_organism_rows(observation: SpatialObservation) -> list[TableRow]:
    return [
        {
            "Organism": item.organism_id,
            "x": item.x,
            "y": item.y,
            "Age": item.age,
            "Energy": item.energy,
            "Body mass": item.body_mass,
            "Mating type": item.mating_type,
        }
        for item in observation.organisms
    ]


def spatial_resource_rows(observation: SpatialObservation) -> list[TableRow]:
    return [
        {"x": item.x, "y": item.y, "Amount": item.amount}
        for item in observation.resources
    ]


def spatial_carcass_rows(observation: SpatialObservation) -> list[TableRow]:
    return [
        {
            "Carcass": item.carcass_id,
            "x": item.x,
            "y": item.y,
            "Resource units": item.resource_units,
        }
        for item in observation.carcasses
    ]


def e3_summary_rows(summaries: Sequence[E3TreatmentSummary]) -> list[TableRow]:
    """Copy existing E3 treatment summaries without recalculation."""
    return [
        {
            "Maximum speed": item.treatment.max_speed,
            "Environment": _humanize(item.treatment.environment),
            "Replicates": item.replicate_count,
            "Seeds": ", ".join(str(seed) for seed in item.seeds),
            "Mean cumulative births": item.mean_cumulative_birth_count,
            "Mean final population": item.mean_final_population_size,
            "Mean resource consumed": item.mean_total_resource_consumed,
            "Mean realized distance": item.mean_total_realized_distance,
            "Mean locomotion energy": item.mean_total_locomotion_energy_expenditure,
            "Extinctions": item.extinction_count,
        }
        for item in summaries
    ]


def e3_replicate_identity_rows(value: MaxSpeedSweepReplicateView) -> list[TableRow]:
    return [
        {
            "Factor": "Maximum speed",
            "Factor level": value.factor_level,
            "Seed / replicate": value.seed,
            "Treatment ID": value.treatment_id,
            "Manifest digest": value.manifest_digest,
        }
    ]


def e3_outcome_rows(value: E3ReplicateOutcome) -> list[TableRow]:
    return [
        {
            "Final population": value.final_population_size,
            "Final population energy": value.final_total_population_energy,
            "Cumulative births": value.cumulative_birth_count,
            "Resource consumed": value.total_resource_consumed,
            "Boundary clipping events": value.boundary_clipping_event_count,
            "Extinction step": value.extinction.observed_step_index,
            "Extinction right-censored": value.extinction.right_censored,
        }
    ]


def e3_energy_rows(value: E3ReplicateOutcome) -> list[TableRow]:
    return [
        {
            "Step": item.step_index,
            "Population size": item.population_size,
            "Total population energy": item.total_population_energy,
        }
        for item in value.energy_trajectory
    ]


def e4_summary_rows(summaries: Sequence[E4EnvironmentSummary]) -> list[TableRow]:
    """Copy existing E4 environment summaries, one row per focal speed."""
    rows: list[TableRow] = []
    for summary in summaries:
        for index, speed in enumerate(E4_FOCAL_SPEEDS):
            rows.append(
                {
                    "Environment": _humanize(summary.environment),
                    "Maximum speed strategy": speed,
                    "Replicates": summary.replicate_count,
                    "Defined endpoints": summary.defined_endpoint_count,
                    "Extinctions": summary.extinction_count,
                    "Mean final frequency": summary.mean_final_frequencies[index],
                    "Mean frequency change": summary.mean_frequency_changes[index],
                    "Mean births": summary.mean_births_by_speed[index],
                    "Mean resources consumed": summary.mean_resources_by_speed[index],
                    "Mean realized distance": summary.mean_realized_distance_by_speed[
                        index
                    ],
                    "Mean locomotion energy": summary.mean_locomotion_energy_by_speed[
                        index
                    ],
                }
            )
    return rows


def e4_summary_chart_rows(summaries: Sequence[E4EnvironmentSummary]) -> list[TableRow]:
    """Reshape existing frequency-change values into one row per environment."""
    return [
        {
            "Environment": _humanize(summary.environment),
            **{
                f"Speed {speed} frequency change": summary.mean_frequency_changes[index]
                for index, speed in enumerate(E4_FOCAL_SPEEDS)
            },
        }
        for summary in summaries
    ]


def e4_replicate_identity_rows(
    value: EnvironmentSelectionReplicateView,
) -> list[TableRow]:
    return [
        {
            "Role": value.role.title(),
            "Factor": "Resource geography",
            "Factor level": _humanize(value.factor_level),
            "Seed / replicate": value.seed,
            "Treatment ID": value.treatment_id,
            "Standing focal composition": _id_list(value.standing_focal_composition),
            "Founder-speed order (counterbalance)": _id_list(value.founder_speed_order),
        }
    ]


def e4_trajectory_rows(value: E4ReplicateOutcome) -> list[TableRow]:
    rows: list[TableRow] = []
    for point in value.focal_trajectory:
        row: TableRow = {
            "Step": point.step_index,
            "Population size": point.population_size,
        }
        for index, speed in enumerate(E4_FOCAL_SPEEDS):
            row[f"Speed {speed} count"] = point.counts[index]
            row[f"Speed {speed} frequency"] = point.frequencies[index]
        rows.append(row)
    return rows


def e4_mechanism_rows(value: E4ReplicateOutcome) -> list[TableRow]:
    return [
        {
            "Maximum speed strategy": item.max_speed,
            "Applied movements": item.applied_movement_count,
            "Realized distance": item.total_realized_distance,
            "Locomotion energy": item.total_locomotion_energy_expenditure,
            "Resources consumed": item.total_resource_consumed,
            "Cumulative births": item.cumulative_birth_count,
        }
        for item in value.mechanisms
    ]


def b3_matched_summary_rows(values: Sequence[B3MatchedPairSummary]) -> list[TableRow]:
    """Keep B3 same-seed matched comparisons as one row per pair."""
    return [
        {
            "Seed / matched block": item.seed,
            "Founder assignment": _humanize(item.founder_assignment),
            "Uniform primary high-speed frequency": item.control.primary_high_speed_frequency,
            "Compact primary high-speed frequency": item.treatment.primary_high_speed_frequency,
            "Compact − uniform primary effect": item.primary_effect,
            "Uniform extinction step": item.control.extinction_step,
            "Compact extinction step": item.treatment.extinction_step,
        }
        for item in values
    ]


def b3_single_summary_rows(values: Sequence[B3RunSummary]) -> list[TableRow]:
    return [
        {
            "Seed": item.seed,
            "Environment": _humanize(item.environment),
            "Founder assignment": _humanize(item.founder_assignment),
            "Primary high-speed frequency": item.primary_high_speed_frequency,
            "Extinction step": item.extinction_step,
        }
        for item in values
    ]


def b3_population_rows(value: B3RunSummary) -> list[TableRow]:
    return [
        {
            "Step": item.step_index,
            "Population size": item.population_size,
            "Total resources": item.total_resources,
            "Mean energy": item.mean_energy,
            "Mean maximum-speed capacity": item.mean_max_speed_capacity,
        }
        for item in value.population_trajectory
    ]


def b3_genetic_rows(value: B3RunSummary) -> list[TableRow]:
    return [
        {
            "Step": item.step_index,
            "Population size": item.population_size,
            "High-speed allele frequency": item.high_speed_allele_frequency,
        }
        for item in value.genetic_trajectory
    ]


def workbench_provenance_rows(value: WorkbenchRunProvenance) -> list[TableRow]:
    return [
        {
            "Run ID": value.run_id,
            "Study revision": value.study_revision_id,
            "Manifest digest": value.manifest_digest,
            "Evidence IDs": ", ".join(value.evidence_ids),
            "Evidence references": ", ".join(value.evidence_references),
            "Result references": ", ".join(value.result_references),
        }
    ]


def historical_run_rows(values: Sequence[WorkbenchRunProvenance]) -> list[TableRow]:
    return [workbench_provenance_rows(value)[0] for value in values]


def scientific_provenance_rows(value: Any) -> list[TableRow]:
    """Copy fields from the existing ScientificRunProvenance value."""
    return [
        {
            "Experiment ID": value.experiment_id,
            "Scenario ID": value.scenario_id,
            "Treatment ID": value.treatment_id,
            "Seed / replicate": value.seed,
            "Run role": value.run_role,
            "Horizon step": value.horizon_step_index,
            "Observation cadence": value.observation_every_n_steps,
            "Includes step zero": value.observation_include_step_zero,
            "Focal variables": ", ".join(value.focal_variables),
            "Treatment specification": value.treatment_specification_json,
        }
    ]


def _id_list(values: Sequence[object]) -> str:
    return ", ".join(str(value) for value in values) or "—"


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = [
    "b3_genetic_rows",
    "b3_matched_summary_rows",
    "b3_population_rows",
    "b3_single_summary_rows",
    "e3_energy_rows",
    "e3_outcome_rows",
    "e3_replicate_identity_rows",
    "e3_summary_rows",
    "e4_mechanism_rows",
    "e4_replicate_identity_rows",
    "e4_summary_chart_rows",
    "e4_summary_rows",
    "e4_trajectory_rows",
    "event_rows",
    "genetic_allele_rows",
    "genetic_genotype_rows",
    "historical_run_rows",
    "locomotion_rows",
    "pedigree_rows",
    "population_rows",
    "scientific_provenance_rows",
    "spatial_carcass_rows",
    "spatial_frame_rows",
    "spatial_organism_rows",
    "spatial_resource_rows",
    "workbench_provenance_rows",
]
