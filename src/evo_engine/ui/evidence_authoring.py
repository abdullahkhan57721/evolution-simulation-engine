"""UI-only Evidence helpers over existing concrete Workbench contracts."""

from __future__ import annotations

from typing import TypeAlias

import attrs

from evo_engine.workbench import (
    B3_EVENT_EVIDENCE_ID,
    B3_GENETIC_EVIDENCE_ID,
    B3_INDIVIDUAL_TRAIT_EVIDENCE_ID,
    B3_PEDIGREE_EVIDENCE_ID,
    B3_POPULATION_EVIDENCE_ID,
    B3_SPATIAL_EVIDENCE_ID,
    EVENT_EVIDENCE_ID,
    INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
    POPULATION_EVIDENCE_ID,
    REFERENCE_EVENT_EVIDENCE_ID,
    REFERENCE_GENETIC_EVIDENCE_ID,
    REFERENCE_PEDIGREE_EVIDENCE_ID,
    REFERENCE_POPULATION_EVIDENCE_ID,
    REFERENCE_SPATIAL_EVIDENCE_ID,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EvidenceAdvisory,
    EvidencePlan,
    MaxSpeedSweepDefinition,
    ReferenceEvidencePlan,
    ReferenceStudyRevision,
    StudyRevision,
    evidence_advisories,
    fork_reference_study_revision,
    fork_study_revision,
)

EvidenceBearingArtifact: TypeAlias = (
    StudyRevision
    | MaxSpeedSweepDefinition
    | EnvironmentSelectionComparisonDefinition
    | B3StudyRevision
    | ReferenceStudyRevision
)
EditableEvidencePlan: TypeAlias = EvidencePlan | ReferenceEvidencePlan


@attrs.frozen(slots=True, kw_only=True)
class EvidenceOption:
    """Describe one evidence stream in user-facing scientific language."""

    evidence_id: str
    label: str
    meaning: str
    enables: str
    required: bool


_CONTROLLED_OPTIONS = (
    EvidenceOption(
        evidence_id=POPULATION_EVIDENCE_ID,
        label="Population maximum-speed observations",
        meaning=(
            "Committed population observations of the focal inherited maximum-speed "
            "trait across the run."
        ),
        enables="Population trait trajectories and treatment-level focal-trait analysis.",
        required=False,
    ),
    EvidenceOption(
        evidence_id=EVENT_EVIDENCE_ID,
        label="Committed events",
        meaning=(
            "Authoritative events after conflict resolution and application, including "
            "realized locomotion consequences."
        ),
        enables="Realized movement and locomotion-energy measurements.",
        required=False,
    ),
)

_REFERENCE_OPTIONS = (
    EvidenceOption(
        evidence_id=REFERENCE_POPULATION_EVIDENCE_ID,
        label="Population traits",
        meaning="Committed population-level evolutionary trait observations.",
        enables="Population summaries and trait-change analysis.",
        required=False,
    ),
    EvidenceOption(
        evidence_id=REFERENCE_EVENT_EVIDENCE_ID,
        label="Committed events",
        meaning="Authoritative committed event/effect history from the simulation.",
        enables="Causal event analysis and mechanism inspection.",
        required=False,
    ),
    EvidenceOption(
        evidence_id=REFERENCE_PEDIGREE_EVIDENCE_ID,
        label="Pedigree and life history",
        meaning="Committed ancestry and individual life-history records.",
        enables="Lineage, ancestry, reproduction, and life-history analysis.",
        required=False,
    ),
    EvidenceOption(
        evidence_id=REFERENCE_GENETIC_EVIDENCE_ID,
        label="Genetic composition",
        meaning="Committed allele and genotype composition through time.",
        enables="Genetic-composition and inheritance analysis.",
        required=False,
    ),
    EvidenceOption(
        evidence_id=REFERENCE_SPATIAL_EVIDENCE_ID,
        label="Spatial history",
        meaning="Committed world-state frames needed for spatial replay.",
        enables="Spatial inspection and downstream interactive world presentation.",
        required=False,
    ),
)

