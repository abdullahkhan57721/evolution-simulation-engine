"""Native Evidence authoring over existing concrete Workbench evidence plans."""

from __future__ import annotations

import uuid

from PySide6.QtCore import Property, QObject, Signal, Slot

from evo_engine.desktop.artifacts import ConcreteWorkbenchArtifact
from evo_engine.desktop.models.authoring import EvidenceItem, EvidenceOptionModel
from evo_engine.workbench import (
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EvidencePlan,
    MaxSpeedSweepDefinition,
    ReferenceEvidencePlan,
    ReferenceStudyRevision,
    StudyRevision,
    assess_readiness,
    assess_reference_readiness,
)
from evo_engine.workbench.evidence_authoring import (
    evidence_advisories_for_artifact,
    evidence_options,
    make_editable_evidence_plan,
    requested_evidence_ids,
    save_evidence_child,
)


class EvidenceAuthoringController(QObject):
    """Own only transient native evidence selection for the active concrete artifact."""

    activeChanged = Signal()
    draftChanged = Signal()
    scientificDraftChanged = Signal()
    revisionCommitted = Signal(object)
    statusChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._requested: tuple[str, ...] = ()
        self._options = EvidenceOptionModel()
        self._status = "Evidence authoring is inactive."

    @Property(QObject, constant=True)
    def optionModel(self) -> QObject:  # noqa: N802
        return self._options

    @Property(bool, notify=activeChanged)
    def active(self) -> bool:
        return self._artifact is not None

    @Property(bool, notify=activeChanged)
    def editable(self) -> bool:
        return isinstance(self._artifact, (StudyRevision, ReferenceStudyRevision))

    def is_draft_dirty(self) -> bool:
        """Return scientific draft ownership for Python controller use."""
        artifact = self._artifact
        return (
            isinstance(artifact, (StudyRevision, ReferenceStudyRevision))
            and self._requested != artifact.evidence_plan.requested
        )

    def draft_plan(self) -> EvidencePlan | ReferenceEvidencePlan | None:
        """Return the concrete transient evidence plan for application Run binding."""
        artifact = self._artifact
        if isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
            return make_editable_evidence_plan(artifact, self._requested)
        return None

    @Property(bool, notify=draftChanged)
    def draftDirty(self) -> bool:  # noqa: N802
        return self.is_draft_dirty()

    @Property(bool, notify=draftChanged)
    def draftReady(self) -> bool:  # noqa: N802
        return self._readiness_state() == "ready"

    @Property(str, notify=draftChanged)
    def readinessMessage(self) -> str:  # noqa: N802
        return self._readiness_message()

    def _readiness_message(self) -> str:
        artifact = self._artifact
        if isinstance(artifact, StudyRevision):
            plan = make_editable_evidence_plan(artifact, self._requested)
            assert isinstance(plan, EvidencePlan)
            readiness = assess_readiness(artifact.intent, plan)
        elif isinstance(artifact, ReferenceStudyRevision):
            plan = make_editable_evidence_plan(artifact, self._requested)
            assert isinstance(plan, ReferenceEvidencePlan)
            readiness = assess_reference_readiness(artifact.intent, plan)
        else:
            return "Required evidence is fixed by this scientific design."
        if not readiness.diagnostics:
            return "Ready"
        return " · ".join(item.message for item in readiness.diagnostics)

    @Property(str, notify=draftChanged)
    def advisoryMessage(self) -> str:  # noqa: N802
        artifact = self._artifact
        if not isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
            return ""
        plan = make_editable_evidence_plan(artifact, self._requested)
        advisories = evidence_advisories_for_artifact(artifact, plan=plan)
        return " · ".join(item.message for item in advisories)

    @Property(str, notify=draftChanged)
    def missingEvidenceMessage(self) -> str:  # noqa: N802
        artifact = self._artifact
        if artifact is None:
            return ""
        missing = [
            option.enables
            for option in evidence_options(artifact)
            if option.evidence_id not in self._requested and not option.required
        ]
        if not missing:
            return ""
        return (
            "Not recorded in the current draft: "
            + "; ".join(missing)
            + ". Unrecorded evidence cannot be reconstructed from Results."
        )

    @Property(str, notify=activeChanged)
    def lockMessage(self) -> str:  # noqa: N802
        artifact = self._artifact
        if isinstance(artifact, B3StudyRevision):
            return "This evidence set is part of the curated B3 scientific design."
        if isinstance(
            artifact,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            return (
                "This experiment requires the displayed evidence for its authoritative "
                "analysis; required streams cannot be removed."
            )
        return ""

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    def activate_artifact(self, artifact: ConcreteWorkbenchArtifact) -> None:
        self._artifact = artifact
        self._requested = requested_evidence_ids(artifact)
        self._refresh_model()
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Evidence follows the active exact Workbench artifact.")

    def clear(self) -> None:
        self._artifact = None
        self._requested = ()
        self._options.set_items(())
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Evidence authoring is inactive.")

    @Slot(str, bool)
    def setEvidenceSelected(self, evidence_id: str, selected: bool) -> None:  # noqa: N802
        artifact = self._artifact
        if not isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
            return
        if type(evidence_id) is not str or type(selected) is not bool:
            return
        options = evidence_options(artifact)
        option = next(
            (item for item in options if item.evidence_id == evidence_id), None
        )
        if option is None or option.required:
            return
        selected_ids = set(self._requested)
        if selected:
            selected_ids.add(evidence_id)
        else:
            selected_ids.discard(evidence_id)
        resolved = tuple(
            item.evidence_id for item in options if item.evidence_id in selected_ids
        )
        if resolved == self._requested:
            return
        self._requested = resolved
        self._refresh_model()
        self.draftChanged.emit()
        self.scientificDraftChanged.emit()
        self._set_status("Unsaved Evidence draft changed.")

    @Slot(result=bool)
    def saveEvidenceChildRevision(self) -> bool:  # noqa: N802
        artifact = self._artifact
        if not isinstance(artifact, (StudyRevision, ReferenceStudyRevision)):
            self._set_status("Evidence is locked for this Study family.")
            return False
        if not self.is_draft_dirty():
            self._set_status("Evidence matches the current immutable revision.")
            return False
        if self._readiness_state() != "ready":
            self._set_status(self._readiness_message())
            return False
        prefix = "controlled" if isinstance(artifact, StudyRevision) else "reference"
        child = save_evidence_child(
            artifact,
            requested=self._requested,
            revision_id=f"{prefix}-{uuid.uuid4().hex[:10]}",
        )
        self.revisionCommitted.emit(child)
        return True

    def _readiness_state(self) -> str:
        artifact = self._artifact
        if isinstance(artifact, StudyRevision):
            plan = make_editable_evidence_plan(artifact, self._requested)
            assert isinstance(plan, EvidencePlan)
            return assess_readiness(artifact.intent, plan).state
        if isinstance(artifact, ReferenceStudyRevision):
            plan = make_editable_evidence_plan(artifact, self._requested)
            assert isinstance(plan, ReferenceEvidencePlan)
            return assess_reference_readiness(artifact.intent, plan).state
        return "ready" if artifact is not None else ""

    def _refresh_model(self) -> None:
        artifact = self._artifact
        if artifact is None:
            self._options.set_items(())
            return
        editable = isinstance(artifact, (StudyRevision, ReferenceStudyRevision))
        self._options.set_items(
            tuple(
                EvidenceItem(
                    evidence_id=option.evidence_id,
                    label=option.label,
                    meaning=option.meaning,
                    enables=option.enables,
                    selected=option.evidence_id in self._requested,
                    required=option.required,
                    editable=editable and not option.required,
                )
                for option in evidence_options(artifact)
            )
        )

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


__all__ = ["EvidenceAuthoringController"]
