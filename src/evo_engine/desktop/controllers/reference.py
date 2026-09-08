"""Family-specific Qt controller for Reference Ecology authoring, run, and world state."""

# PySide's Property setter decorator is a runtime descriptor but its stubs currently
# report paired getter/setter declarations as a redeclaration.
# pyright: reportRedeclaration=false

from __future__ import annotations

import uuid

import attrs
from PySide6.QtCore import Property, QObject, QThread, Signal, Slot

from evo_engine.desktop.models import WorldOrganismModel, WorldResourceModel
from evo_engine.presentation.workbench import (
    WorkbenchWorldPresentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.ui.simulation_authoring import (
    normalize_reference_draft,
    reference_has_expert_controls,
    save_reference_child,
)
from evo_engine.workbench.reference_ecology import (
    ReferenceEcologyIntent,
    ReferenceEcologyManifest,
    assess_reference_readiness,
    resolve_reference_ecology,
)
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    ReferenceStudyRevision,
    run_reference_study_revision,
)
from evo_engine.workbench.results import inspect_reference_study_results


class _ReferenceRunWorker(QObject):
    """Run the existing synchronous Reference Workbench runner off the GUI thread."""

    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, revision: ReferenceStudyRevision) -> None:
        super().__init__()
        self._revision = revision

    @Slot()
    def run(self) -> None:
        try:
            result = run_reference_study_revision(self._revision)
        except Exception as exc:  # boundary converts worker failure into UI state
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.completed.emit(result)


