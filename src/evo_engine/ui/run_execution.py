"""WU3 execution routing through existing authoritative Workbench run contracts."""

from __future__ import annotations

from typing import TypeAlias, TypeGuard

from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
    ReferenceRunResult,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchRunResult,
    run_b3_study_revision,
    run_environment_selection_comparison,
    run_max_speed_sweep,
    run_reference_study_revision,
    run_study_revision,
)

AuthoritativeRunResult: TypeAlias = (
    WorkbenchRunResult
    | ReferenceRunResult
    | B3CuratedRunResult
    | MaxSpeedSweepResult
    | EnvironmentSelectionComparisonResult
)
_RESULT_TYPES = (
    WorkbenchRunResult,
    ReferenceRunResult,
    B3CuratedRunResult,
    MaxSpeedSweepResult,
    EnvironmentSelectionComparisonResult,
)


def execute_artifact(
    artifact: ConcreteWorkbenchArtifact,
) -> tuple[ConcreteWorkbenchArtifact, AuthoritativeRunResult]:
    """Execute one exact concrete artifact through its existing Workbench runner."""
    if isinstance(artifact, StudyRevision):
        result = run_study_revision(artifact)
        return artifact.with_run(result.provenance), result
    if isinstance(artifact, ReferenceStudyRevision):
        result = run_reference_study_revision(artifact)
        return artifact.with_run(result.provenance), result
    if isinstance(artifact, B3StudyRevision):
        result = run_b3_study_revision(artifact)
        return artifact.with_run(result.provenance), result
    if isinstance(artifact, MaxSpeedSweepDefinition):
        return artifact, run_max_speed_sweep(artifact)
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
        return artifact, run_environment_selection_comparison(artifact)
    raise TypeError("Unsupported Workbench artifact for execution.")


def is_authoritative_run_result(value: object) -> TypeGuard[AuthoritativeRunResult]:
    """Return whether session state holds one of the exact Workbench result types."""
    return isinstance(value, _RESULT_TYPES)


def result_run_id(result: AuthoritativeRunResult) -> str | None:
    """Return a run ID only where the existing result contract owns one."""
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult, B3CuratedRunResult)):
        return result.provenance.run_id
    return None


def result_revision_id(result: AuthoritativeRunResult) -> str | None:
    """Return exact saved revision identity where the existing result owns it."""
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult, B3CuratedRunResult)):
        return result.provenance.study_revision_id
    return None


def result_evidence_ids(result: AuthoritativeRunResult) -> tuple[str, ...]:
    """Return the exact evidence plan associated with one authoritative result."""
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult, B3CuratedRunResult)):
        return result.provenance.evidence_ids
    return result.definition.evidence_plan.requested


def result_simulation_count(result: AuthoritativeRunResult) -> int:
    """Return the number of concrete simulations represented by the result."""
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult)):
        return 1
    if isinstance(result, B3CuratedRunResult):
        return (
            len(result.confirmation) * 2
            + len(result.radius_sensitivity)
            + len(result.counterbalanced) * 2
        )
    return len(result.treatments)


__all__ = [
    "AuthoritativeRunResult",
    "execute_artifact",
    "is_authoritative_run_result",
    "result_evidence_ids",
    "result_revision_id",
    "result_run_id",
    "result_simulation_count",
]
