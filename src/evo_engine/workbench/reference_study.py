"""Persistence and execution for bounded WB4 reference-ecology studies."""

from __future__ import annotations

import hashlib
import json
import uuid

import attrs

from evo_engine.experiments.science import (
    ScientificRunProvenance,
    canonical_treatment_specification,
)
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent
from evo_engine.workbench.reference_ecology import (
    EVENT_EVIDENCE_ID,
    GENETIC_EVIDENCE_ID,
    HORIZON_SLOT,
    PEDIGREE_EVIDENCE_ID,
    POPULATION_EVIDENCE_ID,
    SEED_SLOT,
    SPATIAL_EVIDENCE_ID,
    ReferenceEcologyDiff,
    ReferenceEcologyIntent,
    ReferenceEcologyManifest,
    ReferenceEvidencePlan,
    assess_reference_readiness,
    compile_reference_ecology,
    normalized_reference_explicit_values,
    resolve_reference_ecology,
    semantic_reference_diff,
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
        _require_nonempty(self.revision_id, name="revision_id")
        if not isinstance(self.intent, ReferenceEcologyIntent):
            raise TypeError("intent must be a ReferenceEcologyIntent.")
        if not isinstance(self.manifest, ReferenceEcologyManifest):
            raise TypeError("manifest must be a ReferenceEcologyManifest.")
        if not isinstance(self.evidence_plan, ReferenceEvidencePlan):
            raise TypeError("evidence_plan must be a ReferenceEvidencePlan.")
        if self.parent_revision_id is not None:
            _require_nonempty(self.parent_revision_id, name="parent_revision_id")
            if self.parent_revision_id == self.revision_id:
                raise ValueError("parent_revision_id must differ from revision_id.")
        if _normalize_saved_intent(self.intent) != self.intent:
            raise ValueError("Stored reference intent contains inactive stale values.")
        readiness = assess_reference_readiness(self.intent, self.evidence_plan)
        if readiness.state != "ready":
            raise ValueError(
                "Stored reference intent is outside the WB4 support envelope."
            )
        if (
            normalized_reference_explicit_values(self.intent)
            != self.manifest.explicit_values
        ):
            raise ValueError("Stored reference intent does not match stored manifest.")
        _validate_runs(self)

    def with_run(self, provenance: WorkbenchRunProvenance) -> ReferenceStudyRevision:
        """Return a new immutable snapshot with one completed-run reference."""
        if not isinstance(provenance, WorkbenchRunProvenance):
            raise TypeError("provenance must be a WorkbenchRunProvenance.")
        _validate_run_for_revision(provenance, revision=self)
        if any(run.run_id == provenance.run_id for run in self.runs):
            raise ValueError(f"Run ID {provenance.run_id!r} is already recorded.")
        return attrs.evolve(self, runs=(*self.runs, provenance))

    def to_json(self) -> str:
        """Serialize the exact saved revision canonically."""
        return json.dumps(
            {
                "evidence_plan": {"requested": list(self.evidence_plan.requested)},
                "format_id": REFERENCE_STUDY_FORMAT_ID,
                "format_version": REFERENCE_STUDY_FORMAT_VERSION,
                "intent": attrs.asdict(self.intent),
                "manifest_json": self.manifest.to_json(),
                "parent_revision_id": self.parent_revision_id,
                "revision_id": self.revision_id,
                "runs": [_run_to_mapping(run) for run in self.runs],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_json(cls, value: str) -> ReferenceStudyRevision:
        """Load stored intent and exact manifest without re-resolving defaults."""
        if type(value) is not str:
            raise TypeError("value must be a string.")
        decoded = json.loads(value)
        if type(decoded) is not dict:
            raise ValueError("study JSON must encode an object.")
        if decoded.get("format_id") != REFERENCE_STUDY_FORMAT_ID:
            raise ValueError("Unsupported reference study format ID.")
        if decoded.get("format_version") != REFERENCE_STUDY_FORMAT_VERSION:
            raise ValueError("Unsupported reference study format version.")
        plan_mapping = _required_mapping(decoded, "evidence_plan")
        requested = _required_string_list(plan_mapping, "requested")
        runs = decoded.get("runs")
        if type(runs) is not list:
            raise TypeError("runs must be a JSON array.")
        return cls(
            revision_id=_required_string(decoded, "revision_id"),
            parent_revision_id=_optional_string(decoded, "parent_revision_id"),
            intent=_intent_from_mapping(_required_mapping(decoded, "intent")),
            manifest=ReferenceEcologyManifest.from_json(
                _required_string(decoded, "manifest_json")
            ),
            evidence_plan=ReferenceEvidencePlan(requested=tuple(requested)),
            runs=tuple(_run_from_mapping(item) for item in runs),
        )


@attrs.frozen(slots=True, kw_only=True)
class ReferenceRunResult:
    """Expose immutable evidence from one completed reference study run."""

    provenance: WorkbenchRunProvenance
    scientific_provenance: ScientificRunProvenance
    population_observations: tuple[PopulationObservation, ...]
    applied_events: tuple[AppliedEvent, ...]
    pedigree_records: tuple[IndividualLifeHistory, ...]
    genetic_observations: tuple[GeneticCompositionObservation, ...]
    spatial_observations: tuple[SpatialObservation, ...]


def create_reference_study_revision(
    *,
    revision_id: str,
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> ReferenceStudyRevision:
    """Resolve authoring intent into one immutable saved reference study."""
    _require_nonempty(revision_id, name="revision_id")
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    normalized_intent = _normalize_saved_intent(intent)
    manifest = resolve_reference_ecology(normalized_intent, plan)
    return ReferenceStudyRevision(
        revision_id=revision_id,
        intent=normalized_intent,
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
    if not isinstance(parent, ReferenceStudyRevision):
        raise TypeError("parent must be a ReferenceStudyRevision.")
    _require_nonempty(revision_id, name="revision_id")
    if revision_id == parent.revision_id:
        raise ValueError("A fork must use a new revision_id.")
    plan = parent.evidence_plan if evidence_plan is None else evidence_plan
    normalized_intent = _normalize_saved_intent(intent)
    manifest = resolve_reference_ecology(normalized_intent, plan)
    return ReferenceStudyRevision(
        revision_id=revision_id,
        parent_revision_id=parent.revision_id,
        intent=normalized_intent,
        manifest=manifest,
        evidence_plan=plan,
    )


def diff_reference_study_revisions(
    before: ReferenceStudyRevision,
    after: ReferenceStudyRevision,
) -> ReferenceEcologyDiff:
    """Return the stable semantic diff between two reference study revisions."""
    if not isinstance(before, ReferenceStudyRevision) or not isinstance(
        after, ReferenceStudyRevision
    ):
        raise TypeError("before and after must be ReferenceStudyRevision values.")
    return semantic_reference_diff(before.manifest, after.manifest)


def run_reference_study_revision(
    revision: ReferenceStudyRevision,
    *,
    run_id: str | None = None,
) -> ReferenceRunResult:
    """Compile, run, and tie concrete evidence to the exact saved manifest."""
    if not isinstance(revision, ReferenceStudyRevision):
        raise TypeError("revision must be a ReferenceStudyRevision.")
    resolved_run_id = uuid.uuid4().hex if run_id is None else run_id
    _require_nonempty(resolved_run_id, name="run_id")
    prepared = compile_reference_ecology(revision.manifest, revision.evidence_plan)
    prepared.compiled.engine.run(prepared.compiled.simulation)
    population = (
        ()
        if prepared.evidence.population_recorder is None
        else prepared.evidence.population_recorder.observations
    )
    events = (
        ()
        if prepared.evidence.event_recorder is None
        else prepared.evidence.event_recorder.events
    )
    pedigree = (
        ()
        if prepared.evidence.pedigree_recorder is None
        else prepared.evidence.pedigree_recorder.records
    )
    genetics = (
        ()
        if prepared.evidence.genetic_recorder is None
        else prepared.evidence.genetic_recorder.observations
    )
    spatial = (
        ()
        if prepared.evidence.spatial_recorder is None
        else prepared.evidence.spatial_recorder.observations
    )
    provenance = _workbench_provenance(
        revision,
        run_id=resolved_run_id,
    )
    return ReferenceRunResult(
        provenance=provenance,
        scientific_provenance=_scientific_provenance(revision),
        population_observations=population,
        applied_events=events,
        pedigree_records=pedigree,
        genetic_observations=genetics,
        spatial_observations=spatial,
    )


def _workbench_provenance(
    revision: ReferenceStudyRevision,
    *,
    run_id: str,
) -> WorkbenchRunProvenance:
    evidence_references = tuple(
        f"{run_id}:{suffix}"
        for evidence_id, suffix in (
            (POPULATION_EVIDENCE_ID, "population-observations"),
            (EVENT_EVIDENCE_ID, "committed-events"),
            (PEDIGREE_EVIDENCE_ID, "pedigree"),
            (GENETIC_EVIDENCE_ID, "genetic-composition"),
            (SPATIAL_EVIDENCE_ID, "spatial-replay"),
        )
        if evidence_id in revision.evidence_plan.requested
    )
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=evidence_references,
        result_references=(),
    )


def _scientific_provenance(
    revision: ReferenceStudyRevision,
) -> ScientificRunProvenance:
    treatment_specification_json = canonical_treatment_specification(
        dict(revision.manifest.explicit_values)
    )
    treatment_digest = hashlib.sha256(
        treatment_specification_json.encode("utf-8")
    ).hexdigest()[:12]
    state_evidence_ids = {
        POPULATION_EVIDENCE_ID,
        PEDIGREE_EVIDENCE_ID,
        GENETIC_EVIDENCE_ID,
        SPATIAL_EVIDENCE_ID,
    }
    return ScientificRunProvenance(
        experiment_id="workbench-reference-ecology",
        scenario_id=(f"bounded-reference-ecology-v{revision.manifest.recipe_version}"),
        treatment_id=f"custom-reference-ecology-{treatment_digest}",
        treatment_specification_json=treatment_specification_json,
        seed=cast_int(revision.manifest.explicit_value(SEED_SLOT)),
        horizon_step_index=cast_int(revision.manifest.explicit_value(HORIZON_SLOT)),
        observation_every_n_steps=1,
        observation_include_step_zero=bool(
            state_evidence_ids.intersection(revision.evidence_plan.requested)
        ),
        focal_variables=_focal_variables(revision.evidence_plan),
    )


def _focal_variables(plan: ReferenceEvidencePlan) -> tuple[str, ...]:
    variables: list[str] = []
    mapping = (
        (POPULATION_EVIDENCE_ID, "population_traits"),
        (EVENT_EVIDENCE_ID, "committed_events"),
        (PEDIGREE_EVIDENCE_ID, "pedigree"),
        (GENETIC_EVIDENCE_ID, "genetic_composition"),
        (SPATIAL_EVIDENCE_ID, "spatial_state"),
    )
    for evidence_id, variable in mapping:
        if evidence_id in plan.requested:
            variables.append(variable)
    return tuple(variables)


def _normalize_saved_intent(intent: ReferenceEcologyIntent) -> ReferenceEcologyIntent:
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")
    patch_enabled = intent.resource_geography == "two_patches"
    mutation_enabled = intent.mutation_enabled is True
    return attrs.evolve(
        intent,
        gaussian_standard_deviation=(
            intent.gaussian_standard_deviation
            if intent.exploration_movement == "gaussian"
            else None
        ),
        patch_1_center_x=intent.patch_1_center_x if patch_enabled else None,
        patch_1_center_y=intent.patch_1_center_y if patch_enabled else None,
        patch_1_radius=intent.patch_1_radius if patch_enabled else None,
        patch_2_center_x=intent.patch_2_center_x if patch_enabled else None,
        patch_2_center_y=intent.patch_2_center_y if patch_enabled else None,
        patch_2_radius=intent.patch_2_radius if patch_enabled else None,
        mutation_probability_ppm=(
            intent.mutation_probability_ppm if mutation_enabled else None
        ),
        mutation_max_change=intent.mutation_max_change if mutation_enabled else None,
    )


def _validate_runs(revision: ReferenceStudyRevision) -> None:
    if type(revision.runs) is not tuple:
        raise TypeError("runs must be a tuple.")
    for index, run in enumerate(revision.runs):
        if not isinstance(run, WorkbenchRunProvenance):
            raise TypeError(f"runs[{index}] must be a WorkbenchRunProvenance.")
        _validate_run_for_revision(run, revision=revision)


def _validate_run_for_revision(
    run: WorkbenchRunProvenance,
    *,
    revision: ReferenceStudyRevision,
) -> None:
    if run.study_revision_id != revision.revision_id:
        raise ValueError("Run provenance references a different study revision.")
    if run.manifest_digest != revision.manifest.digest:
        raise ValueError("Run provenance references a different manifest.")
    if run.evidence_ids != revision.evidence_plan.requested:
        raise ValueError("Run provenance references a different evidence plan.")


def _intent_from_mapping(mapping: dict[object, object]) -> ReferenceEcologyIntent:
    return ReferenceEcologyIntent(
        width=_optional_int(mapping, "width"),
        height=_optional_int(mapping, "height"),
        founder_population=_optional_int(mapping, "founder_population"),
        founder_energy=_optional_int(mapping, "founder_energy"),
        horizon=_optional_int(mapping, "horizon"),
        seed=_optional_int(mapping, "seed"),
        max_speed=_optional_int(mapping, "max_speed"),
        sensory_range=_optional_int(mapping, "sensory_range"),
        sensory_accuracy=_optional_int(mapping, "sensory_accuracy"),
        exploration_movement=_optional_string(mapping, "exploration_movement"),
        gaussian_standard_deviation=_optional_int(
            mapping,
            "gaussian_standard_deviation",
        ),
        resource_geography=_optional_string(mapping, "resource_geography"),
        resource_generation_amount=_optional_int(
            mapping,
            "resource_generation_amount",
        ),
        resource_deposits_per_step=_optional_int(
            mapping,
            "resource_deposits_per_step",
        ),
        patch_1_center_x=_optional_int(mapping, "patch_1_center_x"),
        patch_1_center_y=_optional_int(mapping, "patch_1_center_y"),
        patch_1_radius=_optional_int(mapping, "patch_1_radius"),
        patch_2_center_x=_optional_int(mapping, "patch_2_center_x"),
        patch_2_center_y=_optional_int(mapping, "patch_2_center_y"),
        patch_2_radius=_optional_int(mapping, "patch_2_radius"),
        mutation_enabled=_optional_bool(mapping, "mutation_enabled"),
        mutation_probability_ppm=_optional_int(
            mapping,
            "mutation_probability_ppm",
        ),
        mutation_max_change=_optional_int(mapping, "mutation_max_change"),
        recombination_probability_ppm=_optional_int(
            mapping,
            "recombination_probability_ppm",
        ),
    )


def _run_to_mapping(run: WorkbenchRunProvenance) -> dict[str, object]:
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
    return WorkbenchRunProvenance(
        run_id=_required_string(value, "run_id"),
        study_revision_id=_required_string(value, "study_revision_id"),
        manifest_digest=_required_string(value, "manifest_digest"),
        evidence_ids=tuple(_required_string_list(value, "evidence_ids")),
        evidence_references=tuple(_required_string_list(value, "evidence_references")),
        result_references=tuple(_required_string_list(value, "result_references")),
    )


def _required_mapping(
    mapping: dict[object, object],
    key: str,
) -> dict[object, object]:
    value = mapping.get(key)
    if type(value) is not dict:
        raise TypeError(f"{key} must be a JSON object.")
    return value


def _required_string(mapping: dict[object, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _required_string_list(
    mapping: dict[object, object],
    key: str,
) -> list[str]:
    value = mapping.get(key)
    if type(value) is not list or not all(type(item) is str for item in value):
        raise TypeError(f"{key} must be a string array.")
    return value


def _optional_string(mapping: dict[object, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be null or a non-empty string.")
    return value


def _optional_int(mapping: dict[object, object], key: str) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{key} must be null or an integer.")
    return value


def _optional_bool(mapping: dict[object, object], key: str) -> bool | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not bool:
        raise TypeError(f"{key} must be null or a boolean.")
    return value


def _require_nonempty(value: str, *, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")


def cast_int(value: object) -> int:
    """Return an exact integer manifest scalar or fail loudly."""
    if type(value) is not int:
        raise TypeError("Expected an integer manifest scalar.")
    return value


__all__ = [
    "REFERENCE_STUDY_FORMAT_ID",
    "REFERENCE_STUDY_FORMAT_VERSION",
    "ReferenceRunResult",
    "ReferenceStudyRevision",
    "create_reference_study_revision",
    "diff_reference_study_revisions",
    "fork_reference_study_revision",
    "run_reference_study_revision",
]
