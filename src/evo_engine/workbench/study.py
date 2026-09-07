"""Persistence, lineage, execution provenance, and forking for WB1 studies."""

from __future__ import annotations

import json
import uuid
from typing import cast

import attrs

from evo_engine.experiments.locomotion import (
    LocomotionReplicateMeasurements,
    summarize_locomotion_replicate,
)
from evo_engine.experiments.science import (
    ScientificRunProvenance,
    canonical_treatment_specification,
)
from evo_engine.observation import PopulationObservation
from evo_engine.telemetry import AppliedEvent
from evo_engine.workbench.controlled_locomotion import (
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT,
    ControlledLocomotionDiff,
    ControlledLocomotionIntent,
    ControlledLocomotionManifest,
    EvidencePlan,
    compile_controlled_locomotion,
    resolve_controlled_locomotion,
    semantic_diff,
)

STUDY_FORMAT_ID = "evolution-experiment-workbench-study"
STUDY_FORMAT_VERSION = 1


@attrs.frozen(slots=True, kw_only=True)
class WorkbenchRunProvenance:
    """Tie one completed Workbench run to its exact saved scientific manifest."""

    run_id: str
    study_revision_id: str
    manifest_digest: str
    evidence_ids: tuple[str, ...]
    evidence_references: tuple[str, ...]
    result_references: tuple[str, ...]

    def __attrs_post_init__(self) -> None:
        _require_nonempty_string(self.run_id, "run_id")
        _require_nonempty_string(self.study_revision_id, "study_revision_id")
        _require_nonempty_string(self.manifest_digest, "manifest_digest")
        _validate_string_tuple(self.evidence_ids, "evidence_ids")
        _validate_string_tuple(self.evidence_references, "evidence_references")
        _validate_string_tuple(self.result_references, "result_references")


