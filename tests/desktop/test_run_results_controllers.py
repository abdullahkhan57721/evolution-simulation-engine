from __future__ import annotations

import os
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtGui import QGuiApplication

import evo_engine.desktop.controllers.run as run_module
from evo_engine.desktop.artifacts import new_controlled_run
from evo_engine.desktop.controllers import (
    ApplicationController,
    EvidenceAuthoringController,
    ExperimentAuthoringController,
    ResultsController,
    RunController,
    SimulationAuthoringController,
)
from evo_engine.desktop.models import EvidenceOptionModel, MeaningListModel
from evo_engine.workbench import (
    REFERENCE_SPATIAL_EVIDENCE_ID,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
    run_study_revision,
)


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _controller() -> ApplicationController:
    _app()
    return ApplicationController()


def _active(controller: ApplicationController):
    assert controller._artifact is not None
    return controller._artifact


def _simulation(controller: ApplicationController) -> SimulationAuthoringController:
    return cast(SimulationAuthoringController, controller.simulationController)


def _evidence(controller: ApplicationController) -> EvidenceAuthoringController:
    return cast(EvidenceAuthoringController, controller.evidenceController)


def _experiment(controller: ApplicationController) -> ExperimentAuthoringController:
    return cast(ExperimentAuthoringController, controller.experimentController)


def _run(controller: ApplicationController) -> RunController:
    return cast(RunController, controller.runController)


@pytest.mark.parametrize(
    "kind",
    (
        "controlled-run",
        "reference-ecology",
        "max-speed-sweep",
        "environment-selection-comparison",
        "b3-flagship",
    ),
)
def test_all_supported_families_open_exact_native_run_plan(kind: str) -> None:
    controller = _controller()
    assert controller.createStudy(kind)
    assert controller.canRun

    controller.runStudy()

    run = _run(controller)
    assert controller.runPlanOpen
    assert run.planOpen
    assert run.family == kind
    assert cast(MeaningListModel, run.summaryModel).items()
    assert cast(MeaningListModel, run.evidenceModel).items()
    if kind in ("max-speed-sweep", "environment-selection-comparison"):
        assert run.expandedRunCount > 0


def test_controlled_pending_simulation_and_evidence_bind_to_one_child_before_run() -> None:
    controller = _controller()
    assert controller.createStudy("controlled-run")
    parent = _active(controller)
    assert isinstance(parent, StudyRevision)
    encoded = parent.to_json()

    simulation = _simulation(controller)
    simulation.set_controlled_max_speed(7)
    evidence = _evidence(controller)
    option = cast(EvidenceOptionModel, evidence.optionModel).items()[0]
    evidence.setEvidenceSelected(option.evidence_id, False)

    controller.runStudy()

    child = _active(controller)
    assert isinstance(child, StudyRevision)
    assert child.parent_revision_id == parent.revision_id
    assert child.intent.max_speed == 7
    assert option.evidence_id not in child.evidence_plan.requested
    assert parent.to_json() == encoded
    assert _run(controller).bindingNotice.startswith(
        "Pending Simulation/Evidence edits were bound atomically"
    )
    assert controller.runPlanOpen


def test_reference_pending_simulation_and_evidence_bind_to_one_child_before_run() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    parent = _active(controller)
    assert isinstance(parent, ReferenceStudyRevision)
    encoded = parent.to_json()

    reference = controller._reference
    reference.set_draft_max_speed(4 if reference.draftMaxSpeed != 4 else 3)
    evidence = _evidence(controller)
    spatial = next(
        item
        for item in cast(EvidenceOptionModel, evidence.optionModel).items()
        if item.evidence_id == REFERENCE_SPATIAL_EVIDENCE_ID
    )
    evidence.setEvidenceSelected(spatial.evidence_id, not spatial.selected)

    controller.runStudy()

    child = _active(controller)
    assert isinstance(child, ReferenceStudyRevision)
    assert child.parent_revision_id == parent.revision_id
    assert child.intent.max_speed != parent.intent.max_speed
    assert (
        REFERENCE_SPATIAL_EVIDENCE_ID in child.evidence_plan.requested
    ) != (
        REFERENCE_SPATIAL_EVIDENCE_ID in parent.evidence_plan.requested
    )
    assert parent.to_json() == encoded
    assert controller.runPlanOpen


def test_pending_e3_definition_becomes_exact_owner_before_run_plan() -> None:
    controller = _controller()
    assert controller.createStudy("max-speed-sweep")
    before = _active(controller)
    assert isinstance(before, MaxSpeedSweepDefinition)
    experiment = _experiment(controller)
    experiment.setReplicateSeeds("101, 202")
    assert experiment.draftDirty

    controller.runStudy()

    after = _active(controller)
    assert isinstance(after, MaxSpeedSweepDefinition)
    assert after.seeds == (101, 202)
    assert after != before
    assert controller.runPlanOpen
    assert "Pending Experiment edits" in _run(controller).bindingNotice


def test_invalid_experiment_draft_blocks_run_plan() -> None:
    controller = _controller()
    assert controller.createStudy("environment-selection-comparison")
    assert isinstance(_active(controller), EnvironmentSelectionComparisonDefinition)
    experiment = _experiment(controller)

    experiment.setReplicateSeeds("")

    assert not experiment.draftValid
    assert not controller.canRun
    controller.runStudy()
    assert not controller.runPlanOpen
    assert controller.statusTone == "warning"


def test_run_controller_executes_supported_dispatch_away_from_gui_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app()
    run = RunController()
    artifact = new_controlled_run(revision_id="q3-worker-thread")
    worker_threads: list[bool] = []

    def fake_execute(value):
        worker_threads.append(QThread.currentThread() != app.thread())
        return value, object()

    monkeypatch.setattr(run_module, "execute_artifact", fake_execute)
    run.open_plan(artifact)
    loop = QEventLoop()

    def stop_when_finished() -> None:
        if not run.running:
            loop.quit()

    run.runningChanged.connect(stop_when_finished)
    QTimer.singleShot(5000, loop.quit)
    assert run.executePlan()
    loop.exec()

    assert worker_threads == [True]
    assert not run.running


def test_controlled_results_use_wb5_and_historical_reopen_is_not_payload_archive() -> None:
    _app()
    revision = new_controlled_run(revision_id="q3-results")
    result = run_study_revision(revision, run_id="q3-results-run")
    updated = revision.with_run(result.provenance)
    results = ResultsController()

    assert results.bind_result(updated, result)
    assert results.hasResult
    assert cast(MeaningListModel, results.overviewModel).items()
    assert cast(MeaningListModel, results.provenanceModel).items()

    results.activate_artifact(updated)
    assert not results.hasResult
    assert "provenance is not a result archive" in results.historicalMessage


def test_results_reject_result_from_different_exact_owner() -> None:
    _app()
    first = new_controlled_run(revision_id="q3-first")
    second = new_controlled_run(revision_id="q3-second")
    result = run_study_revision(first, run_id="q3-stale")
    results = ResultsController()

    assert not results.bind_result(second, result)
    assert not results.hasResult


def test_scientific_change_closes_q3_run_plan_and_clears_result_presentation() -> None:
    controller = _controller()
    assert controller.createStudy("controlled-run")
    controller.runStudy()
    assert controller.runPlanOpen

    _simulation(controller).set_controlled_max_speed(7)

    assert not controller.runPlanOpen
    assert not controller.hasResult
    assert controller.presentationOwner == ""
