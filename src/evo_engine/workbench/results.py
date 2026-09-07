"""Study-facing navigation over existing authoritative scientific artifacts.

WB5 deliberately keeps this module thin.  It associates already-produced evidence
and result values with exact Workbench provenance, reports evidence insufficiency,
and preserves treatment/replicate identity.  It does not calculate scientific
measurements, treatment summaries, causal claims, charts, or renderer state.
"""

from __future__ import annotations

import attrs

from evo_engine.experiments.e3_performance import E3ReplicateOutcome, E3TreatmentSummary
from evo_engine.experiments.e4_selection import E4EnvironmentSummary, E4ReplicateOutcome
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent
from evo_engine.workbench.b3_curated import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3_VALIDATED_SCENARIO_ID,
    B3CuratedRunResult,
    B3MatchedRunArtifacts,
    B3SingleRunArtifacts,
    B3StudyRevision,
)
from evo_engine.workbench.controlled_locomotion import (
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
)
from evo_engine.workbench.experiments import (
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
)
from evo_engine.workbench.reference_ecology import (
    EVENT_EVIDENCE_ID as REFERENCE_EVENT_EVIDENCE_ID,
)
from evo_engine.workbench.reference_ecology import (
    GENETIC_EVIDENCE_ID as REFERENCE_GENETIC_EVIDENCE_ID,
)
from evo_engine.workbench.reference_ecology import (
    PEDIGREE_EVIDENCE_ID as REFERENCE_PEDIGREE_EVIDENCE_ID,
)
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID as REFERENCE_POPULATION_EVIDENCE_ID,
)
from evo_engine.workbench.reference_ecology import (
    SPATIAL_EVIDENCE_ID as REFERENCE_SPATIAL_EVIDENCE_ID,
)
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    ReferenceStudyRevision,
)
from evo_engine.workbench.study import (
    StudyRevision,
    WorkbenchRunProvenance,
    WorkbenchRunResult,
)


@attrs.frozen(slots=True, kw_only=True)
class AnalysisAvailability:
    """Describe whether one concrete existing analysis/evidence view is available.

    This is not an evidence dependency solver.  Concrete builders below declare the
    small fixed evidence requirements of their already-established consumers.
    """

    analysis_id: str
    source_contract: str
    required_evidence_ids: tuple[str, ...]
    missing_evidence_ids: tuple[str, ...] = ()
    unavailable_reason: str | None = None

    def __attrs_post_init__(self) -> None:
        _require_nonempty(self.analysis_id, name="analysis_id")
        _require_nonempty(self.source_contract, name="source_contract")
        _validate_string_tuple(self.required_evidence_ids, name="required_evidence_ids")
        _validate_string_tuple(self.missing_evidence_ids, name="missing_evidence_ids")
        if not set(self.missing_evidence_ids).issubset(self.required_evidence_ids):
            raise ValueError("missing_evidence_ids must be required evidence IDs.")
        if self.unavailable_reason is not None:
            _require_nonempty(self.unavailable_reason, name="unavailable_reason")

    @property
    def available(self) -> bool:
        """Return whether the concrete view can be shown from recorded artifacts."""
        return not self.missing_evidence_ids and self.unavailable_reason is None


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionResultsView:
    """Navigate one WB1 run without replacing its E1 measurement contract."""

    provenance: WorkbenchRunProvenance
    scientific_provenance: ScientificRunProvenance
    population_observations: tuple[PopulationObservation, ...]
    locomotion: object | None
    population_availability: AnalysisAvailability
    locomotion_availability: AnalysisAvailability


