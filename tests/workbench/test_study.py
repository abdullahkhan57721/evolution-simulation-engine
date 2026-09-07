"""Tests for WB1 saved studies, lineage, execution, and provenance."""

from __future__ import annotations

import json

import attrs
import pytest

import evo_engine.workbench.study as study_module
from evo_engine.workbench import (
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
    ControlledLocomotionIntent,
    EvidencePlan,
    StudyRevision,
    WorkbenchRunProvenance,
    create_study_revision,
    diff_study_revisions,
    fork_study_revision,
    run_study_revision,
)


def _revision(
    *,
    revision_id: str = "study-r1",
    max_speed: int = 3,
    geography: str = "local_resource",
    seed: int = 23,
    evidence_plan: EvidencePlan | None = None,
) -> StudyRevision:
    return create_study_revision(
        revision_id=revision_id,
        intent=ControlledLocomotionIntent(
            max_speed=max_speed,
            resource_geography=geography,
            seed=seed,
        ),
        evidence_plan=evidence_plan,
    )


def test_saved_revision_round_trips_exact_intent_manifest_and_evidence_plan() -> None:
    revision = _revision()

    encoded = revision.to_json()
    loaded = StudyRevision.from_json(encoded)

    assert loaded == revision
    assert loaded.intent == revision.intent
    assert loaded.manifest == revision.manifest
    assert loaded.manifest.to_json() == revision.manifest.to_json()
    assert loaded.manifest.digest == revision.manifest.digest
    assert loaded.evidence_plan == revision.evidence_plan
    assert loaded.to_json() == encoded


def test_load_uses_stored_manifest_without_reresolving_authoring_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = _revision()
    encoded = revision.to_json()

    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("load must not re-resolve persisted intent")

    monkeypatch.setattr(study_module, "resolve_controlled_locomotion", fail_if_called)

    loaded = StudyRevision.from_json(encoded)
    assert loaded.manifest == revision.manifest


def test_same_saved_revision_reproduces_same_evidence_and_scientific_result() -> None:
    revision = _revision()
    loaded = StudyRevision.from_json(revision.to_json())

    first = run_study_revision(revision, run_id="run-a")
    second = run_study_revision(loaded, run_id="run-b")

    assert first.population_observations == second.population_observations
    assert first.applied_events == second.applied_events
    assert first.scientific_provenance == second.scientific_provenance
    assert first.locomotion == second.locomotion
    assert first.provenance.manifest_digest == revision.manifest.digest
    assert second.provenance.manifest_digest == loaded.manifest.digest


def test_run_provenance_ties_evidence_and_e1_measurement_to_exact_manifest() -> None:
    revision = _revision()

    result = run_study_revision(revision, run_id="run-1")

    assert result.provenance.run_id == "run-1"
    assert result.provenance.study_revision_id == revision.revision_id
    assert result.provenance.manifest_digest == revision.manifest.digest
    assert result.provenance.evidence_ids == revision.evidence_plan.requested
    assert result.provenance.evidence_references == (
        "run-1:population-observations",
        "run-1:committed-events",
    )
    assert result.provenance.result_references == ("run-1:e1-locomotion-measurements",)
    assert result.population_observations
    assert result.applied_events
    assert result.locomotion is not None
    assert result.locomotion.provenance == result.scientific_provenance


def test_run_uses_requested_evidence_plan_without_inventing_other_recorders() -> None:
    population_revision = _revision(
        revision_id="population-only",
        evidence_plan=EvidencePlan(requested=(POPULATION_EVIDENCE_ID,)),
    )
    event_revision = _revision(
        revision_id="events-only",
        evidence_plan=EvidencePlan(requested=(EVENT_EVIDENCE_ID,)),
    )

    population_result = run_study_revision(population_revision, run_id="population-run")
    event_result = run_study_revision(event_revision, run_id="event-run")

    assert population_result.population_observations
    assert population_result.applied_events == ()
    assert population_result.locomotion is None
    assert population_result.provenance.evidence_references == (
        "population-run:population-observations",
    )
    assert population_result.provenance.result_references == ()

    assert event_result.population_observations == ()
    assert event_result.applied_events
    assert event_result.locomotion is not None
    assert event_result.provenance.evidence_references == (
        "event-run:committed-events",
    )


