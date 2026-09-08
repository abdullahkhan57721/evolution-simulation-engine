"""Concrete Workbench artifact routing for the native Q1 application shell.

`Study` is a product/navigation concept here, not a persisted domain type.  The
native application owns only explicit dispatch and user-facing metadata over the
existing concrete Workbench artifacts.  Exact persistence remains with each
artifact's own serializer/loader.
"""

from __future__ import annotations

import json
from typing import Literal, TypeAlias, TypeGuard

from evo_engine.experiments.e3_performance import E3_CONFIRMATION_SEEDS
from evo_engine.experiments.e4_selection import E4_CONFIRMATION_SEEDS
from evo_engine.workbench.b3_curated import (
    B3_STUDY_FORMAT_ID,
    B3_VALIDATED_SCENARIO_ID,
    B3CuratedRunResult,
    B3StudyRevision,
    assess_b3_readiness,
    create_b3_study_revision,
    fork_b3_study_revision,
)
from evo_engine.workbench.controlled_locomotion import (
    IncompatibleManifestError,
    WorkbenchReadiness,
    assess_readiness,
)
from evo_engine.workbench.experiments import (
    ENVIRONMENT_SELECTION_PATTERN_ID,
    EXPERIMENT_DEFINITION_FORMAT_ID,
    MAX_SPEED_SWEEP_PATTERN_ID,
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
)
from evo_engine.workbench.reference_ecology import (
    assess_reference_readiness,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_study import (
    REFERENCE_STUDY_FORMAT_ID,
    ReferenceRunResult,
    ReferenceStudyRevision,
    create_reference_study_revision,
)
from evo_engine.workbench.results import (
    inspect_b3_results,
    inspect_controlled_locomotion_results,
    inspect_environment_selection_results,
    inspect_max_speed_sweep_results,
    inspect_reference_study_results,
)
from evo_engine.workbench.study import (
    STUDY_FORMAT_ID,
    StudyRevision,
    WorkbenchRunResult,
    create_study_revision,
)
from evo_engine.workbench.controlled_locomotion import ControlledLocomotionIntent

ArtifactKind = Literal[
    "controlled-run",
    "max-speed-sweep",
    "environment-selection-comparison",
    "b3-flagship",
    "reference-ecology",
]
StudySection = Literal[
    "Simulation",
    "Evidence",
    "Experiment",
    "Results",
    "Presentation",
]
ConcreteWorkbenchArtifact: TypeAlias = (
    StudyRevision
    | MaxSpeedSweepDefinition
    | EnvironmentSelectionComparisonDefinition
    | B3StudyRevision
    | ReferenceStudyRevision
)

STUDY_SECTIONS: tuple[StudySection, ...] = (
    "Simulation",
    "Evidence",
    "Experiment",
    "Results",
    "Presentation",
)


class UnsupportedStudyArtifactError(ValueError):
    """Raised when JSON is not one of the supported concrete Workbench formats."""


_ARTIFACT_TITLES: dict[ArtifactKind, str] = {
    "controlled-run": "Controlled Locomotion",
    "max-speed-sweep": "Max-Speed Sweep",
    "environment-selection-comparison": "Environment-Selection Comparison",
    "b3-flagship": "B3 Flagship",
    "reference-ecology": "Reference Ecology",
}

_ARTIFACT_TYPE_LABELS: dict[ArtifactKind, str] = {
    "controlled-run": "Controlled Workbench study revision",
    "max-speed-sweep": "Controlled max-speed sweep definition",
    "environment-selection-comparison": (
        "Controlled environment-selection comparison definition"
    ),
    "b3-flagship": "Curated B3 study revision",
    "reference-ecology": "Reference-ecology study revision",
}


def new_controlled_run(*, revision_id: str) -> StudyRevision:
    """Create the current bounded controlled-locomotion starting revision."""
    return create_study_revision(
        revision_id=revision_id,
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=E3_CONFIRMATION_SEEDS[0],
        ),
    )


def new_max_speed_sweep() -> MaxSpeedSweepDefinition:
    """Create the existing E3-pattern sweep with its confirmation seeds."""
    return MaxSpeedSweepDefinition(
        base_intent=ControlledLocomotionIntent(resource_geography="separated_corridor"),
        seeds=E3_CONFIRMATION_SEEDS,
    )


