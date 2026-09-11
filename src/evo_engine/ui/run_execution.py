"""Streamlit compatibility facade for frontend-neutral Workbench execution."""

from evo_engine.workbench.execution import (
    AuthoritativeRunResult,
    ExecutableWorkbenchArtifact,
    RevisionOwnedArtifact,
    RevisionOwnedRunResult,
    execute_artifact,
    is_authoritative_run_result,
    result_evidence_ids,
    result_revision_id,
    result_run_id,
    result_simulation_count,
)

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
