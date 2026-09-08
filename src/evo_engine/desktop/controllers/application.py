"""Native application-state controller over concrete Workbench artifacts.

The controller owns transient product/application state only. Scientific persistence,
validation, authoring semantics, and experiment expansion remain with the existing
concrete Workbench contracts and narrow family-specific authoring controllers.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Literal, cast

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

from evo_engine.desktop.artifacts import (
    STUDY_SECTIONS,
    ArtifactKind,
    ConcreteWorkbenchArtifact,
    StudySection,
    UnsupportedStudyArtifactError,
    artifact_kind,
    artifact_manifest_digest,
    artifact_parent_revision_id,
    artifact_readiness,
    artifact_revision_id,
    artifact_run_count,
    artifact_scenario_identity,
    artifact_scenario_origin,
    artifact_title,
    artifact_type_label,
    can_fork_artifact,
    fork_supported_artifact,
    is_concrete_artifact,
    load_concrete_artifact,
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
    result_matches_artifact,
    result_owner_token,
    serialize_concrete_artifact,
)
from evo_engine.desktop.controllers.evidence import EvidenceAuthoringController
from evo_engine.desktop.controllers.experiment import ExperimentAuthoringController
from evo_engine.desktop.controllers.reference import ReferenceStudyController
from evo_engine.desktop.controllers.simulation import SimulationAuthoringController
from evo_engine.workbench.controlled_locomotion import IncompatibleManifestError
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    ReferenceStudyRevision,
)

Route = Literal["home", "new", "open", "study"]
StatusTone = Literal["neutral", "success", "warning", "error"]

_ROUTES: tuple[Route, ...] = ("home", "new", "open", "study")


class ApplicationController(QObject):
    """Own the native shell state without becoming a scientific persistence schema."""

    routeChanged = Signal()
    sectionChanged = Signal()
    artifactChanged = Signal()
    resultChanged = Signal()
    runPlanChanged = Signal()
    presentationChanged = Signal()
    statusChanged = Signal()
    fileChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._route: Route = "home"
        self._section: StudySection = STUDY_SECTIONS[0]
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._result: object | None = None
        self._run_plan_open = False
        self._presentation_owner = ""
        self._presentation_epoch = 0
        self._file_path: Path | None = None
        self._status = "Create or open a supported Workbench Study."
        self._status_tone: StatusTone = "neutral"
        self._diagnostic_message = ""
        self._diagnostic_remediation = ""

        self._reference = ReferenceStudyController(self)
        self._simulation = SimulationAuthoringController(self._reference, self)
        self._evidence = EvidenceAuthoringController(self)
        self._experiment = ExperimentAuthoringController(self)

        self._reference.scientificDraftChanged.connect(
            self._on_scientific_draft_changed
        )
        self._simulation.scientificDraftChanged.connect(
            self._on_scientific_draft_changed
        )
        self._evidence.scientificDraftChanged.connect(self._on_scientific_draft_changed)
        self._experiment.scientificDraftChanged.connect(
            self._on_scientific_draft_changed
        )
        self._reference.revisionCommitted.connect(self._on_reference_revision_committed)
        self._simulation.revisionCommitted.connect(
            self._on_authoring_revision_committed
        )
        self._evidence.revisionCommitted.connect(self._on_authoring_revision_committed)
        self._experiment.artifactReplaced.connect(self._on_experiment_artifact_replaced)
        self._reference.runCompleted.connect(self._on_reference_run_completed)
        self._reference.runningChanged.connect(self.artifactChanged.emit)

    @Property(QObject, constant=True)
    def referenceController(self) -> QObject:  # noqa: N802
        return self._reference

    @Property(QObject, constant=True)
    def simulationController(self) -> QObject:  # noqa: N802
        return self._simulation

    @Property(QObject, constant=True)
    def evidenceController(self) -> QObject:  # noqa: N802
        return self._evidence

    @Property(QObject, constant=True)
    def experimentController(self) -> QObject:  # noqa: N802
        return self._experiment

    @Property(str, notify=routeChanged)
    def route(self) -> str:
        return self._route

    @Property(bool, notify=artifactChanged)
    def hasStudy(self) -> bool:  # noqa: N802
        return self._artifact is not None

    @Property(str, notify=sectionChanged)
    def studySection(self) -> str:  # noqa: N802
        return self._section

    @Property(str, notify=artifactChanged)
    def artifactKind(self) -> str:  # noqa: N802
        return "" if self._artifact is None else artifact_kind(self._artifact)

    @Property(str, notify=artifactChanged)
    def studyTitle(self) -> str:  # noqa: N802
        return "" if self._artifact is None else artifact_title(self._artifact)

    @Property(str, notify=artifactChanged)
    def studyTypeLabel(self) -> str:  # noqa: N802
        return "" if self._artifact is None else artifact_type_label(self._artifact)

    @Property(str, notify=artifactChanged)
    def revisionId(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_revision_id(self._artifact) or ""

    @Property(str, notify=artifactChanged)
    def parentRevisionId(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_parent_revision_id(self._artifact) or ""

    @Property(str, notify=artifactChanged)
    def manifestDigest(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_manifest_digest(self._artifact) or ""

    @Property(str, notify=artifactChanged)
    def scenarioOrigin(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_scenario_origin(self._artifact) or ""

    @Property(str, notify=artifactChanged)
    def scenarioIdentity(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_scenario_identity(self._artifact) or ""

    @Property(str, notify=artifactChanged)
    def readinessState(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        return artifact_readiness(self._artifact).state

    @Property(str, notify=artifactChanged)
    def readinessMessage(self) -> str:  # noqa: N802
        if self._artifact is None:
            return ""
        readiness = artifact_readiness(self._artifact)
        if not readiness.diagnostics:
            return "Ready for its currently supported Workbench semantics."
        return " · ".join(item.message for item in readiness.diagnostics)

    @Property(int, notify=artifactChanged)
    def runReferenceCount(self) -> int:  # noqa: N802
        if self._artifact is None:
            return 0
        count = artifact_run_count(self._artifact)
        return 0 if count is None else count

    @Property(bool, notify=artifactChanged)
    def canFork(self) -> bool:  # noqa: N802
        return self._artifact is not None and can_fork_artifact(self._artifact)

    def can_run(self) -> bool:
        """Return whether retained native Reference execution owns exact saved science."""
        if not isinstance(self._artifact, ReferenceStudyRevision):
            return False
        return (
            artifact_readiness(self._artifact).state == "ready"
            and not self._reference.is_draft_dirty()
            and not self._evidence.is_draft_dirty()
            and not self._reference.is_running()
        )

    @Property(bool, notify=artifactChanged)
    def canRun(self) -> bool:  # noqa: N802
        return self.can_run()

    @Property(bool, notify=artifactChanged)
    def running(self) -> bool:
        return self._reference.is_running()

    @Property(bool, notify=resultChanged)
    def hasResult(self) -> bool:  # noqa: N802
        return self._result is not None

    @Property(bool, notify=runPlanChanged)
    def runPlanOpen(self) -> bool:  # noqa: N802
        return self._run_plan_open

    @Property(str, notify=presentationChanged)
    def presentationOwner(self) -> str:  # noqa: N802
        return self._presentation_owner

    @Property(int, notify=presentationChanged)
    def presentationEpoch(self) -> int:  # noqa: N802
        return self._presentation_epoch

    @Property(bool, notify=fileChanged)
    def hasFileLocation(self) -> bool:  # noqa: N802
        return self._file_path is not None

    @Property(str, notify=fileChanged)
    def fileLocation(self) -> str:  # noqa: N802
        return "" if self._file_path is None else str(self._file_path)

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(str, notify=statusChanged)
    def statusTone(self) -> str:  # noqa: N802
        return self._status_tone

    @Property(str, notify=statusChanged)
    def diagnosticMessage(self) -> str:  # noqa: N802
        return self._diagnostic_message

    @Property(str, notify=statusChanged)
    def diagnosticRemediation(self) -> str:  # noqa: N802
        return self._diagnostic_remediation

    @Slot()
    def goHome(self) -> None:  # noqa: N802
        if not self._require_idle():
            return
        self._clear_active_context()
        self._set_route("home")
        self._set_status("Returned Home.", tone="neutral")

    @Slot()
    def showNewStudy(self) -> None:  # noqa: N802
        if not self._require_idle():
            return
        self._set_route("new")
        self._set_status("Choose one supported concrete Study family.", tone="neutral")

    @Slot()
    def showOpenStudy(self) -> None:  # noqa: N802
        if not self._require_idle():
            return
        if self._artifact is None:
            self._set_route("open")
        self._set_status("Choose a supported Workbench JSON artifact.", tone="neutral")

    @Slot(str, result=bool)
    def createStudy(self, kind: str) -> bool:  # noqa: N802
        if not self._require_idle():
            return False
        try:
            artifact = _new_artifact(cast(ArtifactKind, kind))
        except (TypeError, ValueError) as exc:
            self._set_status(f"New Study failed: {exc}", tone="error")
            return False
        self._activate_artifact(artifact, file_path=None, reset_section=True)
        self._set_status(f"Created {artifact_title(artifact)}.", tone="success")
        return True

    @Slot(str, result=bool)
    def openStudy(self, location: str) -> bool:  # noqa: N802
        if not self._require_idle():
            return False
        try:
            path = _path_from_location(location)
            artifact = load_concrete_artifact(path.read_text(encoding="utf-8"))
        except IncompatibleManifestError as exc:
            self._set_exact_reproduction_failure(exc)
            return False
        except (OSError, TypeError, ValueError, UnsupportedStudyArtifactError) as exc:
            self._set_status(f"Open failed: {exc}", tone="error")
            return False
        self._activate_artifact(artifact, file_path=path, reset_section=True)
        self._set_status(
            f"Opened exact {artifact_title(artifact)} artifact.", tone="success"
        )
        return True

    @Slot(str, result=bool)
    def saveStudy(self, location: str) -> bool:  # noqa: N802
        if self._artifact is None:
            self._set_status("Open or create a Study before saving.", tone="warning")
            return False
        try:
            path = _path_from_location(location)
            path.write_text(
                serialize_concrete_artifact(self._artifact), encoding="utf-8"
            )
        except (OSError, TypeError, ValueError) as exc:
            self._set_status(f"Save failed: {exc}", tone="error")
            return False
        self._set_file_path(path)
        self._set_status(f"Saved exact artifact to {path.name}.", tone="success")
        return True

    @Slot(result=bool)
    def saveToCurrentLocation(self) -> bool:  # noqa: N802
        if self._file_path is None:
            self._set_status("Choose Save As before using Save.", tone="warning")
            return False
        return self.saveStudy(str(self._file_path))

    @Slot(str, result=bool)
    def selectSection(self, section: str) -> bool:  # noqa: N802
        if self._artifact is None:
            self._set_status(
                "Open or create a Study before choosing a section.", tone="warning"
            )
            return False
        if section not in STUDY_SECTIONS:
            self._set_status(f"Unknown Study section: {section}", tone="error")
            return False
        resolved = cast(StudySection, section)
        if resolved == self._section:
            return True
        self._section = resolved
        self.sectionChanged.emit()
        return True

    @Slot(result=bool)
    def forkStudy(self) -> bool:  # noqa: N802
        if not self._require_idle() or self._artifact is None:
            return False
        parent = self._artifact
        try:
            child = fork_supported_artifact(
                parent, revision_id=_new_revision_id("b3-sensitivity")
            )
        except (TypeError, ValueError) as exc:
            self._set_status(f"Fork unavailable: {exc}", tone="warning")
            return False
        self._activate_artifact(
            child,
            file_path=None,
            reset_section=False,
            diff_parent=parent,
        )
        self._set_status(
            "Created the supported B3 radius-2 sensitivity fork; validated radius-1 "
            "scenario identity was not inherited.",
            tone="success",
        )
        return True

    @Slot()
    def runStudy(self) -> None:  # noqa: N802
        if not isinstance(self._artifact, ReferenceStudyRevision):
            self._set_status(
                "Native execution for this Study family arrives in the "
                "execution/Results milestone.",
                tone="neutral",
            )
            return
        if not self.can_run():
            self._set_status(
                "Save Simulation and Evidence drafts and keep the exact Reference Study "
                "scientifically ready before Run.",
                tone="warning",
            )
            return
        self._run_plan_open = False
        self.runPlanChanged.emit()
        self._reference.runStudy()

    def bind_result(self, result: object) -> bool:
        if self._artifact is None or not result_matches_artifact(
            self._artifact, result
        ):
            self._set_status(
                "Result rejected because it belongs to a different scientific owner.",
                tone="error",
            )
            return False
        self._result = result
        self._set_presentation_owner(result_owner_token(self._artifact, result) or "")
        self.resultChanged.emit()
        return True

    def set_run_plan_open(self, value: bool) -> None:
        if type(value) is not bool:
            raise TypeError("value must be a bool.")
        if value == self._run_plan_open:
            return
        self._run_plan_open = value
        self.runPlanChanged.emit()

    def _activate_artifact(
        self,
        artifact: ConcreteWorkbenchArtifact,
        *,
        file_path: Path | None,
        reset_section: bool,
        reference_already_active: bool = False,
        diff_parent: ConcreteWorkbenchArtifact | None = None,
    ) -> None:
        previous_kind = (
            None if self._artifact is None else artifact_kind(self._artifact)
        )
        self._clear_result_and_presentation()
        self._run_plan_open = False
        self.runPlanChanged.emit()
        self._artifact = artifact
        self._set_file_path(file_path)
        if reset_section or previous_kind != artifact_kind(artifact):
            self._section = STUDY_SECTIONS[0]
            self.sectionChanged.emit()

        if isinstance(artifact, ReferenceStudyRevision):
            if not reference_already_active:
                self._reference.activate_revision(artifact)
        elif self._reference.is_active():
            self._reference.clear()

        self._simulation.activate_artifact(artifact, diff_parent=diff_parent)
        self._evidence.activate_artifact(artifact)
        self._experiment.activate_artifact(artifact)
        self._set_route("study")
        self._clear_diagnostic()
        self.artifactChanged.emit()

    def _clear_active_context(self) -> None:
        self._artifact = None
        self._result = None
        self._run_plan_open = False
        self._section = STUDY_SECTIONS[0]
        self._set_file_path(None)
        self._set_presentation_owner("")
        if self._reference.is_active():
            self._reference.clear()
        self._simulation.clear()
        self._evidence.clear()
        self._experiment.clear()
        self.sectionChanged.emit()
        self.artifactChanged.emit()
        self.resultChanged.emit()
        self.runPlanChanged.emit()
        self._clear_diagnostic()

    def _clear_result_and_presentation(self) -> None:
        self._result = None
        self.resultChanged.emit()
        self._set_presentation_owner("")

    @Slot()
    def _on_scientific_draft_changed(self) -> None:
        self._result = None
        self._run_plan_open = False
        self.resultChanged.emit()
        self.runPlanChanged.emit()
        self._set_presentation_owner("")
        self.artifactChanged.emit()

    @Slot(object)
    def _on_reference_revision_committed(self, revision: object) -> None:
        if not isinstance(revision, ReferenceStudyRevision):
            self._set_status(
                "Reference controller returned an invalid revision.", tone="error"
            )
            return
        parent = self._artifact
        self._activate_artifact(
            revision,
            file_path=None,
            reset_section=False,
            reference_already_active=True,
            diff_parent=parent,
        )

    @Slot(object)
    def _on_authoring_revision_committed(self, revision: object) -> None:
        if not is_concrete_artifact(revision):
            self._set_status(
                "Authoring controller returned an invalid artifact.", tone="error"
            )
            return
        parent = self._artifact
        self._activate_artifact(
            revision,
            file_path=None,
            reset_section=False,
            diff_parent=parent,
        )
        self._set_status("Saved a new immutable scientific revision.", tone="success")

    @Slot(object)
    def _on_experiment_artifact_replaced(self, artifact: object) -> None:
        if not is_concrete_artifact(artifact):
            self._set_status(
                "Experiment controller returned an invalid artifact.", tone="error"
            )
            return
        self._activate_artifact(artifact, file_path=None, reset_section=False)
        self._set_status(
            "Applied the exact concrete experiment definition.", tone="success"
        )

    @Slot(object, object)
    def _on_reference_run_completed(self, revision: object, result: object) -> None:
        if not isinstance(revision, ReferenceStudyRevision) or not isinstance(
            result, ReferenceRunResult
        ):
            self._set_status(
                "Reference run returned invalid application payloads.", tone="error"
            )
            return
        active = self._artifact
        if not isinstance(active, ReferenceStudyRevision):
            self._set_status(
                "Reference result is stale because another Study is active.",
                tone="error",
            )
            return
        if (
            revision.revision_id != active.revision_id
            or revision.manifest.digest != active.manifest.digest
        ):
            self._set_status(
                "Reference result is stale for the active scientific owner.",
                tone="error",
            )
            return
        self._artifact = revision
        self._simulation.activate_artifact(revision)
        self._evidence.activate_artifact(revision)
        self._experiment.activate_artifact(revision)
        self.artifactChanged.emit()
        if self.bind_result(result):
            self._set_status(
                f"Run {result.provenance.run_id} is bound to the exact active revision.",
                tone="success",
            )

    def _set_presentation_owner(self, owner: str) -> None:
        if owner == self._presentation_owner:
            if not owner:
                self._presentation_epoch += 1
                self.presentationChanged.emit()
            return
        self._presentation_owner = owner
        self._presentation_epoch += 1
        self.presentationChanged.emit()

    def _set_route(self, route: Route) -> None:
        if route not in _ROUTES:
            raise ValueError(f"Unsupported route: {route!r}.")
        if route == self._route:
            return
        self._route = route
        self.routeChanged.emit()

    def _set_file_path(self, path: Path | None) -> None:
        if path == self._file_path:
            return
        self._file_path = path
        self.fileChanged.emit()

    def _set_exact_reproduction_failure(self, exc: IncompatibleManifestError) -> None:
        diagnostic = exc.diagnostic
        self._diagnostic_message = diagnostic.message
        self._diagnostic_remediation = diagnostic.remediation or ""
        self._set_status(
            "Exact reproduction unavailable.", tone="error", preserve_diagnostic=True
        )

    def _clear_diagnostic(self) -> None:
        if not self._diagnostic_message and not self._diagnostic_remediation:
            return
        self._diagnostic_message = ""
        self._diagnostic_remediation = ""
        self.statusChanged.emit()

    def _set_status(
        self,
        value: str,
        *,
        tone: StatusTone,
        preserve_diagnostic: bool = False,
    ) -> None:
        if not preserve_diagnostic:
            self._diagnostic_message = ""
            self._diagnostic_remediation = ""
        self._status = value
        self._status_tone = tone
        self.statusChanged.emit()

    def _require_idle(self) -> bool:
        if self._reference.is_running():
            self._set_status(
                "A Reference run is active; wait for it to finish.", tone="warning"
            )
            return False
        return True


def _new_artifact(kind: ArtifactKind) -> ConcreteWorkbenchArtifact:
    if kind == "controlled-run":
        return new_controlled_run(revision_id=_new_revision_id("controlled"))
    if kind == "max-speed-sweep":
        return new_max_speed_sweep()
    if kind == "environment-selection-comparison":
        return new_environment_selection_comparison()
    if kind == "b3-flagship":
        return new_b3_flagship(revision_id=_new_revision_id("b3"))
    if kind == "reference-ecology":
        return new_reference_ecology(revision_id=_new_revision_id("reference"))
    raise ValueError(f"Unsupported Study family: {kind!r}.")


def _new_revision_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _path_from_location(location: str) -> Path:
    if type(location) is not str or not location.strip():
        raise ValueError("A non-empty Study file location is required.")
    if location.startswith("file:"):
        local = QUrl(location).toLocalFile()
        if not local:
            raise ValueError("Study file URL is not a local file.")
        return Path(local)
    return Path(location)


__all__ = ["ApplicationController", "Route", "StatusTone"]
