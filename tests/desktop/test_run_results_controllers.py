from __future__ import annotations

import os
from types import SimpleNamespace
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QThread, QTimer
from PySide6.QtGui import QGuiApplication

import evo_engine.desktop.controllers.results as results_module
import evo_engine.desktop.controllers.run as run_module
from evo_engine.desktop.artifacts import (
    ConcreteWorkbenchArtifact,
    artifact_kind,
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
)
from evo_engine.desktop.controllers import (
    ApplicationController,
    EvidenceAuthoringController,
    ExperimentAuthoringController,
    ResultsController,
    RunController,
    SimulationAuthoringController,
)
from evo_engine.desktop.models import EvidenceOptionModel, MeaningListModel
from evo_engine.experiments.e4_selection import E4EnvironmentSummary
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.workbench import (
    REFERENCE_SPATIAL_EVIDENCE_ID,
    B3CuratedRunResult,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
    ReferenceRunResult,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchRunProvenance,
    run_study_revision,
)
from evo_engine.workbench.results import AnalysisAvailability


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


def _provenance(
    revision: StudyRevision | ReferenceStudyRevision | B3StudyRevision,
    *,
    run_id: str,
) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )


def _scientific_provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="q3-native-results-test",
        scenario_id="q3-test-scenario",
        treatment_id="q3-test-treatment",
        treatment_specification_json="{}",
        seed=7,
        horizon_step_index=0,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
        run_role="representative",
    )


def _available(analysis_id: str) -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="Q3 test evidence",
        required_evidence_ids=(),
    )


def _missing(analysis_id: str, evidence_id: str) -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="Q3 test evidence",
        required_evidence_ids=(evidence_id,),
        missing_evidence_ids=(evidence_id,),
    )


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
    assert run.is_plan_open()
    assert run.family == kind
    assert cast(MeaningListModel, run.summaryModel).items()
    assert cast(MeaningListModel, run.evidenceModel).items()
    if kind in ("max-speed-sweep", "environment-selection-comparison"):
        assert cast(int, run.property("expandedRunCount")) > 0


def test_controlled_pending_simulation_and_evidence_bind_to_one_child_before_run() -> (
    None
):
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
    assert cast(str, _run(controller).property("bindingNotice")).startswith(
        "Pending Simulation/Evidence edits were bound atomically"
    )
    assert controller.runPlanOpen


