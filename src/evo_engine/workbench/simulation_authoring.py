"""Frontend-neutral Simulation authoring helpers over concrete Workbench contracts."""

from __future__ import annotations

from typing import Literal, TypeAlias, cast

import attrs

from evo_engine.workbench.b3_curated import (
    B3CuratedDiff,
    B3StudyRevision,
    diff_b3_study_revisions,
    fork_b3_study_revision,
)
from evo_engine.workbench.controlled_locomotion import (
    ControlledLocomotionDiff,
    ControlledLocomotionIntent,
    WorkbenchNotReadyError,
    WorkbenchReadiness,
    assess_readiness,
)
from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_RADIUS_SLOT,
    PATCH_1_X_SLOT,
    PATCH_1_Y_SLOT,
    PATCH_2_RADIUS_SLOT,
    PATCH_2_X_SLOT,
    PATCH_2_Y_SLOT,
    REFERENCE_EXPERT_SLOT_IDS,
    REFERENCE_SLOT_METADATA,
    ReferenceEcologyDiff,
    ReferenceEcologyIntent,
    ReferenceSlotMetadata,
    assess_reference_readiness,
    is_slot_applicable,
)
from evo_engine.workbench.reference_ecology import (
    slot_metadata as reference_slot_metadata,
)
from evo_engine.workbench.reference_study import (
    ReferenceStudyRevision,
    diff_reference_study_revisions,
    fork_reference_study_revision,
)
from evo_engine.workbench.study import (
    StudyRevision,
    diff_study_revisions,
    fork_study_revision,
)

ReferenceDisclosure = Literal["Guided", "Advanced"]
EditableSimulationRevision: TypeAlias = StudyRevision | ReferenceStudyRevision
SimulationRevision: TypeAlias = StudyRevision | ReferenceStudyRevision | B3StudyRevision
SimulationDiff: TypeAlias = (
    ControlledLocomotionDiff | ReferenceEcologyDiff | B3CuratedDiff
)

_REFERENCE_CONDITIONAL_FIELDS: tuple[tuple[str, str], ...] = (
    (GAUSSIAN_STDDEV_SLOT, "gaussian_standard_deviation"),
    (PATCH_1_X_SLOT, "patch_1_center_x"),
    (PATCH_1_Y_SLOT, "patch_1_center_y"),
    (PATCH_1_RADIUS_SLOT, "patch_1_radius"),
    (PATCH_2_X_SLOT, "patch_2_center_x"),
    (PATCH_2_Y_SLOT, "patch_2_center_y"),
    (PATCH_2_RADIUS_SLOT, "patch_2_radius"),
    (MUTATION_PROBABILITY_SLOT, "mutation_probability_ppm"),
    (MUTATION_MAX_CHANGE_SLOT, "mutation_max_change"),
)


def reference_slots_for_disclosure(
    intent: ReferenceEcologyIntent,
    disclosure: ReferenceDisclosure,
) -> tuple[ReferenceSlotMetadata, ...]:
    """Return current officially supported slots visible at one disclosure level."""
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")
    if disclosure not in ("Guided", "Advanced"):
        raise ValueError("disclosure must be Guided or Advanced.")
    visible_tiers = {"guided"} if disclosure == "Guided" else {"guided", "advanced"}
    return tuple(
        metadata
        for metadata in REFERENCE_SLOT_METADATA
        if metadata.support_tier in visible_tiers
        and is_slot_applicable(intent, metadata.slot_id)
    )


def normalize_reference_draft(intent: ReferenceEcologyIntent) -> ReferenceEcologyIntent:
    """Clear only values that current WB4 applicability says are inactive.

    This is transient frontend-state hygiene. Saved scientific normalization remains
    owned by ``fork_reference_study_revision`` / ``create_reference_study_revision``.
    """
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")
    replacements: dict[str, object] = {}
    for slot_id, field_name in _REFERENCE_CONDITIONAL_FIELDS:
        if not is_slot_applicable(intent, slot_id):
            replacements[field_name] = None
    return attrs.evolve(intent, **replacements) if replacements else intent


def reference_has_expert_controls() -> bool:
    """Return whether the current bounded recipe actually exposes Expert slots."""
    return bool(REFERENCE_EXPERT_SLOT_IDS)


