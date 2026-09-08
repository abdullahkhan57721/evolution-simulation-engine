"""Thin Qt controller for the Q0 Reference Ecology vertical slice."""

# PySide's Property setter decorator is a runtime descriptor but its stubs currently
# report the paired getter/setter declarations as a redeclaration.
# pyright: reportRedeclaration=false

from __future__ import annotations

import uuid
from pathlib import Path

import attrs
from PySide6.QtCore import Property, QObject, QThread, QUrl, Signal, Slot

from evo_engine.desktop.models import WorldOrganismModel, WorldResourceModel
from evo_engine.presentation.workbench import (
    WorkbenchWorldPresentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID,
    SPATIAL_EVIDENCE_ID,
    ReferenceEcologyIntent,
    ReferenceEvidencePlan,
    assess_reference_readiness,
    default_reference_ecology_intent,
    resolve_reference_ecology,
)
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    ReferenceStudyRevision,
    create_reference_study_revision,
    fork_reference_study_revision,
    run_reference_study_revision,
)
from evo_engine.workbench.results import inspect_reference_study_results

_Q0_EVIDENCE_PLAN = ReferenceEvidencePlan(
    requested=(POPULATION_EVIDENCE_ID, SPATIAL_EVIDENCE_ID)
)


class _ReferenceRunWorker(QObject):
    """Run the existing synchronous Workbench runner outside the GUI thread."""

    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, revision: ReferenceStudyRevision) -> None:
        super().__init__()
        self._revision = revision

    @Slot()
    def run(self) -> None:
        """Execute one exact saved revision and return its authoritative artifacts."""
        try:
            result = run_reference_study_revision(self._revision)
        except Exception as exc:  # boundary converts worker failure into UI state
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.completed.emit(result)


