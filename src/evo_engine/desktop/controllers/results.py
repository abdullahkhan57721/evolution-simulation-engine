"""Family-aware native Results presentation over existing WB5 result inspectors."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal

from evo_engine.desktop.artifacts import (
    ConcreteWorkbenchArtifact,
    artifact_kind,
    artifact_run_count,
    result_matches_artifact,
)
from evo_engine.desktop.models.authoring import MeaningItem, MeaningListModel
from evo_engine.experiments.e4_selection import E4_FOCAL_SPEEDS
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
    ReferenceRunResult,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchRunResult,
)
from evo_engine.workbench.results import (
    AnalysisAvailability,
    inspect_b3_results,
    inspect_controlled_locomotion_results,
    inspect_environment_selection_results,
    inspect_max_speed_sweep_results,
    inspect_reference_study_results,
)


class ResultsController(QObject):
    """Expose renderer-specific cards without creating a scientific result hierarchy."""

    changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._result: object | None = None
        self._overview = MeaningListModel()
        self._explore = MeaningListModel()
        self._analysis = MeaningListModel()
        self._provenance = MeaningListModel()
        self._overview_title = "Overview"
        self._explore_title = "Explore"
        self._analysis_title = "Analysis"
        self._historical_message = ""

    @Property(QObject, constant=True)
    def overviewModel(self) -> QObject:  # noqa: N802
        return self._overview

    @Property(QObject, constant=True)
    def exploreModel(self) -> QObject:  # noqa: N802
        return self._explore

    @Property(QObject, constant=True)
    def analysisModel(self) -> QObject:  # noqa: N802
        return self._analysis

    @Property(QObject, constant=True)
    def provenanceModel(self) -> QObject:  # noqa: N802
        return self._provenance

    @Property(bool, notify=changed)
    def hasResult(self) -> bool:  # noqa: N802
        return self._result is not None

    @Property(str, notify=changed)
    def mode(self) -> str:
        return "" if self._artifact is None else artifact_kind(self._artifact)

    @Property(str, notify=changed)
    def overviewTitle(self) -> str:  # noqa: N802
        return self._overview_title

    @Property(str, notify=changed)
    def exploreTitle(self) -> str:  # noqa: N802
        return self._explore_title

    @Property(str, notify=changed)
    def analysisTitle(self) -> str:  # noqa: N802
        return self._analysis_title

    @Property(str, notify=changed)
    def historicalMessage(self) -> str:  # noqa: N802
        return self._historical_message

    def activate_artifact(self, artifact: ConcreteWorkbenchArtifact) -> None:
        self._artifact = artifact
        self._result = None
        self._clear_models()
        count = artifact_run_count(artifact)
        self._historical_message = (
            ""
            if not count
            else (
                f"This saved revision records {count} historical run reference(s), but "
                "persisted provenance is not a result archive. Opened Studies do not "
                "reconstruct observations or rerun implicitly."
            )
        )
        self.changed.emit()

    def clear(self) -> None:
        self._artifact = None
        self._result = None
        self._historical_message = ""
        self._clear_models()
        self.changed.emit()

    def bind_result(
        self,
        artifact: ConcreteWorkbenchArtifact,
        result: object,
    ) -> bool:
        if not result_matches_artifact(artifact, result):
            return False
        self._artifact = artifact
        self._result = result
        self._historical_message = ""
        if isinstance(artifact, StudyRevision) and isinstance(
            result, WorkbenchRunResult
        ):
            self._bind_controlled(artifact, result)
        elif isinstance(artifact, ReferenceStudyRevision) and isinstance(
            result, ReferenceRunResult
        ):
            self._bind_reference(artifact, result)
        elif isinstance(artifact, MaxSpeedSweepDefinition) and isinstance(
            result, MaxSpeedSweepResult
        ):
            self._bind_e3(result)
        elif isinstance(
            artifact, EnvironmentSelectionComparisonDefinition
        ) and isinstance(result, EnvironmentSelectionComparisonResult):
            self._bind_e4(result)
        elif isinstance(artifact, B3StudyRevision) and isinstance(
            result, B3CuratedRunResult
        ):
            self._bind_b3(artifact, result)
        else:
            return False
        self.changed.emit()
        return True

    def _bind_controlled(
        self, revision: StudyRevision, result: WorkbenchRunResult
    ) -> None:
        view = inspect_controlled_locomotion_results(revision, result)
        self._overview_title = "Run overview"
        self._explore_title = "Recorded population"
        self._analysis_title = "Locomotion analysis"
        population = view.population_observations
        overview: list[MeaningItem] = [
            MeaningItem(label="Run ID", value=view.provenance.run_id),
            MeaningItem(
                label="Study revision", value=view.provenance.study_revision_id
            ),
            MeaningItem(
                label="Population evidence",
                value=_availability_text(view.population_availability),
            ),
            MeaningItem(
                label="Locomotion measurement",
                value=_availability_text(view.locomotion_availability),
            ),
        ]
        if population:
            overview.append(
                MeaningItem(
                    label="Final population", value=str(population[-1].population_size)
                )
            )
        self._overview.set_items(overview)
        self._explore.set_items(
            tuple(
                MeaningItem(
                    label=f"Committed step {item.step_index}",
                    value=(
                        f"population {item.population_size} · resources "
                        f"{item.total_resources} · mean energy {_number(item.energy.mean)}"
                    ),
                )
                for item in population
            )
        )
        if view.locomotion is None:
            self._analysis.set_items(
                (
                    MeaningItem(
                        label="Unavailable",
                        value=_availability_text(view.locomotion_availability),
                    ),
                )
            )
        else:
            value = view.locomotion
            self._analysis.set_items(
                (
                    MeaningItem(
                        label="Applied movements",
                        value=str(value.applied_movement_count),
                    ),
                    MeaningItem(
                        label="Total realized distance",
                        value=_number(value.total_realized_distance),
                    ),
                    MeaningItem(
                        label="Mean realized distance / applied movement",
                        value=_number(
                            value.mean_realized_distance_per_applied_movement
                        ),
                    ),
                    MeaningItem(
                        label="Total locomotion energy",
                        value=str(value.total_locomotion_energy_expenditure),
                    ),
                )
            )
        self._set_revision_provenance(view.provenance, view.scientific_provenance)

    def _bind_reference(
        self, revision: ReferenceStudyRevision, result: ReferenceRunResult
    ) -> None:
        view = inspect_reference_study_results(revision, result)
        self._overview_title = "Recorded evidence overview"
        self._explore_title = "Evidence counts"
        self._analysis_title = "Analysis availability"
        availabilities = (
            ("Population", view.population_availability),
            ("Committed events", view.event_availability),
            ("Pedigree / life history", view.pedigree_availability),
            ("Genetic composition", view.genetic_availability),
            ("Spatial replay", view.spatial_availability),
        )
        final_population = (
            str(view.population_observations[-1].population_size)
            if view.population_observations
            else "unavailable"
        )
        self._overview.set_items(
            (
                MeaningItem(label="Run ID", value=view.provenance.run_id),
                MeaningItem(label="Final population", value=final_population),
                *(
                    MeaningItem(label=label, value=_availability_text(value))
                    for label, value in availabilities
                ),
            )
        )
        self._explore.set_items(
            (
                MeaningItem(
                    label="Population observations",
                    value=str(len(view.population_observations)),
                ),
                MeaningItem(
                    label="Committed events", value=str(len(view.applied_events))
                ),
                MeaningItem(
                    label="Pedigree records", value=str(len(view.pedigree_records))
                ),
                MeaningItem(
                    label="Genetic observations",
                    value=str(len(view.genetic_observations)),
                ),
                MeaningItem(
                    label="Spatial frames", value=str(len(view.spatial_observations))
                ),
            )
        )
        self._analysis.set_items(
            tuple(
                MeaningItem(label=label, value=_availability_text(value))
                for label, value in availabilities
            )
        )
        self._set_revision_provenance(view.provenance, view.scientific_provenance)

    def _bind_e3(self, result: MaxSpeedSweepResult) -> None:
        view = inspect_max_speed_sweep_results(result)
        self._overview_title = "Treatment summaries"
        self._explore_title = "Replicates"
        self._analysis_title = "Existing treatment analysis"
        self._overview.set_items(
            tuple(
                MeaningItem(
                    label=f"Maximum speed {summary.treatment.max_speed}",
                    value=(
                        f"{summary.replicate_count} replicates · mean final population "
                        f"{_number(summary.mean_final_population_size)} · mean births "
                        f"{_number(summary.mean_cumulative_birth_count)} · extinctions "
                        f"{summary.extinction_count}"
                    ),
                )
                for summary in view.treatment_summaries
            )
        )
        self._explore.set_items(
            tuple(
                MeaningItem(
                    label=f"Speed {replicate.factor_level} · seed {replicate.seed}",
                    value=(
                        f"treatment {replicate.treatment_id} · manifest "
                        f"{replicate.manifest_digest[:12]}… · final population "
                        f"{replicate.outcome.final_population_size} · births "
                        f"{replicate.outcome.cumulative_birth_count}"
                    ),
                )
                for replicate in view.replicates
            )
        )
        self._analysis.set_items(
            tuple(
                MeaningItem(
                    label=f"Speed {summary.treatment.max_speed}",
                    value=(
                        f"mean resource consumed {_number(summary.mean_total_resource_consumed)} · "
                        f"mean realized distance {_number(summary.mean_total_realized_distance)} · "
                        f"mean locomotion energy "
                        f"{_number(summary.mean_total_locomotion_energy_expenditure)}"
                    ),
                )
                for summary in view.treatment_summaries
            )
        )
        self._provenance.set_items(
            (
                MeaningItem(label="Factor", value="Maximum speed"),
                MeaningItem(
                    label="Evidence IDs",
                    value=", ".join(result.definition.evidence_plan.requested),
                ),
                MeaningItem(
                    label="Replicate seeds",
                    value=", ".join(str(seed) for seed in result.definition.seeds),
                ),
            )
        )

    def _bind_e4(self, result: EnvironmentSelectionComparisonResult) -> None:
        view = inspect_environment_selection_results(result)
        self._overview_title = "Environment summaries"
        self._explore_title = "Matched-arm replicates"
        self._analysis_title = "Existing selection summaries"
        self._overview.set_items(
            tuple(
                MeaningItem(
                    label=_humanize(summary.environment),
                    value=(
                        f"{summary.replicate_count} replicates · "
                        f"{summary.defined_endpoint_count} defined endpoints · "
                        f"{summary.extinction_count} extinctions"
                    ),
                )
                for summary in view.environment_summaries
            )
        )
        self._explore.set_items(
            tuple(
                MeaningItem(
                    label=(
                        f"{replicate.role.title()} · {_humanize(replicate.factor_level)} · "
                        f"seed {replicate.seed}"
                    ),
                    value=(
                        f"treatment {replicate.treatment_id} · standing composition "
                        f"{_integers(replicate.standing_focal_composition)} · founder order "
                        f"{_integers(replicate.founder_speed_order)} · final frequencies "
                        f"{_optional_numbers(replicate.outcome.final_composition.frequencies)}"
                    ),
                )
                for replicate in view.replicates
            )
        )
        analysis: list[MeaningItem] = []
        for summary in view.environment_summaries:
            for index, speed in enumerate(E4_FOCAL_SPEEDS):
                analysis.append(
                    MeaningItem(
                        label=f"{_humanize(summary.environment)} · speed {speed}",
                        value=(
                            f"mean final frequency {_optional_number(summary.mean_final_frequencies[index])} · "
                            f"mean frequency change {_optional_number(summary.mean_frequency_changes[index])} · "
                            f"mean births {_number(summary.mean_births_by_speed[index])} · "
                            f"mean resources {_number(summary.mean_resources_by_speed[index])}"
                        ),
                    )
                )
        self._analysis.set_items(analysis)
        self._provenance.set_items(
            (
                MeaningItem(label="Factor", value="Resource geography"),
                MeaningItem(
                    label="Control / treatment",
                    value=(
                        f"{_humanize(result.definition.control_environment)} / "
                        f"{_humanize(result.definition.treatment_environment)}"
                    ),
                ),
                MeaningItem(
                    label="Standing focal composition",
                    value=_integers(result.definition.focal_speeds),
                ),
                MeaningItem(
                    label="Evidence IDs",
                    value=", ".join(result.definition.evidence_plan.requested),
                ),
            )
        )

    def _bind_b3(self, revision: B3StudyRevision, result: B3CuratedRunResult) -> None:
        view = inspect_b3_results(revision, result)
        self._overview_title = "Curated study overview"
        self._explore_title = "Primary confirmation"
        self._analysis_title = "Sensitivity and counterbalance"
        self._overview.set_items(
            (
                MeaningItem(label="Run ID", value=view.provenance.run_id),
                MeaningItem(label="Scenario origin", value=view.scenario_origin),
                MeaningItem(
                    label="Validated scenario",
                    value=view.scenario_identity
                    or "none — B3-derived sensitivity Study",
                ),
                MeaningItem(
                    label="Primary confirmation pairs",
                    value=str(len(view.confirmation)),
                ),
                MeaningItem(
                    label="Radius-sensitivity runs",
                    value=str(len(view.radius_sensitivity)),
                ),
                MeaningItem(
                    label="Counterbalanced pairs", value=str(len(view.counterbalanced))
                ),
                MeaningItem(
                    label="Scientific story handoff",
                    value=_availability_text(view.cinematic_handoff_availability),
                ),
            )
        )
        self._explore.set_items(
            tuple(
                MeaningItem(
                    label=f"Matched seed {pair.summary.seed}",
                    value=(
                        f"founder assignment {_humanize(pair.summary.founder_assignment)} · "
                        f"compact − uniform primary effect "
                        f"{_optional_number(pair.summary.primary_effect)}"
                    ),
                )
                for pair in view.confirmation
            )
        )
        sensitivity = tuple(
            MeaningItem(
                label=f"Radius sensitivity · seed {item.summary.seed}",
                value=(
                    f"{_humanize(item.summary.environment)} · primary high-speed frequency "
                    f"{_optional_number(item.summary.primary_high_speed_frequency)}"
                ),
            )
            for item in view.radius_sensitivity
        )
        counterbalance = tuple(
            MeaningItem(
                label=f"Founder counterbalance · seed {pair.summary.seed}",
                value=(
                    f"assignment {_humanize(pair.summary.founder_assignment)} · primary effect "
                    f"{_optional_number(pair.summary.primary_effect)}"
                ),
            )
            for pair in view.counterbalanced
        )
        self._analysis.set_items((*sensitivity, *counterbalance))
        self._set_revision_provenance(view.provenance, None)

    def _set_revision_provenance(self, provenance, scientific) -> None:
        rows = [
            MeaningItem(label="Run ID", value=provenance.run_id),
            MeaningItem(label="Study revision", value=provenance.study_revision_id),
            MeaningItem(label="Manifest digest", value=provenance.manifest_digest),
            MeaningItem(label="Evidence IDs", value=", ".join(provenance.evidence_ids)),
        ]
        if scientific is not None:
            rows.extend(
                (
                    MeaningItem(label="Experiment", value=scientific.experiment_id),
                    MeaningItem(label="Scenario", value=scientific.scenario_id),
                    MeaningItem(label="Treatment", value=scientific.treatment_id),
                    MeaningItem(label="Seed / replicate", value=str(scientific.seed)),
                    MeaningItem(label="Run role", value=str(scientific.run_role)),
                )
            )
        self._provenance.set_items(rows)

    def _clear_models(self) -> None:
        self._overview_title = "Overview"
        self._explore_title = "Explore"
        self._analysis_title = "Analysis"
        self._overview.set_items(())
        self._explore.set_items(())
        self._analysis.set_items(())
        self._provenance.set_items(())


def _availability_text(value: AnalysisAvailability) -> str:
    if value.available:
        return "Available from recorded evidence"
    if value.unavailable_reason is not None:
        return value.unavailable_reason
    missing = ", ".join(value.missing_evidence_ids)
    return f"Unavailable — missing {missing}; run again with the required EvidencePlan."


def _number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _optional_number(value: float | None) -> str:
    return "undefined" if value is None else _number(value)


def _optional_numbers(values: tuple[float | None, ...]) -> str:
    return ", ".join(_optional_number(value) for value in values)


def _integers(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = ["ResultsController"]
