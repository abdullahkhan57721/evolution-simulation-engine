"""WU3 Evidence-page rendering over existing concrete Workbench evidence plans."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from evo_engine.ui.evidence_authoring import (
    EditableEvidencePlan,
    EvidenceBearingArtifact,
    evidence_advisories_for_artifact,
    evidence_options,
    make_editable_evidence_plan,
    requested_evidence_ids,
    save_evidence_child,
)
from evo_engine.workbench import (
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EvidencePlan,
    MaxSpeedSweepDefinition,
    ReferenceEvidencePlan,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchReadiness,
    assess_readiness,
    assess_reference_readiness,
)

_DRAFT_PLAN_KEY = "wu3_evidence_draft_plan"
_DRAFT_OWNER_KEY = "wu3_evidence_draft_owner"


def clear_evidence_authoring_state() -> None:
    """Clear transient WU3 Evidence controls when Study context changes."""
    for key in tuple(st.session_state):
        if str(key).startswith("wu3_evidence_"):
            st.session_state.pop(key, None)


def pending_evidence_plan(
    artifact: EvidenceBearingArtifact,
) -> EditableEvidencePlan | None:
    """Return a pending concrete plan only when it belongs to this saved revision."""
    if not isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
        return None
    if st.session_state.get(_DRAFT_OWNER_KEY) != artifact.revision_id:
        return None
    plan = st.session_state.get(_DRAFT_PLAN_KEY)
    if isinstance(artifact, StudyRevision) and isinstance(plan, EvidencePlan):
        return plan
    if isinstance(artifact, ReferenceStudyRevision) and isinstance(
        plan, ReferenceEvidencePlan
    ):
        return plan
    return None


def render_evidence_page(
    artifact: EvidenceBearingArtifact,
    *,
    new_revision_id: Callable[[str], str],
) -> StudyRevision | ReferenceStudyRevision | None:
    """Render Evidence and return a newly saved immutable child when requested."""
    st.header("Evidence")
    st.write("Choose what scientific evidence this Study records.")

    if isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
        return _render_editable_evidence(artifact, new_revision_id)
    _render_locked_evidence(artifact)
    return None


def _render_editable_evidence(
    artifact: StudyRevision | ReferenceStudyRevision,
    new_revision_id: Callable[[str], str],
) -> StudyRevision | ReferenceStudyRevision | None:
    current = pending_evidence_plan(artifact) or artifact.evidence_plan
    selected: list[str] = []
    for option in evidence_options(artifact):
        enabled = st.checkbox(
            option.label,
            value=option.evidence_id in current.requested,
            key=_widget_key(artifact.revision_id, option.evidence_id),
        )
        st.caption(option.meaning)
        st.caption(f"Enables: {option.enables}")
        if enabled:
            selected.append(option.evidence_id)
        st.markdown("")

    plan = make_editable_evidence_plan(artifact, tuple(selected))
    _store_pending_plan(artifact, plan)
    readiness = _readiness_for_plan(artifact, plan)
    _render_readiness(readiness)
    for advisory in evidence_advisories_for_artifact(artifact, plan=plan):
        st.warning(advisory.message)

    if plan == artifact.evidence_plan:
        st.caption("Evidence matches the current immutable revision.")
        return None
    st.info(
        "Evidence is scientific Study intent. Saving creates a new immutable "
        "revision; the current saved revision is not edited in place."
    )
    if st.button(
        "Save Evidence as new revision",
        type="primary",
        disabled=readiness.state != "ready",
    ):
        prefix = "controlled" if isinstance(artifact, StudyRevision) else "reference"
        return save_evidence_child(
            artifact,
            requested=plan.requested,
            revision_id=new_revision_id(prefix),
        )
    return None


def _render_locked_evidence(
    artifact: MaxSpeedSweepDefinition
    | EnvironmentSelectionComparisonDefinition
    | B3StudyRevision,
) -> None:
    if isinstance(artifact, B3StudyRevision):
        st.info("This evidence set is part of the validated B3 scientific design.")
    else:
        st.info(
            "This concrete experiment requires its displayed evidence for the "
            "authoritative scientific analysis. Required streams cannot be removed."
        )
    requested = set(requested_evidence_ids(artifact))
    for option in evidence_options(artifact):
        st.checkbox(
            option.label,
            value=option.evidence_id in requested,
            disabled=True,
            key=f"wu3_evidence_locked_{option.evidence_id}",
        )
        st.caption(option.meaning)
        st.caption(f"Enables: {option.enables}")


def _readiness_for_plan(
    artifact: StudyRevision | ReferenceStudyRevision,
    plan: EditableEvidencePlan,
) -> WorkbenchReadiness:
    if isinstance(artifact, StudyRevision):
        if not isinstance(plan, EvidencePlan):
            raise TypeError("Controlled Evidence requires the controlled EvidencePlan.")
        return assess_readiness(artifact.intent, plan)
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("Reference Ecology Evidence requires ReferenceEvidencePlan.")
    return assess_reference_readiness(artifact.intent, plan)


def _render_readiness(readiness: WorkbenchReadiness) -> None:
    st.markdown(f"**Readiness · {readiness.state.title()}**")
    for diagnostic in readiness.diagnostics:
        if readiness.state == "blocked":
            st.error(diagnostic.message)
        else:
            st.warning(diagnostic.message)
        if diagnostic.remediation is not None:
            st.caption(diagnostic.remediation)


def _store_pending_plan(
    artifact: StudyRevision | ReferenceStudyRevision,
    plan: EditableEvidencePlan,
) -> None:
    st.session_state[_DRAFT_OWNER_KEY] = artifact.revision_id
    st.session_state[_DRAFT_PLAN_KEY] = plan


def _widget_key(revision_id: str, evidence_id: str) -> str:
    safe_id = evidence_id.replace(".", "-")
    return f"wu3_evidence_widget_{revision_id}_{safe_id}"


__all__ = [
    "clear_evidence_authoring_state",
    "pending_evidence_plan",
    "render_evidence_page",
]