class StudyController(QObject):
    """Expose a scalar Qt API while keeping Workbench objects private to Python."""

    studyChanged = Signal()
    draftChanged = Signal()
    runningChanged = Signal()
    resultsChanged = Signal()
    worldChanged = Signal()
    statusChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._revision: ReferenceStudyRevision | None = None
        self._draft_intent: ReferenceEcologyIntent | None = None
        self._result: ReferenceRunResult | None = None
        self._presentation: WorkbenchWorldPresentation | None = None
        self._organisms = WorldOrganismModel()
        self._resources = WorldResourceModel()
        self._thread: QThread | None = None
        self._worker: _ReferenceRunWorker | None = None
        self._status = "Create or open a Reference Ecology Study."

    @Property(bool, notify=studyChanged)
    def hasStudy(self) -> bool:  # noqa: N802
        return self._revision is not None

    @Property(str, notify=studyChanged)
    def revisionId(self) -> str:  # noqa: N802
        return "" if self._revision is None else self._revision.revision_id

    @Property(str, notify=studyChanged)
    def parentRevisionId(self) -> str:  # noqa: N802
        if self._revision is None or self._revision.parent_revision_id is None:
            return ""
        return self._revision.parent_revision_id

    @Property(str, notify=studyChanged)
    def manifestDigest(self) -> str:  # noqa: N802
        return "" if self._revision is None else self._revision.manifest.digest

    @Property(int, notify=draftChanged)
    def draftMaxSpeed(self) -> int:  # noqa: N802
        if self._draft_intent is None or self._draft_intent.max_speed is None:
            return 0
        return self._draft_intent.max_speed

    @draftMaxSpeed.setter
    def draftMaxSpeed(self, value: int) -> None:  # noqa: N802
        self.set_draft_max_speed(value)

    def set_draft_max_speed(self, value: int) -> None:
        """Apply one transient semantic edit without mutating the active revision."""
        if self._draft_intent is None or type(value) is not int:
            return
        if self._draft_intent.max_speed == value:
            return
        self._draft_intent = attrs.evolve(self._draft_intent, max_speed=value)
        self._clear_result_state()
        self.draftChanged.emit()
        self.statusChanged.emit()

    @Property(bool, notify=draftChanged)
    def draftDirty(self) -> bool:  # noqa: N802
        return (
            self._revision is not None
            and self._draft_intent is not None
            and self._draft_intent != self._revision.intent
        )

    @Property(bool, notify=draftChanged)
    def draftReady(self) -> bool:  # noqa: N802
        if self._draft_intent is None or self._revision is None:
            return False
        readiness = assess_reference_readiness(
            self._draft_intent, self._revision.evidence_plan
        )
        return readiness.state == "ready"

    @Property(str, notify=draftChanged)
    def explicitMeaning(self) -> str:  # noqa: N802
        preview = self._preview_manifest()
        if preview is None:
            return "Draft is not scientifically ready."
        return " · ".join(f"{key} = {value}" for key, value in preview.explicit_values)

    @Property(str, notify=draftChanged)
    def derivedMeaning(self) -> str:  # noqa: N802
        preview = self._preview_manifest()
        if preview is None:
            return self._readiness_message()
        return " · ".join(f"{key} = {value}" for key, value in preview.derived_values)

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._thread is not None

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

    @Property(int, notify=worldChanged)
    def worldWidth(self) -> int:  # noqa: N802
        return 0 if self._presentation is None else self._presentation.frame.world_width

    @Property(int, notify=worldChanged)
    def worldHeight(self) -> int:  # noqa: N802
        return (
            0 if self._presentation is None else self._presentation.frame.world_height
        )

    @Property(int, notify=worldChanged)
    def worldStep(self) -> int:  # noqa: N802
        if self._presentation is None:
            return 0
        return self._presentation.frame.committed_step_index

    @Property(QObject, constant=True)
    def organismModel(self) -> QObject:  # noqa: N802
        return self._organisms

    @Property(QObject, constant=True)
    def resourceModel(self) -> QObject:  # noqa: N802
        return self._resources

    @Slot()
    def createStudy(self) -> None:  # noqa: N802
        """Create the bounded Q0 Study through the existing WB4 constructor."""
        if not self._require_idle():
            return
        intent = attrs.evolve(
            default_reference_ecology_intent(),
            width=12,
            height=12,
            founder_population=8,
            horizon=12,
            seed=1729,
        )
        revision = create_reference_study_revision(
            revision_id=f"reference-{uuid.uuid4().hex[:10]}",
            intent=intent,
            evidence_plan=_Q0_EVIDENCE_PLAN,
        )
        self._activate_revision(revision)
        self._set_status("Reference Ecology Study created from Workbench semantics.")

    @Slot(str, result=bool)
    def openStudy(self, location: str) -> bool:  # noqa: N802
        """Open an exact WB4 Study snapshot without re-resolving its manifest."""
        if not self._require_idle():
            return False
        try:
            path = _path_from_location(location)
            revision = ReferenceStudyRevision.from_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, TypeError, ValueError) as exc:
            self._set_status(f"Open failed: {exc}")
            return False
        self._activate_revision(revision)
        self._set_status(f"Opened exact Study revision {revision.revision_id}.")
        return True

    @Slot(str, result=bool)
    def saveStudy(self, location: str) -> bool:  # noqa: N802
        """Persist the active exact revision, never the transient QML draft."""
        if self._revision is None:
            self._set_status("Create or open a Study before saving.")
            return False
        try:
            path = _path_from_location(location)
            path.write_text(self._revision.to_json(), encoding="utf-8")
        except (OSError, TypeError, ValueError) as exc:
            self._set_status(f"Save failed: {exc}")
            return False
        self._set_status(f"Saved exact revision {self._revision.revision_id}.")
        return True

    @Slot(result=bool)
    def saveChildRevision(self) -> bool:  # noqa: N802
        """Commit the draft only by creating an immutable Workbench child revision."""
        if (
            not self._require_idle()
            or self._revision is None
            or self._draft_intent is None
        ):
            return False
        if not self.draftDirty:
            self._set_status("No semantic draft changes to save.")
            return False
        readiness = assess_reference_readiness(
            self._draft_intent, self._revision.evidence_plan
        )
        if readiness.state != "ready":
            self._set_status(self._readiness_message())
            return False
        parent = self._revision
        child = fork_reference_study_revision(
            parent,
            revision_id=f"reference-{uuid.uuid4().hex[:10]}",
            intent=self._draft_intent,
        )
        self._activate_revision(child)
        self._set_status(
            f"Saved immutable child revision {child.revision_id}; parent unchanged."
        )
        return True

    @Slot()
    def runStudy(self) -> None:  # noqa: N802
        """Execute the exact active revision on a worker QThread."""
        if not self._require_idle() or self._revision is None:
            return
        if self.draftDirty:
            self._set_status(
                "Save the semantic draft as a child revision before running."
            )
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
        """Change renderer selection without changing scientific identity."""
        if self._revision is None or self._result is None or self._presentation is None:
            return
        self._prepare_world(
            step_index=self._presentation.frame.committed_step_index,
            selected_organism_id=organism_id,
        )

    @Slot(object)
    def _run_completed(self, result: object) -> None:
        if not isinstance(result, ReferenceRunResult) or self._revision is None:
            self._set_status("Run returned an unexpected result payload.")
            return
        if (
            result.provenance.study_revision_id != self._revision.revision_id
            or result.provenance.manifest_digest != self._revision.manifest.digest
        ):
            self._set_status(
                "Run provenance no longer matches the active Study revision."
            )
            return
        self._revision = self._revision.with_run(result.provenance)
        self._result = result
        view = inspect_reference_study_results(self._revision, result)
        if view.spatial_observations:
            self._prepare_world(step_index=view.spatial_observations[-1].step_index)
        self.studyChanged.emit()
        self.resultsChanged.emit()
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

    def _activate_revision(self, revision: ReferenceStudyRevision) -> None:
        self._revision = revision
        self._draft_intent = revision.intent
        self._clear_result_state()
        self.studyChanged.emit()
        self.draftChanged.emit()

    def _clear_result_state(self) -> None:
        self._result = None
        self._presentation = None
        self._organisms.set_items(())
        self._resources.set_items(())
        self.resultsChanged.emit()
        self.worldChanged.emit()

    def _preview_manifest(self):
        if self._revision is None or self._draft_intent is None:
            return None
        readiness = assess_reference_readiness(
            self._draft_intent, self._revision.evidence_plan
        )
        if readiness.state != "ready":
            return None
        return resolve_reference_ecology(
            self._draft_intent, self._revision.evidence_plan
        )

    def _readiness_message(self) -> str:
        if self._revision is None or self._draft_intent is None:
            return "No Study draft is active."
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
        if self.running:
            self._set_status("A run is already active; wait for it to finish.")
            return False
        return True

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _path_from_location(location: str) -> Path:
    if type(location) is not str or not location.strip():
        raise ValueError("A non-empty Study file location is required.")
    if location.startswith("file:"):
        local = QUrl(location).toLocalFile()
        if not local:
            raise ValueError("Study file URL is not a local file.")
        return Path(local)
    return Path(location)


__all__ = ["StudyController"]
