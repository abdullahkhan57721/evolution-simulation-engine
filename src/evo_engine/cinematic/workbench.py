"""Downstream cinematic adapters for validated Workbench scientific results."""

from __future__ import annotations

from evo_engine.cinematic.b3_director import (
    B3_REPRESENTATIVE_SEED,
    B3FlagshipDirectorPlan,
    prepare_b3_flagship_director,
)
from evo_engine.workbench import B3CuratedRunResult, B3StudyRevision
from evo_engine.workbench.results import inspect_b3_results


def prepare_b3_workbench_cinematic(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
) -> B3FlagshipDirectorPlan:
    """Prepare the existing confirmed B3 cinematic from one exact Workbench result.

    Workbench owns only study/run association and evidence availability.  The
    existing B3 director remains authoritative for representative-seed selection,
    scientific encoding, confirmation semantics, sensitivity evidence, bounded
    conclusion text, and renderer-neutral choreography inputs.
    """
    view = inspect_b3_results(revision, result)
    availability = view.cinematic_handoff_availability
    if not availability.available:
        missing = ", ".join(availability.missing_evidence_ids)
        detail = availability.unavailable_reason
        if missing:
            detail = (
                f"Missing recorded evidence: {missing}."
                if detail is None
                else f"{detail} Missing recorded evidence: {missing}."
            )
        raise ValueError(
            detail
            or "The confirmed B3 cinematic scientific handoff is unavailable."
        )

    representative = next(
        (
            pair
            for pair in view.confirmation
            if pair.summary.seed == B3_REPRESENTATIVE_SEED
        ),
        None,
    )
    if representative is None:
        raise ValueError(
            "The authoritative B3 representative seed is missing from confirmation "
            "artifacts."
        )

    return prepare_b3_flagship_director(
        control_evidence=representative.control_evidence,
        treatment_evidence=representative.treatment_evidence,
        confirmation_pairs=tuple(pair.summary for pair in view.confirmation),
        broad_patch_summaries=tuple(
            item.summary for item in view.radius_sensitivity
        ),
    )


__all__ = ["prepare_b3_workbench_cinematic"]
