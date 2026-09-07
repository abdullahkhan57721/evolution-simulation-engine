"""Persistence and run-level contracts for WB4 reference studies."""

from __future__ import annotations

import attrs

from evo_engine.workbench.reference_ecology import ReferenceEcologyIntent
from evo_engine.workbench.reference_study import (
    ReferenceStudyRevision,
    create_reference_study_revision,
    diff_reference_study_revisions,
    fork_reference_study_revision,
    run_reference_study_revision,
)


def _intent() -> ReferenceEcologyIntent:
    return ReferenceEcologyIntent(
        width=12,
        height=12,
        founder_population=20,
        founder_energy=30,
        horizon=3,
        seed=5,
        max_speed=2,
        sensory_range=5,
        sensory_accuracy=90,
        exploration_movement="moore",
        gaussian_standard_deviation=9,
        resource_geography="uniform",
        resource_generation_amount=6,
        resource_deposits_per_step=8,
        patch_1_center_x=2,
        patch_1_center_y=5,
        patch_1_radius=1,
        patch_2_center_x=9,
        patch_2_center_y=5,
        patch_2_radius=1,
        mutation_enabled=False,
        mutation_probability_ppm=99_999,
        mutation_max_change=4,
        recombination_probability_ppm=500_000,
    )


def test_reference_study_round_trip_preserves_exact_manifest() -> None:
    revision = create_reference_study_revision(
        revision_id="reference-1",
        intent=_intent(),
    )
    loaded = ReferenceStudyRevision.from_json(revision.to_json())
    assert loaded == revision
    assert loaded.manifest.to_json() == revision.manifest.to_json()


def test_reference_fork_is_immutable_and_semantic() -> None:
    parent = create_reference_study_revision(revision_id="parent", intent=_intent())
    child = fork_reference_study_revision(
        parent,
        revision_id="child",
        intent=attrs.evolve(_intent(), max_speed=3),
    )
    assert parent.parent_revision_id is None
    assert child.parent_revision_id == parent.revision_id
    assert [change.slot_id for change in diff_reference_study_revisions(parent, child).explicit_changes] == [
        "reference-ecology.founder-max-speed"
    ]


def test_reference_run_ties_evidence_to_exact_manifest() -> None:
    revision = create_reference_study_revision(revision_id="run-study", intent=_intent())
    result = run_reference_study_revision(revision, run_id="run-1")
    assert result.provenance.study_revision_id == revision.revision_id
    assert result.provenance.manifest_digest == revision.manifest.digest
    assert result.population_observations
    assert result.applied_events