def test_reference_pending_simulation_and_evidence_bind_to_one_child_before_run() -> (
    None
):
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
    assert (REFERENCE_SPATIAL_EVIDENCE_ID in child.evidence_plan.requested) != (
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
    assert "Pending Experiment edits" in cast(
        str, _run(controller).property("bindingNotice")
    )


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
def test_each_supported_family_executes_away_from_gui_thread(
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app()
    controller = _controller()
    assert controller.createStudy(kind)
    artifact = _active(controller)
    run = RunController()
    worker_observations: list[tuple[str, bool]] = []

    def fake_execute(
        value: ConcreteWorkbenchArtifact,
    ) -> tuple[ConcreteWorkbenchArtifact, object]:
        worker_observations.append(
            (artifact_kind(value), QThread.currentThread() != app.thread())
        )
        return value, object()

    monkeypatch.setattr(run_module, "execute_artifact", fake_execute)
    run.open_plan(artifact)
    loop = QEventLoop()

    def stop_when_finished() -> None:
        if not run.is_running():
            loop.quit()

    run.runningChanged.connect(stop_when_finished)
    QTimer.singleShot(5000, loop.quit)
    assert run.executePlan()
    loop.exec()

    assert worker_observations == [(kind, True)]
    assert not run.is_running()


def test_controlled_results_use_wb5_and_historical_reopen_is_not_payload_archive() -> (
    None
):
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
    assert "provenance is not a result archive" in cast(
        str, results.property("historicalMessage")
    )


def test_reference_results_keep_missing_spatial_evidence_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    revision = new_reference_ecology(revision_id="q3-reference-results")
    provenance = _provenance(revision, run_id="q3-reference-run")
    scientific = _scientific_provenance()
    result = ReferenceRunResult(
        provenance=provenance,
        scientific_provenance=scientific,
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )
    available = _available("q3.reference.available")
    spatial = _missing("q3.reference.spatial", REFERENCE_SPATIAL_EVIDENCE_ID)
    view = SimpleNamespace(
        provenance=provenance,
        scientific_provenance=scientific,
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
        population_availability=available,
        event_availability=available,
        pedigree_availability=available,
        genetic_availability=available,
        spatial_availability=spatial,
    )
    monkeypatch.setattr(results_module, "result_matches_artifact", lambda *_: True)
    monkeypatch.setattr(
        results_module, "inspect_reference_study_results", lambda *_: view
    )
    results = ResultsController()

    assert results.bind_result(revision, result)

    rows = cast(MeaningListModel, results.analysisModel).items()
    spatial_row = next(item for item in rows if item.label == "Spatial replay")
    assert "Unavailable" in spatial_row.value
    assert REFERENCE_SPATIAL_EVIDENCE_ID in spatial_row.value


def test_e3_results_preserve_factor_identity_without_generic_statistics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    definition = new_max_speed_sweep()
    result = MaxSpeedSweepResult(
        definition=definition,
        treatments=(),
        replicate_outcomes=(),
        treatment_summaries=(),
    )
    view = SimpleNamespace(treatment_summaries=(), replicates=())
    monkeypatch.setattr(results_module, "result_matches_artifact", lambda *_: True)
    monkeypatch.setattr(results_module, "inspect_max_speed_sweep_results", lambda _: view)
    results = ResultsController()

    assert results.bind_result(definition, result)

    provenance = cast(MeaningListModel, results.provenanceModel).items()
    factor = next(item for item in provenance if item.label == "Factor")
    assert factor.value == "Maximum speed"
    assert cast(str, results.property("overviewTitle")) == "Treatment summaries"


def test_e4_results_preserve_factor_roles_and_standing_composition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    definition = new_environment_selection_comparison()
    result = EnvironmentSelectionComparisonResult(
        definition=definition,
        treatments=(),
        replicate_outcomes=(),
        environment_summaries=cast(
            tuple[E4EnvironmentSummary, E4EnvironmentSummary], ()
        ),
    )
    view = SimpleNamespace(environment_summaries=(), replicates=())
    monkeypatch.setattr(results_module, "result_matches_artifact", lambda *_: True)
    monkeypatch.setattr(
        results_module, "inspect_environment_selection_results", lambda _: view
    )
    results = ResultsController()

    assert results.bind_result(definition, result)

    provenance = cast(MeaningListModel, results.provenanceModel).items()
    factor = next(item for item in provenance if item.label == "Factor")
    standing = next(
        item for item in provenance if item.label == "Standing focal composition"
    )
    assert factor.value == "Resource geography"
    assert standing.value == "1, 3, 9"


def test_b3_results_preserve_scenario_identity_and_curated_result_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    revision = new_b3_flagship(revision_id="q3-b3-results")
    provenance = _provenance(revision, run_id="q3-b3-run")
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    view = SimpleNamespace(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
        cinematic_handoff_availability=_available("q3.b3.handoff"),
    )
    monkeypatch.setattr(results_module, "result_matches_artifact", lambda *_: True)
    monkeypatch.setattr(results_module, "inspect_b3_results", lambda *_: view)
    results = ResultsController()

    assert results.bind_result(revision, result)

    overview = cast(MeaningListModel, results.overviewModel).items()
    scenario_origin = next(item for item in overview if item.label == "Scenario origin")
    validated = next(item for item in overview if item.label == "Validated scenario")
    assert scenario_origin.value == revision.scenario_origin
    assert validated.value == revision.scenario_identity
    assert cast(str, results.property("analysisTitle")) == "Sensitivity and counterbalance"


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