def new_environment_selection_comparison() -> EnvironmentSelectionComparisonDefinition:
    """Create the existing frozen E4-pattern environment comparison."""
    return EnvironmentSelectionComparisonDefinition(seeds=E4_CONFIRMATION_SEEDS)


def new_b3_flagship(*, revision_id: str) -> B3StudyRevision:
    """Create the canonical validated radius-1 B3 starting revision."""
    return create_b3_study_revision(revision_id=revision_id)


def new_reference_ecology(*, revision_id: str) -> ReferenceStudyRevision:
    """Create the current bounded Reference Ecology starting revision."""
    return create_reference_study_revision(
        revision_id=revision_id,
        intent=default_reference_ecology_intent(),
    )


def load_concrete_artifact(value: str) -> ConcreteWorkbenchArtifact:
    """Dispatch exact JSON to one existing concrete Workbench loader."""
    if type(value) is not str:
        raise TypeError("Study JSON must be a string.")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise UnsupportedStudyArtifactError("Study file is not valid JSON.") from exc
    if type(decoded) is not dict:
        raise UnsupportedStudyArtifactError("Study JSON must encode an object.")

    format_id = decoded.get("format_id")
    if format_id == STUDY_FORMAT_ID:
        return StudyRevision.from_json(value)
    if format_id == B3_STUDY_FORMAT_ID:
        return B3StudyRevision.from_json(value)
    if format_id == REFERENCE_STUDY_FORMAT_ID:
        return ReferenceStudyRevision.from_json(value)
    if format_id == EXPERIMENT_DEFINITION_FORMAT_ID:
        pattern_id = decoded.get("pattern_id")
        if pattern_id == MAX_SPEED_SWEEP_PATTERN_ID:
            return MaxSpeedSweepDefinition.from_json(value)
        if pattern_id == ENVIRONMENT_SELECTION_PATTERN_ID:
            return EnvironmentSelectionComparisonDefinition.from_json(value)
        raise UnsupportedStudyArtifactError(
            "Unsupported Workbench experiment pattern identity."
        )
    raise UnsupportedStudyArtifactError("Unsupported Workbench Study format identity.")


def serialize_concrete_artifact(artifact: ConcreteWorkbenchArtifact) -> str:
    """Return the artifact's own canonical persistence representation."""
    return artifact.to_json()


def is_concrete_artifact(value: object) -> TypeGuard[ConcreteWorkbenchArtifact]:
    """Return whether a value is one of Q1's five supported concrete artifacts."""
    return isinstance(
        value,
        (
            StudyRevision,
            MaxSpeedSweepDefinition,
            EnvironmentSelectionComparisonDefinition,
            B3StudyRevision,
            ReferenceStudyRevision,
        ),
    )


def artifact_kind(artifact: ConcreteWorkbenchArtifact) -> ArtifactKind:
    """Classify one supported concrete artifact for native navigation only."""
    if isinstance(artifact, StudyRevision):
        return "controlled-run"
    if isinstance(artifact, MaxSpeedSweepDefinition):
        return "max-speed-sweep"
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
        return "environment-selection-comparison"
    if isinstance(artifact, B3StudyRevision):
        return "b3-flagship"
    if isinstance(artifact, ReferenceStudyRevision):
        return "reference-ecology"
    raise TypeError("Unsupported Workbench artifact type.")


def artifact_title(artifact: ConcreteWorkbenchArtifact) -> str:
    """Return the product title for one concrete artifact."""
    return _ARTIFACT_TITLES[artifact_kind(artifact)]


def artifact_type_label(artifact: ConcreteWorkbenchArtifact) -> str:
    """Return a truthful user-facing concrete artifact type label."""
    if isinstance(artifact, B3StudyRevision) and artifact.study_kind != "validated-b3":
        return "B3-derived custom study revision"
    return _ARTIFACT_TYPE_LABELS[artifact_kind(artifact)]


