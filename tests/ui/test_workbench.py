"""Tests for V2 world presentation from exact Workbench results."""

from __future__ import annotations

import pytest

from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    run_b3_flagship,
    summarize_b3_run,
)
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.presets.reference_ecology.b3_flagship import (
    build_b3_flagship_specification,
)
from evo_engine.ui.workbench import (
    WorkbenchPresentationUnavailableError,
    build_b3_workbench_world_presentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.workbench import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3CuratedRunResult,
    B3MatchedRunArtifacts,
    B3StudyRevision,
    ReferenceEvidencePlan,
    ReferenceRunResult,
    WorkbenchRunProvenance,
    create_b3_study_revision,
    create_reference_study_revision,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID as REFERENCE_POPULATION_EVIDENCE_ID,
)

_B3_TEST_SEED = 5


@pytest.fixture(scope="module")
def representative_b3_result() -> tuple[B3StudyRevision, B3CuratedRunResult]:
    """Build one real matched B3 representative pair for V2 adapter tests."""
    revision = create_b3_study_revision(revision_id="b3-v2")
    control_evidence = run_b3_flagship(
        build_b3_flagship_specification(
            seed=_B3_TEST_SEED,
            environment="uniform",
        )
    )
    treatment_evidence = run_b3_flagship(
        build_b3_flagship_specification(
            seed=_B3_TEST_SEED,
            environment="compact_patch",
        )
    )
    control = summarize_b3_run(control_evidence)
    treatment = summarize_b3_run(treatment_evidence)
    pair = B3MatchedRunArtifacts(
        control_evidence=control_evidence,
        treatment_evidence=treatment_evidence,
        summary=B3MatchedPairSummary(
            seed=_B3_TEST_SEED,
            founder_assignment="standard",
            control=control,
            treatment=treatment,
        ),
    )
    provenance = WorkbenchRunProvenance(
        run_id="b3-v2-run",
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=B3_REQUIRED_EVIDENCE_IDS,
        evidence_references=("b3-v2-run:evidence",),
        result_references=("b3-v2-run:result",),
    )
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(pair,),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    return revision, result


def test_b3_matched_world_frames_preserve_same_scientific_encoding(
    representative_b3_result: tuple[B3StudyRevision, B3CuratedRunResult],
) -> None:
    revision, result = representative_b3_result
    before_manifest = revision.manifest.to_json()

    control = build_b3_workbench_world_presentation(
        revision,
        result,
        seed=_B3_TEST_SEED,
        arm="control",
        step_index=0,
        show_resources=False,
        show_trails=False,
    )
    treatment = build_b3_workbench_world_presentation(
        revision,
        result,
        seed=_B3_TEST_SEED,
        arm="treatment",
        step_index=0,
        show_resources=True,
        show_trails=True,
    )

    assert control.provenance is result.provenance
    assert treatment.provenance is result.provenance
    assert control.seed == treatment.seed == _B3_TEST_SEED
    assert control.arm == "control"
    assert treatment.arm == "treatment"
    assert control.environment == "uniform"
    assert treatment.environment == "compact_patch"
    assert control.frame.focal_encoding == treatment.frame.focal_encoding
    assert control.frame.focal_encoding is not None
    assert control.frame.focal_encoding.lower_bound == 1
    assert control.frame.focal_encoding.upper_bound == 4
    assert revision.manifest.to_json() == before_manifest


def test_reference_world_replay_is_unavailable_without_spatial_evidence() -> None:
    plan = ReferenceEvidencePlan(requested=(REFERENCE_POPULATION_EVIDENCE_ID,))
    revision = create_reference_study_revision(
        revision_id="reference-no-spatial",
        intent=default_reference_ecology_intent(),
        evidence_plan=plan,
    )
    result = ReferenceRunResult(
        provenance=WorkbenchRunProvenance(
            run_id="reference-no-spatial-run",
            study_revision_id=revision.revision_id,
            manifest_digest=revision.manifest.digest,
            evidence_ids=plan.requested,
            evidence_references=("reference-no-spatial-run:population",),
            result_references=(),
        ),
        scientific_provenance=_scientific_provenance(),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )

    with pytest.raises(
        WorkbenchPresentationUnavailableError,
        match="spatial.*Rerun",
    ):
        build_reference_workbench_world_presentation(
            revision,
            result,
            step_index=0,
        )


def _scientific_provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="reference-test",
        scenario_id="reference-test",
        treatment_id="reference-test",
        treatment_specification_json="{}",
        seed=42,
        horizon_step_index=1,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
    )
