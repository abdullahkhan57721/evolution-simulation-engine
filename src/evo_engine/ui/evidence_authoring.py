"""Streamlit compatibility facade for frontend-neutral Evidence authoring."""

from evo_engine.workbench.evidence_authoring import (
    EditableEvidencePlan,
    EvidenceBearingArtifact,
    EvidenceOption,
    evidence_advisories_for_artifact,
    evidence_options,
    make_editable_evidence_plan,
    requested_evidence_ids,
    save_evidence_child,
)

__all__ = [
    "EditableEvidencePlan",
    "EvidenceBearingArtifact",
    "EvidenceOption",
    "evidence_advisories_for_artifact",
    "evidence_options",
    "make_editable_evidence_plan",
    "requested_evidence_ids",
    "save_evidence_child",
]