@attrs.frozen(slots=True, kw_only=True)
class ReferenceStudyResultsView:
    """Navigate recorded WB4 evidence without inferring unrecorded evidence."""

    provenance: WorkbenchRunProvenance
    scientific_provenance: ScientificRunProvenance
    population_observations: tuple[PopulationObservation, ...]
    applied_events: tuple[AppliedEvent, ...]
    pedigree_records: tuple[IndividualLifeHistory, ...]
    genetic_observations: tuple[GeneticCompositionObservation, ...]
    spatial_observations: tuple[SpatialObservation, ...]
    population_availability: AnalysisAvailability
    event_availability: AnalysisAvailability
    pedigree_availability: AnalysisAvailability
    genetic_availability: AnalysisAvailability
    spatial_availability: AnalysisAvailability


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedSweepReplicateView:
    """Bind one existing E3 outcome to its authored semantic factor replicate."""

    factor_slot_id: str
    factor_level: int
    seed: int
    manifest_digest: str
    treatment_id: str
    outcome: E3ReplicateOutcome

    def __attrs_post_init__(self) -> None:
        if self.factor_slot_id != MAX_SPEED_SLOT:
            raise ValueError("E3 result navigation must preserve the max-speed factor.")
        if type(self.factor_level) is not int or type(self.seed) is not int:
            raise TypeError("factor_level and seed must be integers.")
        _require_nonempty(self.manifest_digest, name="manifest_digest")
        _require_nonempty(self.treatment_id, name="treatment_id")
        if self.outcome.treatment.max_speed != self.factor_level:
            raise ValueError("E3 outcome does not match the authored factor level.")
        if self.outcome.provenance.seed != self.seed:
            raise ValueError("E3 outcome does not match the authored replicate seed.")
        if self.outcome.treatment.treatment_id != self.treatment_id:
            raise ValueError("E3 outcome treatment identity changed during navigation.")


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedSweepResultsView:
    """Study-facing organization of unchanged E3 replicate and summary values."""

    definition: MaxSpeedSweepDefinition
    replicates: tuple[MaxSpeedSweepReplicateView, ...]
    treatment_summaries: tuple[E3TreatmentSummary, ...]


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentSelectionReplicateView:
    """Bind one E4 outcome to factor, arm, replicate, and counterbalance identity."""

    role: str
    factor_slot_id: str
    factor_level: str
    seed: int
    treatment_id: str
    founder_speed_order: tuple[int, int, int]
    standing_focal_composition: tuple[int, int, int]
    outcome: E4ReplicateOutcome

    def __attrs_post_init__(self) -> None:
        if self.role not in ("control", "treatment"):
            raise ValueError("role must be control or treatment.")
        if self.factor_slot_id != RESOURCE_GEOGRAPHY_SLOT:
            raise ValueError("E4 navigation must preserve resource geography as factor.")
        _require_nonempty(self.factor_level, name="factor_level")
        _require_nonempty(self.treatment_id, name="treatment_id")
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer.")
        if self.outcome.provenance.seed != self.seed:
            raise ValueError("E4 outcome does not match the authored replicate seed.")
        if self.outcome.treatment.environment != self.factor_level:
            raise ValueError("E4 outcome does not match the authored factor level.")
        if self.outcome.treatment.treatment_id != self.treatment_id:
            raise ValueError("E4 outcome treatment identity changed during navigation.")
        if self.outcome.treatment.founder_speed_order != self.founder_speed_order:
            raise ValueError("E4 founder-ID counterbalance changed during navigation.")


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentSelectionResultsView:
    """Study-facing organization of unchanged E4 evolutionary result values."""

    definition: EnvironmentSelectionComparisonDefinition
    replicates: tuple[EnvironmentSelectionReplicateView, ...]
    environment_summaries: tuple[E4EnvironmentSummary, E4EnvironmentSummary]


@attrs.frozen(slots=True, kw_only=True)
class B3ResultsView:
    """Keep B3 confirmation, sensitivity, and counterbalance artifacts distinct."""

    provenance: WorkbenchRunProvenance
    scenario_origin: str
    scenario_identity: str | None
    confirmation: tuple[B3MatchedRunArtifacts, ...]
    radius_sensitivity: tuple[B3SingleRunArtifacts, ...]
    counterbalanced: tuple[B3MatchedRunArtifacts, ...]
    cinematic_handoff_availability: AnalysisAvailability


