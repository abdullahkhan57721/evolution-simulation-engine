"""Persistence and execution for bounded WB4 reference-ecology studies."""

from __future__ import annotations

import json
import uuid

import attrs

from evo_engine.observation import (
    GeneticCompositionObservation,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent
from evo_engine.workbench.reference_ecology import (
    ReferenceEcologyDiff,
    ReferenceEcologyIntent,
    ReferenceEcologyManifest,
    ReferenceEvidencePlan,
    compile_reference_ecology,
    resolve_reference_ecology,
    semantic_diff,
)
from evo_engine.workbench.study import WorkbenchRunProvenance

REFERENCE_STUDY_FORMAT_ID = "evolution-experiment-workbench-reference-study"
REFERENCE_STUDY_FORMAT_VERSION = 1


@attrs.frozen(slots=True, kw_only=True)
class ReferenceStudyRevision:
    """Persist one immutable bounded reference-ecology study revision."""

    revision_id: str
    intent: ReferenceEcologyIntent
    manifest: ReferenceEcologyManifest
    evidence_plan: ReferenceEvidencePlan
    parent_revision_id: str | None = None
    runs: tuple[WorkbenchRunProvenance, ...] = ()

    def __attrs_post_init__(self) -> None:
        if type(self.revision_id) is not str or not self.revision_id.strip():
            raise ValueError("revision_id must be a non-empty string.")
        if self.parent_revision_id == self.revision_id:
            raise ValueError("parent_revision_id must differ from revision_id.")
        if resolve_reference_ecology(self.intent, self.evidence_plan) != self.manifest:
            raise ValueError("Stored reference intent does not resolve to stored manifest.")
        for run in self.runs:
            if run.study_revision_id != self.revision_id:
                raise ValueError("Run provenance references a different revision.")
            if run.manifest_digest != self.manifest.digest:
                raise ValueError("Run provenance references a different manifest.")
            if run.evidence_ids != self.evidence_plan.requested:
                raise ValueError("Run provenance references a different evidence plan.")

    def with_run(self, provenance: WorkbenchRunProvenance) -> ReferenceStudyRevision:
        """Return an immutable revision snapshot with one completed run reference."""
        if provenance.study_revision_id != self.revision_id:
            raise ValueError("Run provenance references a different revision.")
        if provenance.manifest_digest != self.manifest.digest:
            raise ValueError("Run provenance references a different manifest.")
        if provenance.evidence_ids != self.evidence_plan.requested:
            raise ValueError("Run provenance references a different evidence plan.")
        if any(run.run_id == provenance.run_id for run in self.runs):
            raise ValueError("run_id is already recorded on this revision.")
        return attrs.evolve(self, runs=(*self.runs, provenance))

    def to_json(self) -> str:
        """Serialize this exact saved revision canonically."""
        return json.dumps(
            {
                "evidence_plan": {"requested": list(self.evidence_plan.requested)},
                "format_id": REFERENCE_STUDY_FORMAT_ID,
                "format_version": REFERENCE_STUDY_FORMAT_VERSION,
                "intent": attrs.asdict(self.intent),
                "manifest_json": self.manifest.to_json(),
                "parent_revision_id": self.parent_revision_id,
                "revision_id": self.revision_id,
                "runs": [_run_mapping(run) for run in self.runs],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_json(cls, value: str) -> ReferenceStudyRevision:
        """Load persisted intent and exact stored manifest without migration."""
        decoded = json.loads(value)
        if type(decoded) is not dict:
            raise ValueError("study JSON must encode an object.")
        if decoded.get("format_id") != REFERENCE_STUDY_FORMAT_ID:
            raise ValueError("Unsupported reference study format ID.")
        if decoded.get("format_version") != REFERENCE_STUDY_FORMAT_VERSION:
            raise ValueError("Unsupported reference study format version.")
        raw_intent = decoded.get("intent")
        raw_plan = decoded.get("evidence_plan")
        raw_runs = decoded.get("runs")
        if type(raw_intent) is not dict or type(raw_plan) is not dict or type(raw_runs) is not list:
            raise TypeError("Malformed reference study persistence payload.")
        requested = raw_plan.get("requested")
        if type(requested) is not list or not all(type(item) is str for item in requested):
            raise TypeError("evidence_plan.requested must be a string array.")
        return cls(
            revision_id=_required_string(decoded, "revision_id"),
            parent_revision_id=_optional_string(decoded, "parent_revision_id"),
            intent=ReferenceEcologyIntent(**raw_intent),
            manifest=ReferenceEcologyManifest.from_json(_required_string(decoded, "manifest_json")),
            evidence_plan=ReferenceEvidencePlan(requested=tuple(requested)),
            runs=tuple(_run_from_mapping(item) for item in raw_runs),
        )


@attrs.frozen(slots=True, kw_only=True)
class ReferenceRunResult:
    """Expose immutable evidence produced by one completed reference study run."""

    provenance: WorkbenchRunProvenance
    population_observations: tuple[PopulationObservation, ...]
    applied_events: tuple[AppliedEvent, ...]
    genetic_observations: tuple[GeneticCompositionObservation, ...]
    spatial_observations: tuple[SpatialObservation, ...]


def create_reference_study_revision(
    *,
    revision_id: str,
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> ReferenceStudyRevision:
    """Resolve authoring intent into one immutable saved reference study."""
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    manifest = resolve_reference_ecology(intent, plan)
    return ReferenceStudyRevision(
        revision_id=revision_id,
        intent=intent,
        manifest=manifest,
        evidence_plan=plan,
    )


def fork_reference_study_revision(
    parent: ReferenceStudyRevision,
    *,
    revision_id: str,
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> ReferenceStudyRevision:
    """Create a child revision from an explicitly supplied new semantic intent."""
    if revision_id == parent.revision_id:
        raise ValueError("A fork must use a new revision_id.")
    plan = parent.evidence_plan if evidence_plan is None else evidence_plan
    manifest = resolve_reference_ecology(intent, plan)
    return ReferenceStudyRevision(
        revision_id=revision_id,
        parent_revision_id=parent.revision_id,
        intent=intent,
        manifest=manifest,
        evidence_plan=plan,
    )


def diff_reference_study_revisions(
    before: ReferenceStudyRevision,
    after: ReferenceStudyRevision,
) -> ReferenceEcologyDiff:
    """Return the stable semantic diff between saved reference revisions."""
    return semantic_diff(before.manifest, after.manifest)


def run_reference_study_revision(
    revision: ReferenceStudyRevision,
    *,
    run_id: str | None = None,
) -> ReferenceRunResult:
    """Compile, run, and tie concrete evidence to the exact saved manifest."""
    resolved_run_id = uuid.uuid4().hex if run_id is None else run_id
    if type(resolved_run_id) is not str or not resolved_run_id.strip():
        raise ValueError("run_id must be a non-empty string.")
    prepared = compile_reference_ecology(revision.manifest, revision.evidence_plan)
    prepared.compiled.engine.run(prepared.compiled.simulation)
    population = () if prepared.evidence.population_recorder is None else prepared.evidence.population_recorder.observations
    events = () if prepared.evidence.event_recorder is None else prepared.evidence.event_recorder.events
    genetics = () if prepared.evidence.genetic_recorder is None else prepared.evidence.genetic_recorder.observations
    spatial = () if prepared.evidence.spatial_recorder is None else prepared.evidence.spatial_recorder.observations
    evidence_references = tuple(
        reference
        for enabled, reference in (
            (prepared.evidence.population_recorder is not None, f"{resolved_run_id}:population-observations"),
            (prepared.evidence.event_recorder is not None, f"{resolved_run_id}:committed-events"),
            (prepared.evidence.pedigree_recorder is not None, f"{resolved_run_id}:pedigree"),
            (prepared.evidence.genetic_recorder is not None, f"{resolved_run_id}:genetic-composition"),
            (prepared.evidence.spatial_recorder is not None, f"{resolved_run_id}:spatial-replay"),
        )
        if enabled
    )
    provenance = WorkbenchRunProvenance(
        run_id=resolved_run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=evidence_references,
        result_references=(),
    )
    return ReferenceRunResult(
        provenance=provenance,
        population_observations=population,
        applied_events=events,
        genetic_observations=genetics,
        spatial_observations=spatial,
    )


def _run_mapping(run: WorkbenchRunProvenance) -> dict[str, object]:
    return {
        "evidence_ids": list(run.evidence_ids),
        "evidence_references": list(run.evidence_references),
        "manifest_digest": run.manifest_digest,
        "result_references": list(run.result_references),
        "run_id": run.run_id,
        "study_revision_id": run.study_revision_id,
    }


def _run_from_mapping(value: object) -> WorkbenchRunProvenance:
    if type(value) is not dict:
        raise TypeError("runs entries must be JSON objects.")
    evidence_ids = _required_string_list(value, "evidence_ids")
    evidence_references = _required_string_list(value, "evidence_references")
    result_references = _required_string_list(value, "result_references")
    return WorkbenchRunProvenance(
        run_id=_required_string(value, "run_id"),
        study_revision_id=_required_string(value, "study_revision_id"),
        manifest_digest=_required_string(value, "manifest_digest"),
        evidence_ids=tuple(evidence_ids),
        evidence_references=tuple(evidence_references),
        result_references=tuple(result_references),
    )


def _required_string(mapping: dict[object, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _optional_string(mapping: dict[object, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be null or a non-empty string.")
    return value


def _required_string_list(mapping: dict[object, object], key: str) -> list[str]:
    value = mapping.get(key)
    if type(value) is not list or not all(type(item) is str for item in value):
        raise TypeError(f"{key} must be a string array.")
    return value
