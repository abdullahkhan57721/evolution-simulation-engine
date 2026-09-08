"""Bind WU4 Results to exact authoritative Workbench artifacts.

This module is intentionally small and concrete.  It delegates scientific result
association to the WB5 ``inspect_*_results`` functions and adds only the UI-owned
check that an immutable E3/E4 result still belongs to the active experiment
definition.  It does not define another result hierarchy or calculate science.
"""

from __future__ import annotations

from typing import TypeAlias

from evo_engine.ui.run_execution import AuthoritativeRunResult
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench.b3_curated import B3CuratedRunResult, B3StudyRevision
from evo_engine.workbench.experiments import (
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
)
from evo_engine.workbench.reference_study import ReferenceRunResult, ReferenceStudyRevision
from evo_engine.workbench.results import (
    B3ResultsView,
    ControlledLocomotionResultsView,
    EnvironmentSelectionResultsView,
    MaxSpeedSweepResultsView,
    ReferenceStudyResultsView,
    inspect_b3_results,
    inspect_controlled_locomotion_results,
    inspect_environment_selection_results,
    inspect_max_speed_sweep_results,
    inspect_reference_study_results,
)
from evo_engine.workbench.study import StudyRevision, WorkbenchRunResult

InspectedResultsView: TypeAlias = (
    ControlledLocomotionResultsView
    | ReferenceStudyResultsView
    | MaxSpeedSweepResultsView
    | EnvironmentSelectionResultsView
    | B3ResultsView
)


def inspect_current_results(
    artifact: ConcreteWorkbenchArtifact,
    result: AuthoritativeRunResult,
) -> InspectedResultsView:
    """Return the WB5 view for the exact active artifact/result pair.

    Revision-owned inspectors already validate revision ID, manifest digest, and
    evidence identity.  E3/E4 do not own Study revision IDs, so their immutable
    experiment definition is checked explicitly before delegating to WB5.
    """
    if isinstance(artifact, StudyRevision) and isinstance(result, WorkbenchRunResult):
        return inspect_controlled_locomotion_results(artifact, result)
    if isinstance(artifact, ReferenceStudyRevision) and isinstance(
        result, ReferenceRunResult
    ):
        return inspect_reference_study_results(artifact, result)
    if isinstance(artifact, B3StudyRevision) and isinstance(result, B3CuratedRunResult):
        return inspect_b3_results(artifact, result)
    if isinstance(artifact, MaxSpeedSweepDefinition) and isinstance(
        result, MaxSpeedSweepResult
    ):
        _require_definition_match(artifact, result.definition)
        return inspect_max_speed_sweep_results(result)
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition) and isinstance(
        result, EnvironmentSelectionComparisonResult
    ):
        _require_definition_match(artifact, result.definition)
        return inspect_environment_selection_results(result)
    raise ValueError(
        "The current-session result belongs to a different scientific artifact and "
        "will not be shown for this Study."
    )


def result_matches_artifact(
    artifact: ConcreteWorkbenchArtifact,
    result: AuthoritativeRunResult,
) -> bool:
    """Return whether WB5 accepts the result as belonging to the active artifact."""
    try:
        inspect_current_results(artifact, result)
    except (TypeError, ValueError):
        return False
    return True


def _require_definition_match(expected: object, actual: object) -> None:
    if actual != expected:
        raise ValueError(
            "The current-session result belongs to a different immutable Experiment "
            "definition and will not be shown."
        )


__all__ = ["InspectedResultsView", "inspect_current_results", "result_matches_artifact"]