def inspect_controlled_locomotion_results(
    revision: StudyRevision,
    result: WorkbenchRunResult,
) -> ControlledLocomotionResultsView:
    """Attach an existing WB1 run to its exact revision and evidence availability."""
    if not isinstance(revision, StudyRevision):
        raise TypeError("revision must be a StudyRevision.")
    if not isinstance(result, WorkbenchRunResult):
        raise TypeError("result must be a WorkbenchRunResult.")
    _validate_run_attachment(
        result.provenance,
        revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
    )
    population = _availability(
        requested=revision.evidence_plan.requested,
        analysis_id="controlled-locomotion.population-trajectory",
        source_contract="PopulationObservation",
        required=(POPULATION_EVIDENCE_ID,),
    )
    locomotion = _availability(
        requested=revision.evidence_plan.requested,
        analysis_id="controlled-locomotion.e1-locomotion-measurements",
        source_contract="LocomotionReplicateMeasurements",
        required=(EVENT_EVIDENCE_ID,),
    )
    if locomotion.available != (result.locomotion is not None):
        raise ValueError("WB1 locomotion result availability disagrees with evidence plan.")
    return ControlledLocomotionResultsView(
        provenance=result.provenance,
        scientific_provenance=result.scientific_provenance,
        population_observations=result.population_observations,
        locomotion=result.locomotion,
        population_availability=population,
        locomotion_availability=locomotion,
    )


def inspect_reference_study_results(
    revision: ReferenceStudyRevision,
    result: ReferenceRunResult,
) -> ReferenceStudyResultsView:
    """Attach WB4 evidence to the exact revision and report unavailable evidence."""
    if not isinstance(revision, ReferenceStudyRevision):
        raise TypeError("revision must be a ReferenceStudyRevision.")
    if not isinstance(result, ReferenceRunResult):
        raise TypeError("result must be a ReferenceRunResult.")
    _validate_run_attachment(
        result.provenance,
        revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
    )
    requested = revision.evidence_plan.requested
    return ReferenceStudyResultsView(
        provenance=result.provenance,
        scientific_provenance=result.scientific_provenance,
        population_observations=result.population_observations,
        applied_events=result.applied_events,
        pedigree_records=result.pedigree_records,
        genetic_observations=result.genetic_observations,
        spatial_observations=result.spatial_observations,
        population_availability=_availability(
            requested=requested,
            analysis_id="reference-ecology.population-history",
            source_contract="PopulationObservation",
            required=(REFERENCE_POPULATION_EVIDENCE_ID,),
        ),
        event_availability=_availability(
            requested=requested,
            analysis_id="reference-ecology.committed-events",
            source_contract="AppliedEvent",
            required=(REFERENCE_EVENT_EVIDENCE_ID,),
        ),
        pedigree_availability=_availability(
            requested=requested,
            analysis_id="reference-ecology.pedigree",
            source_contract="IndividualLifeHistory",
            required=(REFERENCE_PEDIGREE_EVIDENCE_ID,),
        ),
        genetic_availability=_availability(
            requested=requested,
            analysis_id="reference-ecology.genetic-composition",
            source_contract="GeneticCompositionObservation",
            required=(REFERENCE_GENETIC_EVIDENCE_ID,),
        ),
        spatial_availability=_availability(
            requested=requested,
            analysis_id="reference-ecology.spatial-replay",
            source_contract="SpatialObservation",
            required=(REFERENCE_SPATIAL_EVIDENCE_ID,),
        ),
    )


def inspect_max_speed_sweep_results(result: MaxSpeedSweepResult) -> MaxSpeedSweepResultsView:
    """Organize E3 results by authored factor/replicate without recomputing them."""
    if not isinstance(result, MaxSpeedSweepResult):
        raise TypeError("result must be a MaxSpeedSweepResult.")
    replicates = tuple(
        MaxSpeedSweepReplicateView(
            factor_slot_id=expanded.factor_slot_id,
            factor_level=expanded.factor_level,
            seed=expanded.seed,
            manifest_digest=expanded.manifest.digest,
            treatment_id=outcome.treatment.treatment_id,
            outcome=outcome,
        )
        for expanded, outcome in zip(
            result.treatments,
            result.replicate_outcomes,
            strict=True,
        )
    )
    return MaxSpeedSweepResultsView(
        definition=result.definition,
        replicates=replicates,
        treatment_summaries=result.treatment_summaries,
    )