@attrs.frozen(slots=True, kw_only=True)
class StudyRevision:
    """Persist one immutable WB1 authoring revision and its exact resolved manifest."""

    revision_id: str
    intent: ControlledLocomotionIntent
    manifest: ControlledLocomotionManifest
    evidence_plan: EvidencePlan
    parent_revision_id: str | None = None
    runs: tuple[WorkbenchRunProvenance, ...] = ()

    def __attrs_post_init__(self) -> None:
        _require_nonempty_string(self.revision_id, "revision_id")
        if not isinstance(self.intent, ControlledLocomotionIntent):
            raise TypeError("intent must be a ControlledLocomotionIntent.")
        if not isinstance(self.manifest, ControlledLocomotionManifest):
            raise TypeError("manifest must be a ControlledLocomotionManifest.")
        if not isinstance(self.evidence_plan, EvidencePlan):
            raise TypeError("evidence_plan must be an EvidencePlan.")
        if self.parent_revision_id is not None:
            _require_nonempty_string(self.parent_revision_id, "parent_revision_id")
            if self.parent_revision_id == self.revision_id:
                raise ValueError("parent_revision_id must differ from revision_id.")
        _validate_study_runs(
            self.runs,
            revision_id=self.revision_id,
            manifest_digest=self.manifest.digest,
            evidence_ids=self.evidence_plan.requested,
        )
        _validate_intent_manifest_alignment(self.intent, self.manifest)

    def with_run(self, provenance: WorkbenchRunProvenance) -> StudyRevision:
        """Return a new immutable snapshot with one completed-run reference."""
        if not isinstance(provenance, WorkbenchRunProvenance):
            raise TypeError("provenance must be a WorkbenchRunProvenance.")
        if provenance.study_revision_id != self.revision_id:
            raise ValueError("Run provenance references a different study revision.")
        if provenance.manifest_digest != self.manifest.digest:
            raise ValueError("Run provenance references a different manifest.")
        if provenance.evidence_ids != self.evidence_plan.requested:
            raise ValueError("Run provenance references a different evidence plan.")
        if any(run.run_id == provenance.run_id for run in self.runs):
            raise ValueError(f"Run ID {provenance.run_id!r} is already recorded.")
        return attrs.evolve(self, runs=(*self.runs, provenance))

    def to_json(self) -> str:
        """Serialize the exact saved revision canonically."""
        return json.dumps(
            {
                "evidence_plan": {"requested": list(self.evidence_plan.requested)},
                "format_id": STUDY_FORMAT_ID,
                "format_version": STUDY_FORMAT_VERSION,
                "intent": {
                    "max_speed": self.intent.max_speed,
                    "resource_geography": self.intent.resource_geography,
                    "seed": self.intent.seed,
                },
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
    def from_json(cls, value: str) -> StudyRevision:
        """Load stored intent and manifest exactly, without re-resolving defaults."""
        if type(value) is not str:
            raise TypeError("value must be a string.")
        decoded = json.loads(value)
        if type(decoded) is not dict:
            raise ValueError("study JSON must encode an object.")
        if decoded.get("format_id") != STUDY_FORMAT_ID:
            raise ValueError("Unsupported Workbench study format ID.")
        if decoded.get("format_version") != STUDY_FORMAT_VERSION:
            raise ValueError("Unsupported Workbench study format version.")

        intent_mapping = _required_mapping(decoded, "intent")
        plan_mapping = _required_mapping(decoded, "evidence_plan")
        requested = plan_mapping.get("requested")
        if type(requested) is not list:
            raise TypeError("evidence_plan.requested must be a JSON array.")

        runs_raw = decoded.get("runs")
        if type(runs_raw) is not list:
            raise TypeError("runs must be a JSON array.")
        return cls(
            revision_id=_required_string(decoded, "revision_id"),
            parent_revision_id=_optional_string(decoded, "parent_revision_id"),
            intent=ControlledLocomotionIntent(
                max_speed=_optional_int(intent_mapping, "max_speed"),
                resource_geography=_optional_string(
                    intent_mapping, "resource_geography"
                ),
                seed=_optional_int(intent_mapping, "seed"),
            ),
            manifest=ControlledLocomotionManifest.from_json(
                _required_string(decoded, "manifest_json")
            ),
            evidence_plan=EvidencePlan(
                requested=tuple(_list_of_strings(requested, "evidence_plan.requested"))
            ),
            runs=tuple(
                _run_from_mapping(item, index=index)
                for index, item in enumerate(runs_raw)
            ),
        )


@attrs.frozen(slots=True, kw_only=True)
class WorkbenchRunResult:
    """Expose immutable evidence/results from one completed WB1 run."""

    provenance: WorkbenchRunProvenance
    scientific_provenance: ScientificRunProvenance
    population_observations: tuple[PopulationObservation, ...]
    applied_events: tuple[AppliedEvent, ...]
    locomotion: LocomotionReplicateMeasurements | None = None


def create_study_revision(
    *,
    revision_id: str,
    intent: ControlledLocomotionIntent,
    evidence_plan: EvidencePlan | None = None,
) -> StudyRevision:
    """Resolve one authoring intent and create its first immutable saved revision."""
    _require_nonempty_string(revision_id, "revision_id")
    plan = EvidencePlan() if evidence_plan is None else evidence_plan
    manifest = resolve_controlled_locomotion(intent, plan)
    return StudyRevision(
        revision_id=revision_id,
        intent=intent,
        manifest=manifest,
        evidence_plan=plan,
    )


def fork_study_revision(
    parent: StudyRevision,
    *,
    revision_id: str,
    max_speed: int | None = None,
    resource_geography: str | None = None,
    seed: int | None = None,
    evidence_plan: EvidencePlan | None = None,
) -> StudyRevision:
    """Fork a saved revision by evolving only explicit WB1 authoring selections."""
    if not isinstance(parent, StudyRevision):
        raise TypeError("parent must be a StudyRevision.")
    _require_nonempty_string(revision_id, "revision_id")
    if revision_id == parent.revision_id:
        raise ValueError("A fork must use a new revision_id.")

    evolved_intent = attrs.evolve(
        parent.intent,
        max_speed=parent.intent.max_speed if max_speed is None else max_speed,
        resource_geography=(
            parent.intent.resource_geography
            if resource_geography is None
            else resource_geography
        ),
        seed=parent.intent.seed if seed is None else seed,
    )
    plan = parent.evidence_plan if evidence_plan is None else evidence_plan
    manifest = resolve_controlled_locomotion(evolved_intent, plan)
    return StudyRevision(
        revision_id=revision_id,
        parent_revision_id=parent.revision_id,
        intent=evolved_intent,
        manifest=manifest,
        evidence_plan=plan,
    )


def diff_study_revisions(
    before: StudyRevision,
    after: StudyRevision,
) -> ControlledLocomotionDiff:
    """Return the recipe-scoped semantic diff between two saved revisions."""
    if not isinstance(before, StudyRevision) or not isinstance(after, StudyRevision):
        raise TypeError("before and after must be StudyRevision values.")
    return semantic_diff(before.manifest, after.manifest)


def run_study_revision(
    revision: StudyRevision,
    *,
    run_id: str | None = None,
) -> WorkbenchRunResult:
    """Compile through authoritative preflight, run, and tie evidence to the manifest."""
    if not isinstance(revision, StudyRevision):
        raise TypeError("revision must be a StudyRevision.")
    resolved_run_id = uuid.uuid4().hex if run_id is None else run_id
    _require_nonempty_string(resolved_run_id, "run_id")

    prepared = compile_controlled_locomotion(
        revision.manifest,
        revision.evidence_plan,
    )
    prepared.compiled.engine.run(prepared.compiled.simulation)

    population_observations = (
        ()
        if prepared.evidence.population_recorder is None
        else prepared.evidence.population_recorder.observations
    )
    applied_events = (
        ()
        if prepared.evidence.event_recorder is None
        else prepared.evidence.event_recorder.events
    )
    scientific_provenance = _scientific_provenance(revision)

    locomotion = (
        summarize_locomotion_replicate(
            provenance=scientific_provenance,
            events=applied_events,
        )
        if prepared.evidence.event_recorder is not None
        else None
    )
    evidence_references = tuple(
        reference
        for enabled, reference in (
            (
                prepared.evidence.population_recorder is not None,
                f"{resolved_run_id}:population-observations",
            ),
            (
                prepared.evidence.event_recorder is not None,
                f"{resolved_run_id}:committed-events",
            ),
        )
        if enabled
    )
    result_references = (
        (f"{resolved_run_id}:e1-locomotion-measurements",)
        if locomotion is not None
        else ()
    )
    provenance = WorkbenchRunProvenance(
        run_id=resolved_run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=evidence_references,
        result_references=result_references,
    )
    return WorkbenchRunResult(
        provenance=provenance,
        scientific_provenance=scientific_provenance,
        population_observations=population_observations,
        applied_events=applied_events,
        locomotion=locomotion,
    )


def _scientific_provenance(revision: StudyRevision) -> ScientificRunProvenance:
    max_speed = cast(int, revision.intent.max_speed)
    geography = cast(str, revision.intent.resource_geography)
    seed = cast(int, revision.intent.seed)
    focal_variables: list[str] = []
    if POPULATION_EVIDENCE_ID in revision.evidence_plan.requested:
        focal_variables.append("max_speed")
    if EVENT_EVIDENCE_ID in revision.evidence_plan.requested:
        focal_variables.extend(("realized_movement", "locomotion_energy_expenditure"))
    return ScientificRunProvenance(
        experiment_id="workbench-controlled-locomotion",
        scenario_id=f"controlled-clonal-locomotion-v{revision.manifest.recipe_version}",
        treatment_id=f"{geography}-speed-{max_speed}",
        treatment_specification_json=canonical_treatment_specification(
            {
                "max_speed": max_speed,
                "resource_geography": geography,
            }
        ),
        seed=seed,
        horizon_step_index=cast(
            int,
            revision.manifest.derived_value("controlled-locomotion.horizon-step-index"),
        ),
        observation_every_n_steps=1,
        observation_include_step_zero=(
            POPULATION_EVIDENCE_ID in revision.evidence_plan.requested
        ),
        focal_variables=tuple(focal_variables),
    )


def _validate_study_runs(
    runs: tuple[WorkbenchRunProvenance, ...],
    *,
    revision_id: str,
    manifest_digest: str,
    evidence_ids: tuple[str, ...],
) -> None:
    if type(runs) is not tuple:
        raise TypeError("runs must be a tuple.")
    for index, run in enumerate(runs):
        if not isinstance(run, WorkbenchRunProvenance):
            raise TypeError(f"runs[{index}] must be a WorkbenchRunProvenance.")
        if run.study_revision_id != revision_id:
            raise ValueError(f"runs[{index}] must reference this study revision.")
        if run.manifest_digest != manifest_digest:
            raise ValueError(
                f"runs[{index}] must reference this revision's exact manifest."
            )
        if run.evidence_ids != evidence_ids:
            raise ValueError(
                f"runs[{index}] must reference this revision's exact evidence plan."
            )


def _validate_intent_manifest_alignment(
    intent: ControlledLocomotionIntent,
    manifest: ControlledLocomotionManifest,
) -> None:
    if manifest.explicit_value(MAX_SPEED_SLOT) != intent.max_speed:
        raise ValueError("Stored intent max_speed does not match stored manifest.")
    if manifest.explicit_value(RESOURCE_GEOGRAPHY_SLOT) != intent.resource_geography:
        raise ValueError(
            "Stored intent resource_geography does not match stored manifest."
        )
    if manifest.explicit_value(SEED_SLOT) != intent.seed:
        raise ValueError("Stored intent seed does not match stored manifest.")


def _run_to_mapping(run: WorkbenchRunProvenance) -> dict[str, object]:
    return {
        "evidence_ids": list(run.evidence_ids),
        "evidence_references": list(run.evidence_references),
        "manifest_digest": run.manifest_digest,
        "result_references": list(run.result_references),
        "run_id": run.run_id,
        "study_revision_id": run.study_revision_id,
    }


def _run_from_mapping(value: object, *, index: int) -> WorkbenchRunProvenance:
    if type(value) is not dict:
        raise TypeError(f"runs[{index}] must be a JSON object.")
    mapping = value
    return WorkbenchRunProvenance(
        run_id=_required_string(mapping, "run_id"),
        study_revision_id=_required_string(mapping, "study_revision_id"),
        manifest_digest=_required_string(mapping, "manifest_digest"),
        evidence_ids=tuple(
            _list_of_strings(
                _required_list(mapping, "evidence_ids"),
                f"runs[{index}].evidence_ids",
            )
        ),
        evidence_references=tuple(
            _list_of_strings(
                _required_list(mapping, "evidence_references"),
                f"runs[{index}].evidence_references",
            )
        ),
        result_references=tuple(
            _list_of_strings(
                _required_list(mapping, "result_references"),
                f"runs[{index}].result_references",
            )
        ),
    )


def _required_mapping(mapping: dict[object, object], key: str) -> dict[object, object]:
    value = mapping.get(key)
    if type(value) is not dict:
        raise TypeError(f"{key} must be a JSON object.")
    return value


def _required_list(mapping: dict[object, object], key: str) -> list[object]:
    value = mapping.get(key)
    if type(value) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    return value


def _required_string(mapping: dict[object, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _optional_string(mapping: dict[object, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{key} must be a string or null.")
    return value


def _optional_int(mapping: dict[object, object], key: str) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer or null.")
    return value


def _list_of_strings(values: list[object], name: str) -> tuple[str, ...]:
    result: list[str] = []
    for index, value in enumerate(values):
        if type(value) is not str or not value:
            raise TypeError(f"{name}[{index}] must be a non-empty string.")
        result.append(value)
    return tuple(result)


def _validate_string_tuple(values: tuple[str, ...], name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple.")
    for index, value in enumerate(values):
        _require_nonempty_string(value, f"{name}[{index}]")


def _require_nonempty_string(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        raise TypeError(f"{name} must be a non-empty string.")
    return value
