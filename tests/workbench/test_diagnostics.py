"""WB6 tests for evidence-backed Workbench diagnostics and support boundaries."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.workbench import (
    ControlledLocomotionIntent,
    EvidencePlan,
    create_b3_study_revision,
    default_reference_ecology_intent,
    fork_b3_study_revision,
)
from evo_engine.workbench.controlled_locomotion import (
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    assess_readiness,
    compile_controlled_locomotion,
    resolve_controlled_locomotion,
)
from evo_engine.workbench.diagnostics import (
    IncompatibleManifestError,
    WorkbenchDiagnostic,
)
from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_RADIUS_SLOT,
    resolve_reference_ecology,
)
from evo_engine.workbench.results import AnalysisAvailability
from evo_engine.workbench.support import (
    analysis_availability_diagnostic,
    b3_scenario_identity_diagnostic,
    reference_normalization_diagnostics,
)


def test_shared_readiness_diagnostic_has_actionable_remediation() -> None:
    readiness = assess_readiness(
        ControlledLocomotionIntent(
            max_speed=11,
            resource_geography="local_resource",
            seed=5,
        )
    )

    assert readiness.state == "blocked"
    diagnostic = next(
        item for item in readiness.diagnostics if item.slot_id == MAX_SPEED_SLOT
    )
    assert isinstance(diagnostic, WorkbenchDiagnostic)
    assert diagnostic.__class__.__module__ == "evo_engine.workbench.diagnostics"
    assert diagnostic.code == "unsupported-value"
    assert diagnostic.severity == "error"
    assert diagnostic.remediation is not None
    assert "characterized WB1 range" in diagnostic.remediation


def test_exact_reproduction_incompatibility_is_structured_without_migration() -> None:
    manifest = resolve_controlled_locomotion(
        ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="separated_corridor",
            seed=17,
        )
    )
    incompatible = attrs.evolve(manifest, engine_version="historical-incompatible")

    with pytest.raises(IncompatibleManifestError) as captured:
        compile_controlled_locomotion(incompatible)

    diagnostic = captured.value.diagnostic
    assert diagnostic.code == "exact-reproduction-unavailable"
    assert diagnostic.severity == "error"
    assert diagnostic.remediation is not None
    assert "Do not treat re-resolution" in diagnostic.remediation


def test_reference_normalization_diagnostics_report_only_present_stale_values() -> None:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        exploration_movement="moore",
        gaussian_standard_deviation=3,
        resource_geography="uniform",
        patch_1_radius=2,
        mutation_enabled=False,
        mutation_probability_ppm=40,
        mutation_max_change=2,
    )

    diagnostics = reference_normalization_diagnostics(intent)

    assert {item.slot_id for item in diagnostics} == {
        GAUSSIAN_STDDEV_SLOT,
        PATCH_1_RADIUS_SLOT,
        MUTATION_PROBABILITY_SLOT,
        MUTATION_MAX_CHANGE_SLOT,
    }
    assert all(item.code == "irrelevant-parameter" for item in diagnostics)
    assert all(item.severity == "warning" for item in diagnostics)
    assert all(item.remediation for item in diagnostics)

    manifest = resolve_reference_ecology(intent)
    active_ids = {slot_id for slot_id, _ in manifest.explicit_values}
    assert GAUSSIAN_STDDEV_SLOT not in active_ids
    assert PATCH_1_RADIUS_SLOT not in active_ids
    assert MUTATION_PROBABILITY_SLOT not in active_ids
    assert MUTATION_MAX_CHANGE_SLOT not in active_ids


def test_b3_identity_loss_is_warning_not_claim_inference() -> None:
    canonical = create_b3_study_revision(revision_id="b3-canonical")
    assert b3_scenario_identity_diagnostic(canonical) is None

    fork = fork_b3_study_revision(canonical, revision_id="b3-radius-two")
    diagnostic = b3_scenario_identity_diagnostic(fork)

    assert diagnostic is not None
    assert diagnostic.code == "scenario-identity-lost"
    assert diagnostic.severity == "warning"
    assert diagnostic.remediation is not None
    assert "B3-derived custom Study" in diagnostic.remediation


def test_missing_evidence_analysis_diagnostic_requires_rerun_not_reconstruction() -> (
    None
):
    availability = AnalysisAvailability(
        analysis_id="reference-ecology.spatial-replay",
        source_contract="SpatialObservation",
        required_evidence_ids=("reference-ecology.spatial-replay",),
        missing_evidence_ids=("reference-ecology.spatial-replay",),
    )

    diagnostic = analysis_availability_diagnostic(availability)

    assert diagnostic is not None
    assert diagnostic.code == "missing-required-evidence"
    assert diagnostic.severity == "error"
    assert diagnostic.remediation is not None
    assert "Rerun the same scientific Study revision" in diagnostic.remediation
    assert "Do not reconstruct" in diagnostic.remediation


def test_available_analysis_has_no_diagnostic() -> None:
    availability = AnalysisAvailability(
        analysis_id="controlled-locomotion.population-trajectory",
        source_contract="PopulationObservation",
        required_evidence_ids=(POPULATION_EVIDENCE_ID,),
    )

    assert analysis_availability_diagnostic(availability) is None


def test_non_evidence_unavailability_remains_bounded_to_analysis_context() -> None:
    availability = AnalysisAvailability(
        analysis_id="b3.confirmed-cinematic-scientific-handoff",
        source_contract="existing B3 scientific handoff",
        required_evidence_ids=(),
        unavailable_reason="Validated B3 scenario identity is required.",
    )

    diagnostic = analysis_availability_diagnostic(availability)

    assert diagnostic is not None
    assert diagnostic.code == "analysis-unavailable"
    assert diagnostic.context == availability.analysis_id
    assert "Validated B3 scenario identity" in diagnostic.message


def test_diagnostic_rejects_empty_or_nonblocking_readiness_payloads() -> None:
    with pytest.raises(TypeError, match="code"):
        WorkbenchDiagnostic(code="", message="message")
    with pytest.raises(ValueError, match="severity"):
        WorkbenchDiagnostic(
            code="x",
            message="message",
            severity="info",  # type: ignore[arg-type]
        )


def test_exact_reproduction_diagnostic_preserves_original_error_message() -> None:
    error = IncompatibleManifestError("Pinned compiler version is unavailable.")

    assert str(error) == "Pinned compiler version is unavailable."
    assert error.diagnostic.message == str(error)
    assert error.diagnostic.context is None


def test_readiness_evidence_plan_remains_separate_from_simulation_intent() -> None:
    readiness = assess_readiness(
        ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=5,
        ),
        EvidencePlan(requested=()),
    )

    assert readiness.state == "draft"
    assert readiness.diagnostics[0].code == "missing-evidence"
    assert readiness.diagnostics[0].remediation is not None