def inspect_environment_selection_results(
    result: EnvironmentSelectionComparisonResult,
) -> EnvironmentSelectionResultsView:
    """Organize E4 results while keeping counterbalance separate from the factor."""
    if not isinstance(result, EnvironmentSelectionComparisonResult):
        raise TypeError("result must be an EnvironmentSelectionComparisonResult.")
    replicates = tuple(
        EnvironmentSelectionReplicateView(
            role=expanded.role,
            factor_slot_id=expanded.factor_slot_id,
            factor_level=expanded.factor_level,
            seed=expanded.seed,
            treatment_id=outcome.treatment.treatment_id,
            founder_speed_order=expanded.founder_speed_order,
            standing_focal_composition=expanded.standing_focal_composition,
            outcome=outcome,
        )
        for expanded, outcome in zip(
            result.treatments,
            result.replicate_outcomes,
            strict=True,
        )
    )
    return EnvironmentSelectionResultsView(
        definition=result.definition,
        replicates=replicates,
        environment_summaries=result.environment_summaries,
    )


def inspect_b3_results(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
) -> B3ResultsView:
    """Attach existing B3 artifacts while preserving evidence-role boundaries."""
    if not isinstance(revision, B3StudyRevision):
        raise TypeError("revision must be a B3StudyRevision.")
    if not isinstance(result, B3CuratedRunResult):
        raise TypeError("result must be a B3CuratedRunResult.")
    _validate_run_attachment(
        result.provenance,
        revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
    )
    if result.scenario_origin != revision.scenario_origin:
        raise ValueError("B3 result scenario origin does not match the study revision.")
    if result.scenario_identity != revision.scenario_identity:
        raise ValueError("B3 result scenario identity does not match the study revision.")

    reason = None
    if revision.scenario_identity != B3_VALIDATED_SCENARIO_ID:
        reason = (
            "This B3-derived fork does not inherit the validated B3 representative "
            "story or headline-claim cinematic handoff."
        )
    handoff = _availability(
        requested=revision.evidence_plan.requested,
        analysis_id="b3.confirmed-cinematic-scientific-handoff",
        source_contract="existing B3 scientific handoff",
        required=B3_REQUIRED_EVIDENCE_IDS,
        unavailable_reason=reason,
    )
    return B3ResultsView(
        provenance=result.provenance,
        scenario_origin=result.scenario_origin,
        scenario_identity=result.scenario_identity,
        confirmation=result.confirmation,
        radius_sensitivity=result.radius_sensitivity,
        counterbalanced=result.counterbalanced,
        cinematic_handoff_availability=handoff,
    )


def _availability(
    *,
    requested: tuple[str, ...],
    analysis_id: str,
    source_contract: str,
    required: tuple[str, ...],
    unavailable_reason: str | None = None,
) -> AnalysisAvailability:
    missing = tuple(evidence_id for evidence_id in required if evidence_id not in requested)
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract=source_contract,
        required_evidence_ids=required,
        missing_evidence_ids=missing,
        unavailable_reason=unavailable_reason,
    )


def _validate_run_attachment(
    provenance: WorkbenchRunProvenance,
    *,
    revision_id: str,
    manifest_digest: str,
    evidence_ids: tuple[str, ...],
) -> None:
    if provenance.study_revision_id != revision_id:
        raise ValueError("Run result belongs to a different Study revision.")
    if provenance.manifest_digest != manifest_digest:
        raise ValueError("Run result belongs to a different resolved manifest.")
    if provenance.evidence_ids != evidence_ids:
        raise ValueError("Run result belongs to a different evidence plan.")


def _validate_string_tuple(values: tuple[str, ...], *, name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple.")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates.")
    for index, value in enumerate(values):
        _require_nonempty(value, name=f"{name}[{index}]")


def _require_nonempty(value: object, *, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise TypeError(f"{name} must be a non-empty string.")
    return value