def artifact_revision_id(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return revision identity only when the concrete artifact owns one."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return artifact.revision_id
    return None


def artifact_parent_revision_id(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return parent revision identity only when the artifact owns lineage."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return artifact.parent_revision_id
    return None


def artifact_manifest_digest(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return persisted manifest identity only for revision-backed artifacts."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return artifact.manifest.digest
    return None


def artifact_scenario_origin(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return scenario origin only for the concrete B3 lineage that owns it."""
    return artifact.scenario_origin if isinstance(artifact, B3StudyRevision) else None


def artifact_scenario_identity(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return validated scenario identity only where the artifact owns it."""
    return artifact.scenario_identity if isinstance(artifact, B3StudyRevision) else None


def artifact_readiness(artifact: ConcreteWorkbenchArtifact) -> WorkbenchReadiness:
    """Return existing authoritative readiness without a desktop readiness model."""
    if isinstance(artifact, StudyRevision):
        return assess_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(artifact, B3StudyRevision):
        return assess_b3_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(artifact, ReferenceStudyRevision):
        return assess_reference_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        return WorkbenchReadiness(state="ready")
    raise TypeError("Unsupported Workbench artifact for readiness.")


def artifact_run_count(artifact: ConcreteWorkbenchArtifact) -> int | None:
    """Return persisted run-reference count where the concrete format stores it."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return len(artifact.runs)
    return None


def can_fork_artifact(artifact: ConcreteWorkbenchArtifact) -> bool:
    """Return whether Q1 exposes an already-established one-click scientific fork."""
    return (
        isinstance(artifact, B3StudyRevision)
        and artifact.scenario_identity == B3_VALIDATED_SCENARIO_ID
    )


def fork_supported_artifact(
    artifact: ConcreteWorkbenchArtifact,
    *,
    revision_id: str,
) -> B3StudyRevision:
    """Create only the existing canonical-B3 to radius-2 sensitivity fork."""
    if not can_fork_artifact(artifact) or not isinstance(artifact, B3StudyRevision):
        raise ValueError("The active Study has no Q1 one-click scientific fork.")
    return fork_b3_study_revision(artifact, revision_id=revision_id)


def result_matches_artifact(
    artifact: ConcreteWorkbenchArtifact,
    result: object,
) -> bool:
    """Return whether existing WB5 semantics accept this artifact/result pair."""
    try:
        if isinstance(artifact, StudyRevision) and isinstance(result, WorkbenchRunResult):
            inspect_controlled_locomotion_results(artifact, result)
            return True
        if isinstance(artifact, ReferenceStudyRevision) and isinstance(
            result, ReferenceRunResult
        ):
            inspect_reference_study_results(artifact, result)
            return True
        if isinstance(artifact, B3StudyRevision) and isinstance(result, B3CuratedRunResult):
            inspect_b3_results(artifact, result)
            return True
        if isinstance(artifact, MaxSpeedSweepDefinition) and isinstance(
            result, MaxSpeedSweepResult
        ):
            if result.definition != artifact:
                return False
            inspect_max_speed_sweep_results(result)
            return True
        if isinstance(artifact, EnvironmentSelectionComparisonDefinition) and isinstance(
            result, EnvironmentSelectionComparisonResult
        ):
            if result.definition != artifact:
                return False
            inspect_environment_selection_results(result)
            return True
    except (TypeError, ValueError):
        return False
    return False


def result_owner_token(
    artifact: ConcreteWorkbenchArtifact,
    result: object,
) -> str | None:
    """Return a session presentation-owner token for supported revision run results."""
    if not result_matches_artifact(artifact, result):
        return None
    if isinstance(result, (WorkbenchRunResult, ReferenceRunResult, B3CuratedRunResult)):
        provenance = result.provenance
        return ":".join(
            (
                artifact_kind(artifact),
                provenance.study_revision_id,
                provenance.manifest_digest,
                provenance.run_id,
            )
        )
    return None


__all__ = [
    "ArtifactKind",
    "ConcreteWorkbenchArtifact",
    "STUDY_SECTIONS",
    "StudySection",
    "UnsupportedStudyArtifactError",
    "artifact_kind",
    "artifact_manifest_digest",
    "artifact_parent_revision_id",
    "artifact_readiness",
    "artifact_revision_id",
    "artifact_run_count",
    "artifact_scenario_identity",
    "artifact_scenario_origin",
    "artifact_title",
    "artifact_type_label",
    "can_fork_artifact",
    "fork_supported_artifact",
    "is_concrete_artifact",
    "load_concrete_artifact",
    "new_b3_flagship",
    "new_controlled_run",
    "new_environment_selection_comparison",
    "new_max_speed_sweep",
    "new_reference_ecology",
    "result_matches_artifact",
    "result_owner_token",
    "serialize_concrete_artifact",
    "IncompatibleManifestError",
]
