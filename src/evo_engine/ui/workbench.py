"""V2 interactive-presentation adapters for exact Workbench run artifacts.

This module is intentionally downstream of Workbench. It converts already-recorded
spatial/trait evidence into the existing renderer-neutral V2 world-presentation
values and keeps exact study/run/treatment context beside the frame. It never
calculates scientific outcomes or reconstructs missing evidence.
"""

from __future__ import annotations

from typing import Literal

import attrs

from evo_engine.genetics import MAX_SPEED
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
)
from evo_engine.ui.world_presentation import (
    WorldPresentationFrame,
    build_world_presentation,
)
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    ReferenceRunResult,
    ReferenceStudyRevision,
    WorkbenchRunProvenance,
)
from evo_engine.workbench.diagnostics import WorkbenchDiagnostic
from evo_engine.workbench.results import (
    AnalysisAvailability,
    inspect_b3_results,
    inspect_reference_study_results,
)
from evo_engine.workbench.support import analysis_availability_diagnostic

B3InteractiveArm = Literal["control", "treatment"]


class WorkbenchPresentationUnavailableError(ValueError):
    """Raised when a requested presentation is unavailable from recorded evidence."""

    def __init__(self, diagnostic: WorkbenchDiagnostic) -> None:
        if not isinstance(diagnostic, WorkbenchDiagnostic):
            raise TypeError("diagnostic must be a WorkbenchDiagnostic.")
        self.diagnostic = diagnostic
        message = diagnostic.message
        if diagnostic.remediation is not None:
            message = f"{message} {diagnostic.remediation}"
        super().__init__(message)


@attrs.frozen(slots=True, kw_only=True)
class WorkbenchWorldPresentation:
    """Keep exact Workbench context beside one existing V2 world frame."""

    provenance: WorkbenchRunProvenance
    seed: int
    frame: WorldPresentationFrame
    arm: str | None = None
    environment: str | None = None

    def __attrs_post_init__(self) -> None:
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer.")
        if self.arm is not None and self.arm not in ("control", "treatment"):
            raise ValueError("arm must be control, treatment, or None.")
        if self.environment is not None and (
            type(self.environment) is not str or not self.environment.strip()
        ):
            raise TypeError("environment must be a non-empty string or None.")


def build_reference_workbench_world_presentation(
    revision: ReferenceStudyRevision,
    result: ReferenceRunResult,
    *,
    step_index: int,
    selected_organism_id: int | None = None,
    show_resources: bool = True,
    show_carcasses: bool = True,
    show_trails: bool = True,
    trail_length: int = 5,
) -> WorkbenchWorldPresentation:
    """Build a V2 world frame only from spatial evidence actually recorded by WB4."""
    view = inspect_reference_study_results(revision, result)
    _require_available(view.spatial_availability)
    frame = build_world_presentation(
        view.spatial_observations,
        step_index=step_index,
        selected_organism_id=selected_organism_id,
        show_resources=show_resources,
        show_carcasses=show_carcasses,
        show_trails=show_trails,
        trail_length=trail_length,
    )
    return WorkbenchWorldPresentation(
        provenance=view.provenance,
        seed=view.scientific_provenance.seed,
        frame=frame,
    )


def build_b3_workbench_world_presentation(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
    *,
    seed: int,
    arm: B3InteractiveArm,
    step_index: int,
    selected_organism_id: int | None = None,
    show_resources: bool = True,
    show_carcasses: bool = True,
    show_trails: bool = True,
    trail_length: int = 5,
) -> WorkbenchWorldPresentation:
    """Build one matched B3 V2 frame while preserving arm/replicate identity."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer.")
    if arm not in ("control", "treatment"):
        raise ValueError("arm must be control or treatment.")
    view = inspect_b3_results(revision, result)
    pair = next((item for item in view.confirmation if item.summary.seed == seed), None)
    if pair is None:
        raise KeyError(f"No B3 confirmation replicate for seed {seed}.")
    evidence = pair.control_evidence if arm == "control" else pair.treatment_evidence
    if evidence.specification.seed != seed:
        raise ValueError("B3 evidence seed does not match selected replicate identity.")

    encoding = ContinuousTraitEncoding(
        trait_name=MAX_SPEED,
        label="Maximum speed",
        lower_bound=B3_LOW_MAX_SPEED,
        upper_bound=B3_HIGH_MAX_SPEED,
    )
    frame = build_world_presentation(
        evidence.spatial_observations,
        step_index=step_index,
        individual_trait_history=evidence.individual_trait_observations,
        focal_encoding=encoding,
        selected_organism_id=selected_organism_id,
        show_resources=show_resources,
        show_carcasses=show_carcasses,
        show_trails=show_trails,
        trail_length=trail_length,
    )
    return WorkbenchWorldPresentation(
        provenance=view.provenance,
        seed=seed,
        arm=arm,
        environment=evidence.specification.environment,
        frame=frame,
    )


def _require_available(availability: AnalysisAvailability) -> None:
    diagnostic = analysis_availability_diagnostic(availability)
    if diagnostic is None:
        return
    raise WorkbenchPresentationUnavailableError(diagnostic)


__all__ = [
    "B3InteractiveArm",
    "WorkbenchPresentationUnavailableError",
    "WorkbenchWorldPresentation",
    "build_b3_workbench_world_presentation",
    "build_reference_workbench_world_presentation",
]
