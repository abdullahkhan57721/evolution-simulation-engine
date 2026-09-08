"""Bind transient WU2/WU3 authoring state to exact runnable scientific artifacts."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import streamlit as st

from evo_engine.ui.evidence_page import pending_evidence_plan
from evo_engine.ui.experiment_page import (
    pending_experiment_definition,
    pending_experiment_error,
)
from evo_engine.ui.simulation_authoring import normalize_reference_draft
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench import (
    B3StudyRevision,
    ControlledLocomotionIntent,
    EnvironmentSelectionComparisonDefinition,
    EvidencePlan,
    MaxSpeedSweepDefinition,
    ReferenceEcologyIntent,
    ReferenceEvidencePlan,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchNotReadyError,
    WorkbenchReadiness,
    assess_b3_readiness,
    assess_readiness,
    assess_reference_readiness,
    fork_reference_study_revision,
    fork_study_revision,
)

_SIMULATION_DRAFT_INTENT_KEY = "wu2_simulation_draft_intent"
_SIMULATION_DRAFT_REVISION_KEY = "wu2_simulation_draft_revision_id"


def effective_readiness(
    artifact: ConcreteWorkbenchArtifact,
) -> WorkbenchReadiness:
    """Assess the exact saved artifact plus any owned transient revision draft."""
    if isinstance(artifact, StudyRevision):
        intent = _pending_controlled_intent(artifact) or artifact.intent
        plan = pending_evidence_plan(artifact) or artifact.evidence_plan
        if not isinstance(plan, EvidencePlan):
            raise TypeError("Controlled Study requires EvidencePlan.")
        return assess_readiness(intent, plan)
    if isinstance(artifact, ReferenceStudyRevision):
        intent = _pending_reference_intent(artifact) or artifact.intent
        plan = pending_evidence_plan(artifact) or artifact.evidence_plan
        if not isinstance(plan, ReferenceEvidencePlan):
            raise TypeError("Reference Study requires ReferenceEvidencePlan.")
        return assess_reference_readiness(normalize_reference_draft(intent), plan)
    if isinstance(artifact, B3StudyRevision):
        return assess_b3_readiness(artifact.intent, artifact.evidence_plan)
    if isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        return WorkbenchReadiness(state="ready")
    raise TypeError("Unsupported Workbench artifact for readiness.")


def bind_pending_scientific_state(
    artifact: ConcreteWorkbenchArtifact,
    *,
    new_revision_id: Callable[[str], str],
) -> tuple[ConcreteWorkbenchArtifact, str | None]:
    """Give unsaved scientific edits an exact immutable owner before Run Plan."""
    if isinstance(artifact, StudyRevision):
        return _bind_controlled(artifact, new_revision_id)
    if isinstance(artifact, ReferenceStudyRevision):
        return _bind_reference(artifact, new_revision_id)
    if isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        error = pending_experiment_error(artifact)
        if error is not None:
            raise ValueError(f"Experiment draft is not runnable: {error}")
        candidate = pending_experiment_definition(artifact)
        if candidate is not None and candidate != artifact:
            return (
                candidate,
                "Unsaved Experiment edits were bound to this exact immutable "
                "experiment definition before execution.",
            )
        return artifact, None
    if isinstance(artifact, B3StudyRevision):
        return artifact, None
    raise TypeError("Unsupported Workbench artifact for run binding.")


def _bind_controlled(
    parent: StudyRevision,
    new_revision_id: Callable[[str], str],
) -> tuple[StudyRevision, str | None]:
    intent = _pending_controlled_intent(parent) or parent.intent
    plan = pending_evidence_plan(parent) or parent.evidence_plan
    if not isinstance(plan, EvidencePlan):
        raise TypeError("Controlled Study requires EvidencePlan.")
    readiness = assess_readiness(intent, plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    if intent == parent.intent and plan == parent.evidence_plan:
        return parent, None
    child = fork_study_revision(
        parent,
        revision_id=new_revision_id("controlled-run"),
        max_speed=cast(int, intent.max_speed),
        resource_geography=cast(str, intent.resource_geography),
        seed=cast(int, intent.seed),
        evidence_plan=plan,
    )
    return (
        child,
        f"Unsaved Simulation/Evidence edits were saved as immutable revision "
        f"`{child.revision_id}` before execution.",
    )


def _bind_reference(
    parent: ReferenceStudyRevision,
    new_revision_id: Callable[[str], str],
) -> tuple[ReferenceStudyRevision, str | None]:
    intent = normalize_reference_draft(
        _pending_reference_intent(parent) or parent.intent
    )
    plan = pending_evidence_plan(parent) or parent.evidence_plan
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("Reference Study requires ReferenceEvidencePlan.")
    readiness = assess_reference_readiness(intent, plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    if intent == parent.intent and plan == parent.evidence_plan:
        return parent, None
    child = fork_reference_study_revision(
        parent,
        revision_id=new_revision_id("reference-run"),
        intent=intent,
        evidence_plan=plan,
    )
    return (
        child,
        f"Unsaved Simulation/Evidence edits were saved as immutable revision "
        f"`{child.revision_id}` before execution.",
    )


def _pending_controlled_intent(
    parent: StudyRevision,
) -> ControlledLocomotionIntent | None:
    if st.session_state.get(_SIMULATION_DRAFT_REVISION_KEY) != parent.revision_id:
        return None
    value = st.session_state.get(_SIMULATION_DRAFT_INTENT_KEY)
    return value if isinstance(value, ControlledLocomotionIntent) else None


def _pending_reference_intent(
    parent: ReferenceStudyRevision,
) -> ReferenceEcologyIntent | None:
    if st.session_state.get(_SIMULATION_DRAFT_REVISION_KEY) != parent.revision_id:
        return None
    value = st.session_state.get(_SIMULATION_DRAFT_INTENT_KEY)
    return value if isinstance(value, ReferenceEcologyIntent) else None


__all__ = ["bind_pending_scientific_state", "effective_readiness"]
