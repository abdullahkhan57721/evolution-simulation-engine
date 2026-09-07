"""Persistence and run-level contracts for WB4 reference studies."""

from __future__ import annotations

import attrs

from evo_engine.workbench.reference_ecology import (
    EVENT_EVIDENCE_ID,
    GENETIC_EVIDENCE_ID,
    PEDIGREE_EVIDENCE_ID,
    POPULATION_EVIDENCE_ID,
    SPATIAL_EVIDENCE_ID,
    ReferenceEcologyIntent,
    ReferenceEvidencePlan,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_study import (
    ReferenceStudyRevision,
    create_reference_study_revision,
    diff_reference_study_revisions,
    fork_reference_study_revision,
    run_reference_study_revision,
)


def _intent() -> ReferenceEcologyIntent:
    return attrs.evolve(
        default_reference_ecology_intent(),
        horizon=2,
        seed=5,
        max_speed=2,
        sensory_range=5,
        sensory_accuracy=90,
        exploration_movement="moore",
        gaussian_standard_deviation=9,
        resource_geography="uniform",
        patch_1_center_x=2,
        patch_1_center_y=5,
        patch_1_radius=1,
        patch_2_center_x=9,
        patch_2_center_y=5,
        patch_2_radius=1,
        mutation_enabled=False,
        mutation_probability_ppm=99_999,
        mutation_max_change=4,
    )


def test_reference_study_round_trip_removes_inactive_stale_intent() -> None:
    revision = create_reference_study_revision(
        revision_id="reference-1",
        intent=_intent(),
    )
    loaded = ReferenceStudyRevision.from_json(revision.to_json())
    assert loaded == revision
    assert loaded.manifest.to_json() == revision.manifest.to_json()
    assert loaded.intent.gaussian_standard_deviation is None
    assert loaded.intent.patch_1_center_x is None
    assert loaded.intent.mutation_probability_ppm is None
    assert loaded.intent.mutation_max_change is None


def test_reference_fork_is_immutable_and_semantic() -> None:
    parent = create_reference_study_revision(revision_id="parent", intent=_intent())
    child = fork_reference_study_revision(
        parent,
        revision_id="child",
        intent=attrs.evolve(_intent(), max_speed=3),
    )
    assert parent.parent_revision_id is None
    assert parent.runs == ()
    assert child.parent_revision_id == parent.revision_id
    assert [
        change.slot_id
        for change in diff_reference_study_revisions(parent, child).explicit_changes
    ] == ["reference-ecology.founder-max-speed"]


def test_reference_run_ties_evidence_and_science_to_exact_manifest() -> None:
    plan = ReferenceEvidencePlan(
        requested=(
            POPULATION_EVIDENCE_ID,
            EVENT_EVIDENCE_ID,
            PEDIGREE_EVIDENCE_ID,
            GENETIC_EVIDENCE_ID,
            SPATIAL_EVIDENCE_ID,
        )
    )
    revision = create_reference_study_revision(
        revision_id="run-study",
        intent=_intent(),
        evidence_plan=plan,
    )
    result = run_reference_study_revision(revision, run_id="run-1")
    assert result.provenance.study_revision_id == revision.revision_id
    assert result.provenance.manifest_digest == revision.manifest.digest
    assert result.provenance.evidence_ids == plan.requested
    assert result.scientific_provenance.seed == 5
    assert result.scientific_provenance.horizon_step_index == 2
    assert result.scientific_provenance.observation_include_step_zero
    assert result.population_observations
    assert result.applied_events
    assert result.pedigree_records
    assert result.genetic_observations
    assert result.spatial_observations


def test_completed_run_can_be_recorded_without_mutating_original_revision() -> None:
    revision = create_reference_study_revision(
        revision_id="record-run",
        intent=_intent(),
    )
    result = run_reference_study_revision(revision, run_id="run-2")
    updated = revision.with_run(result.provenance)
    assert revision.runs == ()
    assert updated.runs == (result.provenance,)
    assert ReferenceStudyRevision.from_json(updated.to_json()) == updated