_B3_OPTIONS = (
    EvidenceOption(
        evidence_id=B3_POPULATION_EVIDENCE_ID,
        label="Population",
        meaning="Population-level committed B3 observations.",
        enables="Primary and sensitivity population summaries.",
        required=True,
    ),
    EvidenceOption(
        evidence_id=B3_EVENT_EVIDENCE_ID,
        label="Committed events",
        meaning="Committed B3 event/effect evidence.",
        enables="Mechanism and causal episode analysis.",
        required=True,
    ),
    EvidenceOption(
        evidence_id=B3_GENETIC_EVIDENCE_ID,
        label="Genetic composition",
        meaning="Committed B3 allele/genotype composition.",
        enables="Genetic-composition analysis.",
        required=True,
    ),
    EvidenceOption(
        evidence_id=B3_INDIVIDUAL_TRAIT_EVIDENCE_ID,
        label="Individual focal trait",
        meaning="Per-individual committed maximum-speed evidence.",
        enables="Founder/descendant focal-trait analysis.",
        required=True,
    ),
    EvidenceOption(
        evidence_id=B3_SPATIAL_EVIDENCE_ID,
        label="Spatial history",
        meaning="Committed B3 world-state frames.",
        enables="Representative spatial mechanism episodes and presentation.",
        required=True,
    ),
    EvidenceOption(
        evidence_id=B3_PEDIGREE_EVIDENCE_ID,
        label="Pedigree",
        meaning="Committed B3 ancestry and life-history records.",
        enables="Founder reproductive-contribution and lineage analysis.",
        required=True,
    ),
)

_E4_INDIVIDUAL_OPTION = EvidenceOption(
    evidence_id=INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
    label="Individual focal trait",
    meaning="Per-individual committed maximum-speed evidence for standing variation.",
    enables="Standing-composition and individual focal-trait selection analysis.",
    required=True,
)


def evidence_options(artifact: EvidenceBearingArtifact) -> tuple[EvidenceOption, ...]:
    """Return scientific evidence descriptions for one concrete artifact."""
    if isinstance(artifact, StudyRevision):
        return _CONTROLLED_OPTIONS
    if isinstance(artifact, ReferenceStudyRevision):
        return _REFERENCE_OPTIONS
    if isinstance(artifact, B3StudyRevision):
        return _B3_OPTIONS
    if isinstance(artifact, MaxSpeedSweepDefinition):
        return tuple(attrs.evolve(option, required=True) for option in _CONTROLLED_OPTIONS)
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
        by_id = {option.evidence_id: option for option in _CONTROLLED_OPTIONS}
        ordered = (
            _E4_INDIVIDUAL_OPTION,
            attrs.evolve(by_id[POPULATION_EVIDENCE_ID], required=True),
            attrs.evolve(by_id[EVENT_EVIDENCE_ID], required=True),
        )
        return ordered
    raise TypeError("Unsupported artifact for Evidence presentation.")


def requested_evidence_ids(artifact: EvidenceBearingArtifact) -> tuple[str, ...]:
    """Return the exact evidence IDs owned by the concrete artifact."""
    return artifact.evidence_plan.requested


def make_editable_evidence_plan(
    artifact: StudyRevision | ReferenceStudyRevision,
    requested: tuple[str, ...],
) -> EditableEvidencePlan:
    """Build only the existing concrete evidence-plan type for an editable Study."""
    if isinstance(artifact, StudyRevision):
        return EvidencePlan(requested=requested)
    if isinstance(artifact, ReferenceStudyRevision):
        return ReferenceEvidencePlan(requested=requested)
    raise TypeError("Evidence authoring is supported only for revision-backed Studies.")


def save_evidence_child(
    parent: StudyRevision | ReferenceStudyRevision,
    *,
    requested: tuple[str, ...],
    revision_id: str,
) -> StudyRevision | ReferenceStudyRevision:
    """Save an Evidence change through the existing concrete immutable fork API."""
    plan = make_editable_evidence_plan(parent, requested)
    if isinstance(parent, StudyRevision):
        assert isinstance(plan, EvidencePlan)
        return fork_study_revision(
            parent,
            revision_id=revision_id,
            evidence_plan=plan,
        )
    assert isinstance(plan, ReferenceEvidencePlan)
    return fork_reference_study_revision(
        parent,
        revision_id=revision_id,
        intent=parent.intent,
        evidence_plan=plan,
    )


def evidence_advisories_for_artifact(
    artifact: EvidenceBearingArtifact,
    *,
    plan: EditableEvidencePlan | None = None,
) -> tuple[EvidenceAdvisory, ...]:
    """Return only advisories already owned by the concrete Workbench recipe."""
    if not isinstance(artifact, ReferenceStudyRevision):
        return ()
    reference_plan = artifact.evidence_plan if plan is None else plan
    if not isinstance(reference_plan, ReferenceEvidencePlan):
        raise TypeError("Reference Ecology advisories require ReferenceEvidencePlan.")
    return evidence_advisories(reference_plan)


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
