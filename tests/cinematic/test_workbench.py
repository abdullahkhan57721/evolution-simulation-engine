"""Tests for the downstream Workbench-to-B3-cinematic adapter."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.cinematic.b3_director import B3_REPRESENTATIVE_SEED
from evo_engine.cinematic.workbench import prepare_b3_workbench_cinematic
from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunSummary,
    run_b3_flagship,
    summarize_b3_run,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_PRIMARY_STEP,
    build_b3_flagship_specification,
)
from evo_engine.workbench import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3CuratedRunResult,
    B3MatchedRunArtifacts,
    B3SingleRunArtifacts,
    B3StudyRevision,
    WorkbenchRunProvenance,
    create_b3_study_revision,
    fork_b3_study_revision,
)


@pytest.fixture(scope="module")
def canonical_b3_workbench_result() -> tuple[B3StudyRevision, B3CuratedRunResult]:
    """Build enough real representative evidence for the existing B3 director."""
    revision = create_b3_study_revision(revision_id="b3-cinematic")
    control_evidence = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="uniform",
        )
    )
    treatment_evidence = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="compact_patch",
        )
    )
    control = summarize_b3_run(control_evidence)
    treatment = summarize_b3_run(treatment_evidence)

    confirmation = tuple(
        B3MatchedRunArtifacts(
            control_evidence=control_evidence,
            treatment_evidence=treatment_evidence,
            summary=B3MatchedPairSummary(
                seed=seed,
                founder_assignment="standard",
                control=_summary_with_primary(
                    control,
                    seed=seed,
                    value=0.30 + index * 0.01,
                ),
                treatment=_summary_with_primary(
                    treatment,
                    seed=seed,
                    value=0.55 + index * 0.01,
                ),
            ),
        )
        for index, seed in enumerate(B3_CONFIRMATION_SEEDS)
    )
    sensitivity = tuple(
        B3SingleRunArtifacts(
            evidence=treatment_evidence,
            summary=attrs.evolve(
                _summary_with_primary(
                    treatment,
                    seed=seed,
                    value=0.45 + index * 0.01,
                ),
                environment="broad_patch",
            ),
        )
        for index, seed in enumerate(B3_CONFIRMATION_SEEDS)
    )
    result = B3CuratedRunResult(
        provenance=WorkbenchRunProvenance(
            run_id="b3-cinematic-run",
            study_revision_id=revision.revision_id,
            manifest_digest=revision.manifest.digest,
            evidence_ids=B3_REQUIRED_EVIDENCE_IDS,
            evidence_references=("b3-cinematic-run:evidence",),
            result_references=("b3-cinematic-run:results",),
        ),
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=confirmation,
        radius_sensitivity=sensitivity,
        counterbalanced=(),
    )
    return revision, result


def test_validated_b3_workbench_result_reuses_existing_director_handoff(
    canonical_b3_workbench_result: tuple[B3StudyRevision, B3CuratedRunResult],
) -> None:
    revision, result = canonical_b3_workbench_result

    plan = prepare_b3_workbench_cinematic(revision, result)

    assert plan.control.evidence is result.confirmation[0].control_evidence
    assert plan.treatment.evidence is result.confirmation[0].treatment_evidence
    assert plan.control.summary.seed == B3_REPRESENTATIVE_SEED
    assert plan.treatment.summary.seed == B3_REPRESENTATIVE_SEED
    assert (
        tuple(point.seed for point in plan.confirmation_points) == B3_CONFIRMATION_SEEDS
    )
    assert plan.is_full_flagship


def test_b3_derived_fork_does_not_inherit_validated_cinematic_claim_handoff(
    canonical_b3_workbench_result: tuple[B3StudyRevision, B3CuratedRunResult],
) -> None:
    canonical, result = canonical_b3_workbench_result
    fork = fork_b3_study_revision(
        canonical,
        revision_id="b3-radius-two",
    )
    fork_result = attrs.evolve(
        result,
        provenance=attrs.evolve(
            result.provenance,
            study_revision_id=fork.revision_id,
            manifest_digest=fork.manifest.digest,
        ),
        scenario_identity=None,
    )

    with pytest.raises(ValueError, match="does not inherit"):
        prepare_b3_workbench_cinematic(fork, fork_result)


def _summary_with_primary(
    summary: B3RunSummary,
    *,
    seed: int,
    value: float,
) -> B3RunSummary:
    trajectory = tuple(
        attrs.evolve(point, high_speed_allele_frequency=value)
        if point.step_index == B3_PRIMARY_STEP
        else point
        for point in summary.genetic_trajectory
    )
    return attrs.evolve(summary, seed=seed, genetic_trajectory=trajectory)
