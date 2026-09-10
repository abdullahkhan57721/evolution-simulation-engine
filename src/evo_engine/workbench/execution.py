"""Frontend-neutral execution dispatch for supported Workbench artifacts.

This module remains deliberately concrete.  It routes only the five currently
supported Workbench artifact families to their existing authoritative synchronous
runners and preserves each family's existing result ownership semantics.  It is not
a generic job system, execution registry, or simulation orchestration layer.
"""

from __future__ import annotations

from typing import TypeAlias, TypeGuard, overload

from evo_engine.workbench.b3_curated import (
    B3CuratedRunResult,
    B3StudyRevision,
    run_b3_study_revision,
)
from evo_engine.workbench.experiments import (
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
    run_environment_selection_comparison,
    run_max_speed_sweep,
)
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    ReferenceStudyRevision,
    run_reference_study_revision,
)
from evo_engine.workbench.study import (
    StudyRevision,
    WorkbenchRunResult,
    run_study_revision,
)

ExecutableWorkbenchArtifact: TypeAlias = (
    StudyRevision
    | MaxSpeedSweepDefinition
    | EnvironmentSelectionComparisonDefinition
    | B3StudyRevision
    | ReferenceStudyRevision
)
AuthoritativeRunResult: TypeAlias = (
    WorkbenchRunResult
    | ReferenceRunResult
    | B3CuratedRunResult
    | MaxSpeedSweepResult
    | EnvironmentSelectionComparisonResult
)
RevisionOwnedArtifact: TypeAlias = (
    StudyRevision | ReferenceStudyRevision | B3StudyRevision
)
RevisionOwnedRunResult: TypeAlias = (
    WorkbenchRunResult | ReferenceRunResult | B3CuratedRunResult
)
_RESULT_TYPES = (
    WorkbenchRunResult,
    ReferenceRunResult,
    B3CuratedRunResult,
    MaxSpeedSweepResult,
    EnvironmentSelectionComparisonResult,
)


@overload
def execute_artifact(
    artifact: RevisionOwnedArtifact,
) -> tuple[RevisionOwnedArtifact, RevisionOwnedRunResult]: ...


@overload
def execute_artifact(
    artifact: MaxSpeedSweepDefinition,
) -> tuple[MaxSpeedSweepDefinition, MaxSpeedSweepResult]: ...


@overload
def execute_artifact(
    artifact: EnvironmentSelectionComparisonDefinition,
) -> tuple[
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
]: ...


@overload
def execute_artifact(
    artifact: ExecutableWorkbenchArtifact,
) -> tuple[ExecutableWorkbenchArtifact, AuthoritativeRunResult]: ...


def execute_artifact(
    artifact: ExecutableWorkbenchArtifact,
) -> tuple[ExecutableWorkbenchArtifact, AuthoritativeRunResult]:
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
    """Return whether a value is one of the exact supported Workbench result types."""
    return isinstance(value, _RESULT_TYPES)


def result_run_id(result: AuthoritativeRunResult) -> str | None:
    """Return a run ID only where the existing result contract owns one."""
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult, B3CuratedRunResult)):
        return result.provenance.run_id
    return None


def result_revision_id(result: AuthoritativeRunResult) -> str | None:
    """Return saved revision identity only where the result contract owns it."""
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
    "ExecutableWorkbenchArtifact",
    "RevisionOwnedArtifact",
    "RevisionOwnedRunResult",
    "execute_artifact",
    "is_authoritative_run_result",
    "result_evidence_ids",
    "result_revision_id",
    "result_run_id",
    "result_simulation_count",
]
