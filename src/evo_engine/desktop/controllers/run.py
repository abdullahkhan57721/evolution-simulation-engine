"""Native Run Plan and worker-thread execution for concrete Workbench artifacts."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, QThread, Signal, Slot

from evo_engine.desktop.artifacts import ConcreteWorkbenchArtifact, artifact_kind
from evo_engine.desktop.models.authoring import (
    ExperimentRunItem,
    ExperimentRunModel,
    MeaningItem,
    MeaningListModel,
)
from evo_engine.workbench import (
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)
from evo_engine.workbench.controlled_locomotion import SEED_SLOT
from evo_engine.workbench.evidence_authoring import (
    evidence_advisories_for_artifact,
    evidence_options,
    requested_evidence_ids,
)
from evo_engine.workbench.execution import execute_artifact
from evo_engine.workbench.experiment_authoring import (
    b3_case_counts,
    environment_run_rows,
    max_speed_run_rows,
)
from evo_engine.workbench.reference_ecology import (
    HORIZON_SLOT as REFERENCE_HORIZON_SLOT,
)
from evo_engine.workbench.reference_ecology import SEED_SLOT as REFERENCE_SEED_SLOT


class _RunWorker(QObject):
    """Execute one exact supported Workbench artifact away from the GUI thread."""

    completed = Signal(object, object, object)
    failed = Signal(object, str)

    def __init__(self, artifact: ConcreteWorkbenchArtifact) -> None:
        super().__init__()
        self._artifact = artifact

    @Slot()
    def run(self) -> None:
        try:
            updated, result = execute_artifact(self._artifact)
        except Exception as exc:  # application boundary converts failure into UI state
            self.failed.emit(self._artifact, f"{type(exc).__name__}: {exc}")
            return
        self.completed.emit(self._artifact, updated, result)


class RunController(QObject):
    """Own transient Run Plan state and one narrow synchronous-runner Qt adapter."""

    planChanged = Signal()
    runningChanged = Signal()
    completed = Signal(object, object, object)
    failed = Signal(object, str)
    statusChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._plan_open = False
        self._binding_notice = ""
        self._advisory = ""
        self._execute_label = "Run"
        self._summary = MeaningListModel()
        self._evidence = MeaningListModel()
        self._runs = ExperimentRunModel()
        self._thread: QThread | None = None
        self._worker: _RunWorker | None = None
        self._status = "No Run Plan is open."

    @Property(QObject, constant=True)
    def summaryModel(self) -> QObject:  # noqa: N802
        return self._summary

    @Property(QObject, constant=True)
    def evidenceModel(self) -> QObject:  # noqa: N802
        return self._evidence

    @Property(QObject, constant=True)
    def runModel(self) -> QObject:  # noqa: N802
        return self._runs

    @Property(bool, notify=planChanged)
    def planOpen(self) -> bool:  # noqa: N802
        return self._plan_open

    @Property(str, notify=planChanged)
    def family(self) -> str:
        return "" if self._artifact is None else artifact_kind(self._artifact)

    @Property(str, notify=planChanged)
    def title(self) -> str:
        if isinstance(self._artifact, B3StudyRevision):
            return "Run curated B3 Study"
        if isinstance(
            self._artifact,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            return "Run experiment"
        return "Run Study"

    @Property(str, notify=planChanged)
    def bindingNotice(self) -> str:  # noqa: N802
        return self._binding_notice

    @Property(str, notify=planChanged)
    def advisoryMessage(self) -> str:  # noqa: N802
        return self._advisory

    @Property(str, notify=planChanged)
    def executeLabel(self) -> str:  # noqa: N802
        return self._execute_label

    @Property(int, notify=planChanged)
    def expandedRunCount(self) -> int:  # noqa: N802
        return self._runs.rowCount()

    def is_running(self) -> bool:
        return self._thread is not None

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self.is_running()

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    def open_plan(
        self,
        artifact: ConcreteWorkbenchArtifact,
        *,
        binding_notice: str | None = None,
    ) -> None:
        if self.is_running():
            raise RuntimeError("Cannot replace the Run Plan while execution is active.")
        self._artifact = artifact
        self._binding_notice = binding_notice or ""
        self._plan_open = True
        self._refresh_plan()
        self.planChanged.emit()
        self._set_status("Review the exact scientific owner before execution.")

    def clear_plan(self) -> None:
        if self.is_running():
            return
        self._artifact = None
        self._plan_open = False
        self._binding_notice = ""
        self._advisory = ""
        self._execute_label = "Run"
        self._summary.set_items(())
        self._evidence.set_items(())
        self._runs.set_items(())
        self.planChanged.emit()
        self._set_status("No Run Plan is open.")

    @Slot()
    def cancelPlan(self) -> None:  # noqa: N802
        self.clear_plan()

    @Slot(result=bool)
    def executePlan(self) -> bool:  # noqa: N802
        if self.is_running() or not self._plan_open or self._artifact is None:
            return False
        artifact = self._artifact
        worker = _RunWorker(artifact)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._worker_completed)
        worker.failed.connect(self._worker_failed)
        worker.completed.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(self._worker_finished)
        thread.finished.connect(thread.deleteLater)
        self._worker = worker
        self._thread = thread
        self._plan_open = False
        self.planChanged.emit()
        self.runningChanged.emit()
        self._set_status("Executing the exact reviewed Workbench artifact…")
        thread.start()
        return True

    @Slot(object, object, object)
    def _worker_completed(
        self, source: object, updated: object, result: object
    ) -> None:
        self.completed.emit(source, updated, result)
        self._set_status("Execution completed; authoritative result returned.")

    @Slot(object, str)
    def _worker_failed(self, source: object, message: str) -> None:
        self.failed.emit(source, message)
        self._set_status(f"Execution failed: {message}")

    @Slot()
    def _worker_finished(self) -> None:
        self._worker = None
        self._thread = None
        self.runningChanged.emit()

    def _refresh_plan(self) -> None:
        artifact = self._artifact
        if artifact is None:
            return
        self._evidence.set_items(
            tuple(
                MeaningItem(label=option.label, value=option.meaning)
                for option in evidence_options(artifact)
                if option.evidence_id in requested_evidence_ids(artifact)
            )
        )
        self._advisory = " · ".join(
            item.message for item in evidence_advisories_for_artifact(artifact)
        )
        self._runs.set_items(())

        if isinstance(artifact, StudyRevision):
            self._summary.set_items(
                (
                    MeaningItem(label="Study revision", value=artifact.revision_id),
                    MeaningItem(
                        label="Seed",
                        value=str(artifact.manifest.explicit_value(SEED_SLOT)),
                    ),
                    MeaningItem(
                        label="Horizon",
                        value=str(
                            artifact.manifest.derived_value(
                                "controlled-locomotion.horizon-step-index"
                            )
                        ),
                    ),
                    MeaningItem(
                        label="Manifest digest", value=artifact.manifest.digest
                    ),
                )
            )
            self._execute_label = "Run Study"
            return

        if isinstance(artifact, ReferenceStudyRevision):
            self._summary.set_items(
                (
                    MeaningItem(label="Study revision", value=artifact.revision_id),
                    MeaningItem(
                        label="Seed",
                        value=str(
                            artifact.manifest.explicit_value(REFERENCE_SEED_SLOT)
                        ),
                    ),
                    MeaningItem(
                        label="Horizon",
                        value=str(
                            artifact.manifest.explicit_value(REFERENCE_HORIZON_SLOT)
                        ),
                    ),
                    MeaningItem(
                        label="Manifest digest", value=artifact.manifest.digest
                    ),
                )
            )
            self._execute_label = "Run Study"
            return

        if isinstance(artifact, MaxSpeedSweepDefinition):
            rows = max_speed_run_rows(artifact)
            self._summary.set_items(
                (
                    MeaningItem(label="Factor", value="Maximum speed"),
                    MeaningItem(label="Levels", value=_integers(artifact.levels)),
                    MeaningItem(
                        label="Replicate seeds", value=_integers(artifact.seeds)
                    ),
                    MeaningItem(label="Total simulations", value=str(len(rows))),
                )
            )
            self._runs.set_items(
                tuple(
                    ExperimentRunItem(
                        maximum_speed=str(row.maximum_speed),
                        seed=str(row.seed),
                        resource_geography=_humanize(row.resource_geography),
                    )
                    for row in rows
                )
            )
            self._execute_label = f"Run {len(rows)} simulations"
            return

        if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
            rows = environment_run_rows(artifact)
            self._summary.set_items(
                (
                    MeaningItem(label="Primary factor", value="Resource geography"),
                    MeaningItem(
                        label="Control", value=_humanize(artifact.control_environment)
                    ),
                    MeaningItem(
                        label="Treatment",
                        value=_humanize(artifact.treatment_environment),
                    ),
                    MeaningItem(
                        label="Standing focal composition",
                        value=_integers(artifact.focal_speeds),
                    ),
                    MeaningItem(
                        label="Replicate seeds", value=_integers(artifact.seeds)
                    ),
                    MeaningItem(label="Total simulations", value=str(len(rows))),
                )
            )
            self._runs.set_items(
                tuple(
                    ExperimentRunItem(
                        seed=str(row.seed),
                        role=row.role.title(),
                        environment=_humanize(row.environment),
                        standing_composition=_integers(row.standing_focal_composition),
                        founder_order=_integers(row.founder_speed_order),
                    )
                    for row in rows
                )
            )
            self._execute_label = f"Run {len(rows)} simulations"
            return

        if isinstance(artifact, B3StudyRevision):
            counts = b3_case_counts(artifact)
            validated = (
                artifact.scenario_identity or "none — B3-derived sensitivity Study"
            )
            self._summary.set_items(
                (
                    MeaningItem(label="Study revision", value=artifact.revision_id),
                    MeaningItem(
                        label="Scenario origin", value=artifact.scenario_origin
                    ),
                    MeaningItem(label="Validated scenario", value=validated),
                    MeaningItem(
                        label="Manifest digest", value=artifact.manifest.digest
                    ),
                    MeaningItem(
                        label="Primary confirmation pairs",
                        value=str(counts.confirmation_pairs),
                    ),
                    MeaningItem(
                        label="Radius-sensitivity runs",
                        value=str(counts.radius_sensitivity_runs),
                    ),
                    MeaningItem(
                        label="Counterbalanced pairs",
                        value=str(counts.counterbalanced_pairs),
                    ),
                    MeaningItem(
                        label="Total simulations", value=str(counts.total_simulations)
                    ),
                )
            )
            self._advisory = (
                "Same-seed control/treatment cases are matched blocks, not guaranteed "
                "lockstep trajectories after treatment divergence."
            )
            self._execute_label = f"Run {counts.total_simulations} simulations"
            return

        raise TypeError("Unsupported Workbench artifact for native Run Plan.")

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _integers(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = ["RunController"]
