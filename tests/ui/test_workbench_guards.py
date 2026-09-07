"""Focused guard coverage for retained Workbench-to-V2 presentation adapters."""

from __future__ import annotations

import pytest

from evo_engine.ui.workbench import (
    WorkbenchPresentationUnavailableError,
    WorkbenchWorldPresentation,
    build_b3_workbench_world_presentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.workbench import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3CuratedRunResult,
    WorkbenchDiagnostic,
    WorkbenchRunProvenance,
    create_b3_study_revision,
    create_reference_study_revision,
    default_reference_ecology_intent,
    run_reference_study_revision,
)


def _provenance(*, revision_id: str, manifest_digest: str) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=f"{revision_id}-run",
        study_revision_id=revision_id,
        manifest_digest=manifest_digest,
        evidence_ids=B3_REQUIRED_EVIDENCE_IDS,
        evidence_references=(f"{revision_id}-run:evidence",),
        result_references=(f"{revision_id}-run:result",),
    )


def _empty_b3_result():  # type: ignore[no-untyped-def]
    revision = create_b3_study_revision(revision_id="b3-guard")
    result = B3CuratedRunResult(
        provenance=_provenance(
            revision_id=revision.revision_id,
            manifest_digest=revision.manifest.digest,
        ),
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    return revision, result


def test_presentation_error_requires_structured_diagnostic() -> None:
    with pytest.raises(TypeError, match="diagnostic"):
        WorkbenchPresentationUnavailableError("not-a-diagnostic")  # type: ignore[arg-type]

    diagnostic = WorkbenchDiagnostic(
        code="test-unavailable",
        message="Presentation unavailable.",
    )
    error = WorkbenchPresentationUnavailableError(diagnostic)

    assert error.diagnostic is diagnostic
    assert str(error) == "Presentation unavailable."


def test_world_presentation_rejects_invalid_transient_identity_values() -> None:
    revision, result = _empty_b3_result()
    provenance = result.provenance

    with pytest.raises(TypeError, match="seed"):
        WorkbenchWorldPresentation(
            provenance=provenance,
            seed=True,  # type: ignore[arg-type]
            frame=None,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="arm"):
        WorkbenchWorldPresentation(
            provenance=provenance,
            seed=1,
            arm="unknown",
            frame=None,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="environment"):
        WorkbenchWorldPresentation(
            provenance=provenance,
            seed=1,
            environment=" ",
            frame=None,  # type: ignore[arg-type]
        )

    value = WorkbenchWorldPresentation(
        provenance=provenance,
        seed=1,
        frame=None,  # type: ignore[arg-type]
    )
    assert value.arm is None
    assert value.environment is None


def test_b3_adapter_rejects_invalid_selection_before_rendering() -> None:
    revision, result = _empty_b3_result()

    with pytest.raises(TypeError, match="seed"):
        build_b3_workbench_world_presentation(
            revision,
            result,
            seed=True,  # type: ignore[arg-type]
            arm="control",
            step_index=0,
        )
    with pytest.raises(ValueError, match="arm"):
        build_b3_workbench_world_presentation(
            revision,
            result,
            seed=5,
            arm="invalid",  # type: ignore[arg-type]
            step_index=0,
        )
    with pytest.raises(KeyError, match="No B3 confirmation replicate"):
        build_b3_workbench_world_presentation(
            revision,
            result,
            seed=5,
            arm="control",
            step_index=0,
        )


def test_reference_adapter_builds_from_recorded_spatial_evidence() -> None:
    revision = create_reference_study_revision(
        revision_id="reference-v2-guard",
        intent=default_reference_ecology_intent(),
    )
    result = run_reference_study_revision(
        revision,
        run_id="reference-v2-guard-run",
    )

    presentation = build_reference_workbench_world_presentation(
        revision,
        result,
        step_index=0,
        show_resources=False,
        show_carcasses=False,
        show_trails=False,
        trail_length=1,
    )

    assert presentation.provenance is result.provenance
    assert presentation.seed == result.scientific_provenance.seed
    assert presentation.arm is None
    assert presentation.environment is None
    assert presentation.frame.step_index == 0