class ReferenceStudyController(QObject):
    """Own the bounded Reference draft plus the retained Q0 run/world vertical."""

    activeChanged = Signal()
    draftChanged = Signal()
    scientificDraftChanged = Signal()
    revisionCommitted = Signal(object)
    runCompleted = Signal(object, object)
    runningChanged = Signal()
    resultsChanged = Signal()
    worldChanged = Signal()
    statusChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._revision: ReferenceStudyRevision | None = None
        self._draft_intent: ReferenceEcologyIntent | None = None
        self._normalization_notice = False
        self._result: ReferenceRunResult | None = None
        self._presentation: WorkbenchWorldPresentation | None = None
        self._organisms = WorldOrganismModel()
        self._resources = WorldResourceModel()
        self._thread: QThread | None = None
        self._worker: _ReferenceRunWorker | None = None
        self._status = "Reference Ecology controls are available for active studies."

    def is_active(self) -> bool:
        return self._revision is not None

    @Property(bool, notify=activeChanged)
    def active(self) -> bool:
        return self.is_active()

    def draft_intent(self) -> ReferenceEcologyIntent | None:
        """Return the transient Reference draft for sibling native controllers."""
        return self._draft_intent

    def preview_manifest(self) -> ReferenceEcologyManifest | None:
        """Resolve the transient draft only when existing WB4 readiness accepts it."""
        if self._revision is None or self._draft_intent is None:
            return None
        readiness = assess_reference_readiness(
            self._draft_intent, self._revision.evidence_plan
        )
        if readiness.state != "ready":
            return None
        return resolve_reference_ecology(self._draft_intent, self._revision.evidence_plan)

    @Property(bool, notify=draftChanged)
    def draftDirty(self) -> bool:  # noqa: N802
        return self.is_draft_dirty()

    def is_draft_dirty(self) -> bool:
        return (
            self._revision is not None
            and self._draft_intent is not None
            and self._draft_intent != self._revision.intent
        )

    @Property(bool, notify=draftChanged)
    def draftReady(self) -> bool:  # noqa: N802
        if self._draft_intent is None or self._revision is None:
            return False
        return (
            assess_reference_readiness(
                self._draft_intent, self._revision.evidence_plan
            ).state
            == "ready"
        )

    @Property(str, notify=draftChanged)
    def readinessMessage(self) -> str:  # noqa: N802
        return self._readiness_message()

    @Property(bool, notify=draftChanged)
    def normalizationNotice(self) -> bool:  # noqa: N802
        return self._normalization_notice

    @Property(bool, constant=True)
    def hasExpertControls(self) -> bool:  # noqa: N802
        return reference_has_expert_controls()

    @Property(bool, notify=draftChanged)
    def gaussianApplicable(self) -> bool:  # noqa: N802
        return self._draft_intent is not None and self._draft_intent.exploration_movement == "gaussian"

    @Property(bool, notify=draftChanged)
    def patchGeometryApplicable(self) -> bool:  # noqa: N802
        return self._draft_intent is not None and self._draft_intent.resource_geography == "two_patches"

    @Property(bool, notify=draftChanged)
    def mutationParametersApplicable(self) -> bool:  # noqa: N802
        return self._draft_intent is not None and self._draft_intent.mutation_enabled is True

    @Property(int, notify=draftChanged)
    def draftWorldWidth(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "width")

    @draftWorldWidth.setter
    def draftWorldWidth(self, value: int) -> None:  # noqa: N802
        self._replace_draft(width=value)

    @Property(int, notify=draftChanged)
    def draftWorldHeight(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "height")

    @draftWorldHeight.setter
    def draftWorldHeight(self, value: int) -> None:  # noqa: N802
        self._replace_draft(height=value)

    @Property(int, notify=draftChanged)
    def draftFounderPopulation(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "founder_population")

    @draftFounderPopulation.setter
    def draftFounderPopulation(self, value: int) -> None:  # noqa: N802
        self._replace_draft(founder_population=value)

    @Property(int, notify=draftChanged)
    def draftFounderEnergy(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "founder_energy")

    @draftFounderEnergy.setter
    def draftFounderEnergy(self, value: int) -> None:  # noqa: N802
        self._replace_draft(founder_energy=value)

    @Property(int, notify=draftChanged)
    def draftHorizon(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "horizon")

    @draftHorizon.setter
    def draftHorizon(self, value: int) -> None:  # noqa: N802
        self._replace_draft(horizon=value)

    @Property(int, notify=draftChanged)
    def draftSeed(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "seed")

    @draftSeed.setter
    def draftSeed(self, value: int) -> None:  # noqa: N802
        self._replace_draft(seed=value)

    @Property(int, notify=draftChanged)
    def draftMaxSpeed(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "max_speed")

    @draftMaxSpeed.setter
    def draftMaxSpeed(self, value: int) -> None:  # noqa: N802
        self.set_draft_max_speed(value)

    def set_draft_max_speed(self, value: int) -> None:
        self._replace_draft(max_speed=value)

    @Property(int, notify=draftChanged)
    def draftSensoryRange(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "sensory_range")

    @draftSensoryRange.setter
    def draftSensoryRange(self, value: int) -> None:  # noqa: N802
        self._replace_draft(sensory_range=value)

    @Property(int, notify=draftChanged)
    def draftSensoryAccuracy(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "sensory_accuracy")

    @draftSensoryAccuracy.setter
    def draftSensoryAccuracy(self, value: int) -> None:  # noqa: N802
        self._replace_draft(sensory_accuracy=value)

    @Property(str, notify=draftChanged)
    def draftExplorationMovement(self) -> str:  # noqa: N802
        return _str_value(self._draft_intent, "exploration_movement")

    @draftExplorationMovement.setter
    def draftExplorationMovement(self, value: str) -> None:  # noqa: N802
        if value in {"moore", "von_neumann", "uniform", "gaussian"}:
            self._replace_draft(exploration_movement=value)

    @Property(int, notify=draftChanged)
    def draftGaussianStandardDeviation(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "gaussian_standard_deviation")

    @draftGaussianStandardDeviation.setter
    def draftGaussianStandardDeviation(self, value: int) -> None:  # noqa: N802
        self._replace_draft(gaussian_standard_deviation=value)

    @Property(str, notify=draftChanged)
    def draftResourceGeography(self) -> str:  # noqa: N802
        return _str_value(self._draft_intent, "resource_geography")

    @draftResourceGeography.setter
    def draftResourceGeography(self, value: str) -> None:  # noqa: N802
        if value in {"uniform", "two_patches"}:
            self._replace_draft(resource_geography=value)

    @Property(int, notify=draftChanged)
    def draftResourceAmount(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "resource_generation_amount")

    @draftResourceAmount.setter
    def draftResourceAmount(self, value: int) -> None:  # noqa: N802
        self._replace_draft(resource_generation_amount=value)

    @Property(int, notify=draftChanged)
    def draftResourceDeposits(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "resource_deposits_per_step")

    @draftResourceDeposits.setter
    def draftResourceDeposits(self, value: int) -> None:  # noqa: N802
        self._replace_draft(resource_deposits_per_step=value)

    @Property(int, notify=draftChanged)
    def draftPatch1X(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_1_center_x")

    @draftPatch1X.setter
    def draftPatch1X(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_1_center_x=value)

    @Property(int, notify=draftChanged)
    def draftPatch1Y(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_1_center_y")

    @draftPatch1Y.setter
    def draftPatch1Y(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_1_center_y=value)

    @Property(int, notify=draftChanged)
    def draftPatch1Radius(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_1_radius")

    @draftPatch1Radius.setter
    def draftPatch1Radius(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_1_radius=value)

    @Property(int, notify=draftChanged)
    def draftPatch2X(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_2_center_x")

    @draftPatch2X.setter
    def draftPatch2X(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_2_center_x=value)

    @Property(int, notify=draftChanged)
    def draftPatch2Y(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_2_center_y")

    @draftPatch2Y.setter
    def draftPatch2Y(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_2_center_y=value)

    @Property(int, notify=draftChanged)
    def draftPatch2Radius(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "patch_2_radius")

    @draftPatch2Radius.setter
    def draftPatch2Radius(self, value: int) -> None:  # noqa: N802
        self._replace_draft(patch_2_radius=value)

    @Property(bool, notify=draftChanged)
    def draftMutationEnabled(self) -> bool:  # noqa: N802
        return self._draft_intent is not None and self._draft_intent.mutation_enabled is True

    @draftMutationEnabled.setter
    def draftMutationEnabled(self, value: bool) -> None:  # noqa: N802
        if type(value) is bool:
            self._replace_draft(mutation_enabled=value)

    @Property(int, notify=draftChanged)
    def draftMutationProbability(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "mutation_probability_ppm")

    @draftMutationProbability.setter
    def draftMutationProbability(self, value: int) -> None:  # noqa: N802
        self._replace_draft(mutation_probability_ppm=value)

    @Property(int, notify=draftChanged)
    def draftMutationMaxChange(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "mutation_max_change")

    @draftMutationMaxChange.setter
    def draftMutationMaxChange(self, value: int) -> None:  # noqa: N802
        self._replace_draft(mutation_max_change=value)

    @Property(int, notify=draftChanged)
    def draftRecombinationProbability(self) -> int:  # noqa: N802
        return _int_value(self._draft_intent, "recombination_probability_ppm")

    @draftRecombinationProbability.setter
    def draftRecombinationProbability(self, value: int) -> None:  # noqa: N802
        self._replace_draft(recombination_probability_ppm=value)

    @Property(str, notify=draftChanged)
    def explicitMeaning(self) -> str:  # noqa: N802
        preview = self.preview_manifest()
        if preview is None:
            return "Draft is not scientifically ready."
        return " · ".join(f"{key} = {value}" for key, value in preview.explicit_values)

    @Property(str, notify=draftChanged)
    def derivedMeaning(self) -> str:  # noqa: N802
        preview = self.preview_manifest()
        if preview is None:
            return self._readiness_message()
        return " · ".join(f"{key} = {value}" for key, value in preview.derived_values)

    def is_running(self) -> bool:
        return self._thread is not None

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self.is_running()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(bool, notify=resultsChanged)
    def hasResult(self) -> bool:  # noqa: N802
        return self._result is not None

    @Property(int, notify=resultsChanged)
    def finalPopulation(self) -> int:  # noqa: N802
        if self._revision is None or self._result is None:
            return 0
        view = inspect_reference_study_results(self._revision, self._result)
        if not view.population_observations:
            return 0
        return view.population_observations[-1].population_size

    @Property(bool, notify=worldChanged)
    def hasWorld(self) -> bool:  # noqa: N802
        return self._presentation is not None

    @Property(int, notify=worldChanged)
    def worldWidth(self) -> int:  # noqa: N802
        return 0 if self._presentation is None else self._presentation.frame.world_width

    @Property(int, notify=worldChanged)
    def worldHeight(self) -> int:  # noqa: N802
        return 0 if self._presentation is None else self._presentation.frame.world_height

    @Property(int, notify=worldChanged)
    def worldStep(self) -> int:  # noqa: N802
        return 0 if self._presentation is None else self._presentation.frame.committed_step_index

    @Property(QObject, constant=True)
    def organismModel(self) -> QObject:  # noqa: N802
        return self._organisms

    @Property(QObject, constant=True)
    def resourceModel(self) -> QObject:  # noqa: N802
        return self._resources

    def activate_revision(self, revision: ReferenceStudyRevision) -> None:
        if not isinstance(revision, ReferenceStudyRevision):
            raise TypeError("revision must be a ReferenceStudyRevision.")
        self._revision = revision
        self._draft_intent = revision.intent
        self._normalization_notice = False
        self._clear_result_state()
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status(f"Reference revision {revision.revision_id} is active.")

    def clear(self) -> None:
        if self.is_running():
            raise RuntimeError("Cannot clear Reference state while a run is active.")
        self._revision = None
        self._draft_intent = None
        self._normalization_notice = False
        self._clear_result_state()
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Reference Ecology controls are inactive.")

    def clear_result_state(self) -> None:
        self._clear_result_state()

    @Slot(result=bool)
    def saveChildRevision(self) -> bool:  # noqa: N802
        if not self._require_idle() or self._revision is None or self._draft_intent is None:
            return False
        if not self.is_draft_dirty():
            self._set_status("No semantic draft changes to save.")
            return False
        try:
            child = save_reference_child(
                self._revision,
                draft=self._draft_intent,
                revision_id=f"reference-{uuid.uuid4().hex[:10]}",
            )
        except (TypeError, ValueError) as exc:
            self._set_status(f"Reference Simulation revision is not ready: {exc}")
            return False
        self.activate_revision(child)
        self.revisionCommitted.emit(child)
        self._set_status(
            f"Saved immutable child revision {child.revision_id}; parent unchanged."
        )
        return True

    @Slot()
    def runStudy(self) -> None:  # noqa: N802
        if not self._require_idle() or self._revision is None:
            return
        if self.is_draft_dirty():
            self._set_status("Save the semantic draft as a child revision before running.")
            return
        worker = _ReferenceRunWorker(self._revision)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._run_completed)
        worker.failed.connect(self._run_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(self._worker_finished)
        thread.finished.connect(thread.deleteLater)
        self._worker = worker
        self._thread = thread
        self._set_status(f"Running exact revision {self._revision.revision_id}…")
        self.runningChanged.emit()
        thread.start()

    @Slot(int)
    def selectOrganism(self, organism_id: int) -> None:  # noqa: N802
        if self._revision is None or self._result is None or self._presentation is None:
            return
        self._prepare_world(
            step_index=self._presentation.frame.committed_step_index,
            selected_organism_id=organism_id,
        )

    def _replace_draft(self, **changes: object) -> None:
        if self._draft_intent is None:
            return
        candidate = attrs.evolve(self._draft_intent, **changes)
        normalized = normalize_reference_draft(candidate)
        if normalized == self._draft_intent:
            return
        self._normalization_notice = normalized != candidate
        self._draft_intent = normalized
        self._clear_result_state()
        self.draftChanged.emit()
        self.scientificDraftChanged.emit()
        self._set_status("Unsaved Reference Ecology semantic draft changed.")

    @Slot(object)
    def _run_completed(self, result: object) -> None:
        if not isinstance(result, ReferenceRunResult) or self._revision is None:
            self._set_status("Run returned an unexpected result payload.")
            return
        if (
            result.provenance.study_revision_id != self._revision.revision_id
            or result.provenance.manifest_digest != self._revision.manifest.digest
        ):
            self._set_status("Run provenance no longer matches the active Study revision.")
            return
        self._revision = self._revision.with_run(result.provenance)
        self._result = result
        view = inspect_reference_study_results(self._revision, result)
        if view.spatial_observations:
            self._prepare_world(step_index=view.spatial_observations[-1].step_index)
        else:
            self._presentation = None
            self._organisms.set_items(())
            self._resources.set_items(())
            self.worldChanged.emit()
        self.resultsChanged.emit()
        self.runCompleted.emit(self._revision, result)
        self._set_status(
            f"Run {result.provenance.run_id} complete; Results use recorded evidence."
        )

    @Slot(str)
    def _run_failed(self, message: str) -> None:
        self._set_status(f"Run failed: {message}")

    @Slot()
    def _worker_finished(self) -> None:
        self._worker = None
        self._thread = None
        self.runningChanged.emit()

    def _clear_result_state(self) -> None:
        self._result = None
        self._presentation = None
        self._organisms.set_items(())
        self._resources.set_items(())
        self.resultsChanged.emit()
        self.worldChanged.emit()

    def _readiness_message(self) -> str:
        if self._revision is None or self._draft_intent is None:
            return "No Reference Study draft is active."
        readiness = assess_reference_readiness(
            self._draft_intent, self._revision.evidence_plan
        )
        if readiness.state == "ready":
            return "Draft is scientifically ready."
        return " · ".join(item.message for item in readiness.diagnostics)

    def _prepare_world(
        self,
        *,
        step_index: int,
        selected_organism_id: int | None = None,
    ) -> None:
        if self._revision is None or self._result is None:
            return
        presentation = build_reference_workbench_world_presentation(
            self._revision,
            self._result,
            step_index=step_index,
            selected_organism_id=selected_organism_id,
        )
        self._presentation = presentation
        self._organisms.set_items(presentation.frame.organisms)
        self._resources.set_items(presentation.frame.resources)
        self.worldChanged.emit()

    def _require_idle(self) -> bool:
        if self.is_running():
            self._set_status("A run is already active; wait for it to finish.")
            return False
        return True

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _int_value(intent: ReferenceEcologyIntent | None, field: str) -> int:
    if intent is None:
        return 0
    value = getattr(intent, field)
    return value if type(value) is int else 0


def _str_value(intent: ReferenceEcologyIntent | None, field: str) -> str:
    if intent is None:
        return ""
    value = getattr(intent, field)
    return value if type(value) is str else ""


__all__ = ["ReferenceStudyController"]
