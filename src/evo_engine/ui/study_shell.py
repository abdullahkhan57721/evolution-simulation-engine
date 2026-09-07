"""UI-only routing over the Workbench's existing concrete persisted artifacts.

This module deliberately does not define a universal Study domain model.  It gives
Streamlit one explicit dispatch seam while leaving scientific identity, persistence,
readiness, and exact-reproduction semantics with the concrete Workbench contracts.
"""

from __future__ import annotations

import json
from typing import Literal, TypeAlias, TypeGuard

from evo_engine.experiments.e3_performance import E3_CONFIRMATION_SEEDS
from evo_engine.experiments.e4_selection import E4_CONFIRMATION_SEEDS
from evo_engine.workbench import (
    B3_STUDY_FORMAT_ID,
    ENVIRONMENT_SELECTION_PATTERN_ID,
    EXPERIMENT_DEFINITION_FORMAT_ID,
    MAX_SPEED_SWEEP_PATTERN_ID,
    REFERENCE_STUDY_FORMAT_ID,
    STUDY_FORMAT_ID,
    B3StudyRevision,
    ControlledLocomotionIntent,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchReadiness,
    assess_b3_readiness,
    assess_readiness,
    assess_reference_readiness,
    create_b3_study_revision,
    create_reference_study_revision,
    create_study_revision,
    default_reference_ecology_intent,
)

ArtifactKind = Literal[
    "controlled-run",
    "max-speed-sweep",
    "environment-selection-comparison",
    "b3-flagship",
    "reference-ecology",
]
ConcreteWorkbenchArtifact: TypeAlias = (
    StudyRevision
    | MaxSpeedSweepDefinition
    | EnvironmentSelectionComparisonDefinition
    | B3StudyRevision
    | ReferenceStudyRevision
)


class UnsupportedStudyArtifactError(ValueError):
    """Raised when an uploaded JSON object is not a supported concrete format."""


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
    """Create one valid bounded controlled-locomotion starting revision."""
    return create_study_revision(
        revision_id=revision_id,
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=E3_CONFIRMATION_SEEDS[0],
        ),
    )


def new_max_speed_sweep() -> MaxSpeedSweepDefinition:
    """Create the existing E3-pattern sweep with its established confirmation seeds."""
    return MaxSpeedSweepDefinition(
        base_intent=ControlledLocomotionIntent(
            resource_geography="separated_corridor"
        ),
        seeds=E3_CONFIRMATION_SEEDS,
    )


def new_environment_selection_comparison() -> EnvironmentSelectionComparisonDefinition:
    """Create the existing frozen E4-pattern environment comparison."""
    return EnvironmentSelectionComparisonDefinition(seeds=E4_CONFIRMATION_SEEDS)


def new_b3_flagship(*, revision_id: str) -> B3StudyRevision:
    """Create the canonical radius-1 B3 starting revision."""
    return create_b3_study_revision(revision_id=revision_id)


def new_reference_ecology(*, revision_id: str) -> ReferenceStudyRevision:
    """Create the bounded WB4 reference-ecology starting revision."""
    return create_reference_study_revision(
        revision_id=revision_id,
        intent=default_reference_ecology_intent(),
    )


def load_concrete_artifact(value: str) -> ConcreteWorkbenchArtifact:
    """Dispatch uploaded JSON to exactly one existing concrete loader.

    Only format and pattern identity are inspected here.  The scientific payload is
    never translated, normalized, or re-resolved by the UI.
    """
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


def is_concrete_artifact(value: object) -> TypeGuard[ConcreteWorkbenchArtifact]:
    """Return whether session state holds one of WU1's exact supported artifacts."""
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


def serialize_concrete_artifact(artifact: ConcreteWorkbenchArtifact) -> str:
    """Return the concrete artifact's own canonical persistence representation."""
    return artifact.to_json()


def artifact_kind(artifact: ConcreteWorkbenchArtifact) -> ArtifactKind:
    """Classify one supported concrete artifact for UI navigation only."""
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
    """Return a truthful concrete-type label for the Study shell."""
    if isinstance(artifact, B3StudyRevision) and artifact.study_kind != "validated-b3":
        return "B3-derived custom study revision"
    return _ARTIFACT_TYPE_LABELS[artifact_kind(artifact)]


def artifact_revision_id(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return revision identity only for artifacts that actually own one."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return artifact.revision_id
    return None


def artifact_readiness(
    artifact: ConcreteWorkbenchArtifact,
) -> WorkbenchReadiness | None:
    """Map only concrete Workbench readiness APIs that already exist."""
    if isinstance(artifact, StudyRevision):
        return assess_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(artifact, B3StudyRevision):
        return assess_b3_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(artifact, ReferenceStudyRevision):
        return assess_reference_readiness(artifact.intent, artifact.evidence_plan)
    return None


def artifact_run_count(artifact: ConcreteWorkbenchArtifact) -> int | None:
    """Return persisted run-reference count where the concrete format stores it."""
    if isinstance(artifact, (StudyRevision, B3StudyRevision, ReferenceStudyRevision)):
        return len(artifact.runs)
    return None


def artifact_download_name(artifact: ConcreteWorkbenchArtifact) -> str:
    """Return a stable user-facing filename without wrapping the saved payload."""
    revision_id = artifact_revision_id(artifact)
    stem = revision_id if revision_id is not None else artifact_kind(artifact)
    return f"{stem}.json"


__all__ = [
    "ArtifactKind",
    "ConcreteWorkbenchArtifact",
    "UnsupportedStudyArtifactError",
    "artifact_download_name",
    "artifact_kind",
    "artifact_readiness",
    "artifact_revision_id",
    "artifact_run_count",
    "artifact_title",
    "artifact_type_label",
    "is_concrete_artifact",
    "load_concrete_artifact",
    "new_b3_flagship",
    "new_controlled_run",
    "new_environment_selection_comparison",
    "new_max_speed_sweep",
    "new_reference_ecology",
    "serialize_concrete_artifact",
]