def test_recording_run_metadata_returns_new_revision_without_mutating_saved_science() -> (
    None
):
    revision = _revision()
    result = run_study_revision(revision, run_id="run-1")

    recorded = revision.with_run(result.provenance)

    assert revision.runs == ()
    assert recorded.runs == (result.provenance,)
    assert recorded.revision_id == revision.revision_id
    assert recorded.intent == revision.intent
    assert recorded.manifest == revision.manifest
    assert StudyRevision.from_json(recorded.to_json()) == recorded
    with pytest.raises(ValueError, match="already recorded"):
        recorded.with_run(result.provenance)


def test_fork_creates_new_revision_and_semantic_diff_without_mutating_parent() -> None:
    parent = _revision(max_speed=3)

    child = fork_study_revision(parent, revision_id="study-r2", max_speed=4)
    difference = diff_study_revisions(parent, child)

    assert parent.revision_id == "study-r1"
    assert parent.parent_revision_id is None
    assert parent.intent.max_speed == 3
    assert parent.runs == ()
    assert child.revision_id == "study-r2"
    assert child.parent_revision_id == parent.revision_id
    assert child.intent.max_speed == 4
    assert child.runs == ()
    assert [
        (change.slot_id, change.before, change.after)
        for change in difference.explicit_changes
    ] == [(MAX_SPEED_SLOT, 3, 4)]
    assert any(
        change.slot_id == "controlled-locomotion.initial-focal-max-speed"
        for change in difference.derived_changes
    )


def test_geography_fork_reports_only_geography_and_its_derived_layout() -> None:
    parent = _revision(geography="local_resource")
    child = fork_study_revision(
        parent,
        revision_id="study-r2",
        resource_geography="separated_corridor",
    )

    difference = diff_study_revisions(parent, child)

    assert [change.slot_id for change in difference.explicit_changes] == [
        RESOURCE_GEOGRAPHY_SLOT
    ]
    assert [change.slot_id for change in difference.derived_changes] == [
        "controlled-locomotion.resource-deposit-layout"
    ]


def test_saved_revision_rejects_intent_manifest_mismatch() -> None:
    revision = _revision()

    with pytest.raises(ValueError, match="max_speed"):
        attrs.evolve(
            revision,
            intent=attrs.evolve(revision.intent, max_speed=4),
        )


def test_run_provenance_must_reference_exact_revision_manifest_and_evidence_plan() -> (
    None
):
    revision = _revision()
    wrong_revision = WorkbenchRunProvenance(
        run_id="run-1",
        study_revision_id="other-revision",
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )
    wrong_manifest = attrs.evolve(
        wrong_revision,
        study_revision_id=revision.revision_id,
        manifest_digest="not-the-manifest",
    )
    wrong_evidence = attrs.evolve(
        wrong_revision,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=(EVENT_EVIDENCE_ID,),
    )

    with pytest.raises(ValueError, match="different study revision"):
        revision.with_run(wrong_revision)
    with pytest.raises(ValueError, match="different manifest"):
        revision.with_run(wrong_manifest)
    with pytest.raises(ValueError, match="different evidence plan"):
        revision.with_run(wrong_evidence)
    with pytest.raises(ValueError, match="exact evidence plan"):
        attrs.evolve(revision, runs=(wrong_evidence,))


def test_study_loader_rejects_unknown_format_instead_of_migrating() -> None:
    payload = json.loads(_revision().to_json())
    payload["format_version"] = 2

    with pytest.raises(ValueError, match="format version"):
        StudyRevision.from_json(json.dumps(payload))


def test_fork_rejects_reusing_parent_revision_id() -> None:
    parent = _revision()

    with pytest.raises(ValueError, match="new revision_id"):
        fork_study_revision(parent, revision_id=parent.revision_id, max_speed=4)


def test_revision_and_provenance_are_immutable_values() -> None:
    revision = _revision()
    result = run_study_revision(revision, run_id="run-immutable")

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        revision.revision_id = "changed"  # type: ignore[misc]
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        result.provenance.run_id = "changed"  # type: ignore[misc]