def controlled_draft_readiness(
    parent: StudyRevision,
    draft: ControlledLocomotionIntent,
) -> WorkbenchReadiness:
    """Assess a controlled draft through the existing WB1 readiness contract."""
    if not isinstance(parent, StudyRevision):
        raise TypeError("parent must be a StudyRevision.")
    return assess_readiness(draft, parent.evidence_plan)


def reference_draft_readiness(
    parent: ReferenceStudyRevision,
    draft: ReferenceEcologyIntent,
) -> WorkbenchReadiness:
    """Assess a reference draft through the existing WB4 readiness contract."""
    if not isinstance(parent, ReferenceStudyRevision):
        raise TypeError("parent must be a ReferenceStudyRevision.")
    return assess_reference_readiness(
        normalize_reference_draft(draft),
        parent.evidence_plan,
    )


def save_controlled_child(
    parent: StudyRevision,
    *,
    draft: ControlledLocomotionIntent,
    revision_id: str,
) -> StudyRevision:
    """Create an immutable controlled child revision from a ready frontend draft."""
    readiness = controlled_draft_readiness(parent, draft)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    return fork_study_revision(
        parent,
        revision_id=revision_id,
        max_speed=cast(int, draft.max_speed),
        resource_geography=cast(str, draft.resource_geography),
        seed=cast(int, draft.seed),
    )


def save_reference_child(
    parent: ReferenceStudyRevision,
    *,
    draft: ReferenceEcologyIntent,
    revision_id: str,
) -> ReferenceStudyRevision:
    """Create an immutable reference child through the existing WB4 fork contract."""
    normalized = normalize_reference_draft(draft)
    readiness = assess_reference_readiness(normalized, parent.evidence_plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    return fork_reference_study_revision(
        parent,
        revision_id=revision_id,
        intent=normalized,
    )


def save_b3_radius_sensitivity_child(
    parent: B3StudyRevision,
    *,
    revision_id: str,
) -> B3StudyRevision:
    """Create the one supported B3 radius-sensitivity child revision."""
    if not isinstance(parent, B3StudyRevision):
        raise TypeError("parent must be a B3StudyRevision.")
    return fork_b3_study_revision(parent, revision_id=revision_id)


def simulation_semantic_diff(
    before: SimulationRevision,
    after: SimulationRevision,
) -> SimulationDiff:
    """Dispatch to the existing concrete recipe-scoped semantic diff."""
    if isinstance(before, StudyRevision) and isinstance(after, StudyRevision):
        return diff_study_revisions(before, after)
    if isinstance(before, ReferenceStudyRevision) and isinstance(
        after, ReferenceStudyRevision
    ):
        return diff_reference_study_revisions(before, after)
    if isinstance(before, B3StudyRevision) and isinstance(after, B3StudyRevision):
        return diff_b3_study_revisions(before, after)
    raise TypeError("Semantic diff requires matching concrete revision types.")


def semantic_slot_label(slot_id: str) -> str:
    """Return a readable label while preserving stable semantic-slot identity."""
    if type(slot_id) is not str or not slot_id:
        raise TypeError("slot_id must be a non-empty string.")
    controlled = {
        "controlled-locomotion.max-speed": "Maximum speed",
        "controlled-locomotion.resource-geography": "Resource geography",
        "controlled-locomotion.seed": "Random seed",
    }
    if slot_id in controlled:
        return controlled[slot_id]
    try:
        return reference_slot_metadata(slot_id).label
    except KeyError:
        suffix = slot_id.split(".", 1)[-1]
        return suffix.replace("-", " ").replace("_", " ").title()


__all__ = [
    "EditableSimulationRevision",
    "ReferenceDisclosure",
    "SimulationDiff",
    "SimulationRevision",
    "controlled_draft_readiness",
    "normalize_reference_draft",
    "reference_draft_readiness",
    "reference_has_expert_controls",
    "reference_slots_for_disclosure",
    "save_b3_radius_sensitivity_child",
    "save_controlled_child",
    "save_reference_child",
    "semantic_slot_label",
    "simulation_semantic_diff",
]
