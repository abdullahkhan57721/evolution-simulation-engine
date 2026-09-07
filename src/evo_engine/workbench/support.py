"""Concrete WB6 diagnostics for real Workbench support-envelope friction."""

from __future__ import annotations

from evo_engine.workbench.b3_curated import (
    B3_VALIDATED_SCENARIO_ID,
    B3StudyRevision,
)
from evo_engine.workbench.diagnostics import WorkbenchDiagnostic
from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_RADIUS_SLOT,
    PATCH_1_X_SLOT,
    PATCH_1_Y_SLOT,
    PATCH_2_RADIUS_SLOT,
    PATCH_2_X_SLOT,
    PATCH_2_Y_SLOT,
    REFERENCE_RECIPE_ID,
    ReferenceEcologyIntent,
)
from evo_engine.workbench.results import AnalysisAvailability


def reference_normalization_diagnostics(
    intent: ReferenceEcologyIntent,
) -> tuple[WorkbenchDiagnostic, ...]:
    """Report user-supplied values the WB4 recipe will normalize away.

    Applicability and normalization remain owned by the concrete reference recipe.
    This function only makes the already-settled behavior legible before resolution.
    """
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")

    diagnostics: list[WorkbenchDiagnostic] = []
    if (
        intent.exploration_movement != "gaussian"
        and intent.gaussian_standard_deviation is not None
    ):
        diagnostics.append(
            _irrelevant_parameter(
                GAUSSIAN_STDDEV_SLOT,
                "Gaussian standard deviation is irrelevant unless exploration "
                "movement is gaussian.",
                "Clear the value or select gaussian exploration. The inactive value "
                "will not be persisted as scientific intent.",
            )
        )

    if intent.resource_geography != "two_patches":
        diagnostics.extend(
            _present_irrelevant_patch_values(intent)
        )

    if intent.mutation_enabled is not True:
        for slot_id, value, label in (
            (
                MUTATION_PROBABILITY_SLOT,
                intent.mutation_probability_ppm,
                "Mutation probability",
            ),
            (
                MUTATION_MAX_CHANGE_SLOT,
                intent.mutation_max_change,
                "Mutation maximum change",
            ),
        ):
            if value is not None:
                diagnostics.append(
                    _irrelevant_parameter(
                        slot_id,
                        f"{label} is irrelevant while mutation is disabled.",
                        "Clear the value or enable mutation. The inactive value will "
                        "not be persisted as scientific intent.",
                    )
                )
    return tuple(diagnostics)


def b3_scenario_identity_diagnostic(
    revision: B3StudyRevision,
) -> WorkbenchDiagnostic | None:
    """Explain when a B3-derived revision no longer has canonical B3 identity."""
    if not isinstance(revision, B3StudyRevision):
        raise TypeError("revision must be a B3StudyRevision.")
    if revision.scenario_identity == B3_VALIDATED_SCENARIO_ID:
        return None
    return WorkbenchDiagnostic(
        code="scenario-identity-lost",
        severity="warning",
        context=revision.scenario_origin,
        message=(
            "This Study retains B3 scientific origin but is not the exact validated "
            "canonical B3 scenario."
        ),
        remediation=(
            "Treat it as a B3-derived custom Study. Use the canonical validated B3 "
            "revision when relying on the original representative story or bounded "
            "headline-claim cinematic handoff."
        ),
    )


def analysis_availability_diagnostic(
    availability: AnalysisAvailability,
) -> WorkbenchDiagnostic | None:
    """Translate one concrete WB5 analysis availability result into remediation."""
    if not isinstance(availability, AnalysisAvailability):
        raise TypeError("availability must be an AnalysisAvailability.")
    if availability.available:
        return None
    if availability.missing_evidence_ids:
        missing = ", ".join(availability.missing_evidence_ids)
        return WorkbenchDiagnostic(
            code="missing-required-evidence",
            context=availability.analysis_id,
            message=(
                f"{availability.analysis_id} is unavailable because required evidence "
                f"was not recorded: {missing}."
            ),
            remediation=(
                "Rerun the same scientific Study revision with an EvidencePlan that "
                f"requests: {missing}. Do not reconstruct the missing evidence from "
                "weaker artifacts."
            ),
        )
    return WorkbenchDiagnostic(
        code="analysis-unavailable",
        context=availability.analysis_id,
        message=(
            availability.unavailable_reason
            or f"{availability.analysis_id} is unavailable for this Study."
        ),
        remediation=(
            "Use an eligible Study/revision for this analysis and preserve the current "
            "Study's scientific identity rather than inferring unsupported meaning."
        ),
    )


def _present_irrelevant_patch_values(
    intent: ReferenceEcologyIntent,
) -> tuple[WorkbenchDiagnostic, ...]:
    values = (
        (PATCH_1_X_SLOT, intent.patch_1_center_x, "Patch 1 center x"),
        (PATCH_1_Y_SLOT, intent.patch_1_center_y, "Patch 1 center y"),
        (PATCH_1_RADIUS_SLOT, intent.patch_1_radius, "Patch 1 radius"),
        (PATCH_2_X_SLOT, intent.patch_2_center_x, "Patch 2 center x"),
        (PATCH_2_Y_SLOT, intent.patch_2_center_y, "Patch 2 center y"),
        (PATCH_2_RADIUS_SLOT, intent.patch_2_radius, "Patch 2 radius"),
    )
    return tuple(
        _irrelevant_parameter(
            slot_id,
            f"{label} is irrelevant unless resource geography is two_patches.",
            "Clear the value or select two_patches geography. The inactive value "
            "will not be persisted as scientific intent.",
        )
        for slot_id, value, label in values
        if value is not None
    )


def _irrelevant_parameter(
    slot_id: str,
    message: str,
    remediation: str,
) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(
        code="irrelevant-parameter",
        severity="warning",
        slot_id=slot_id,
        context=REFERENCE_RECIPE_ID,
        message=message,
        remediation=remediation,
    )


__all__ = [
    "analysis_availability_diagnostic",
    "b3_scenario_identity_diagnostic",
    "reference_normalization_diagnostics",
]
