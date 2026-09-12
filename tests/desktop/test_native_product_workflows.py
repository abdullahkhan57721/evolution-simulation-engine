from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import evo_engine.desktop.controllers.presentation as presentation_module
import evo_engine.desktop.controllers.run as run_module
import evo_engine.desktop.main as desktop_main
from evo_engine.desktop.artifacts import ConcreteWorkbenchArtifact
from evo_engine.desktop.controllers import ApplicationController, PresentationController
from evo_engine.desktop.controllers.experiment import ExperimentAuthoringController
from evo_engine.desktop.controllers.run import RunController
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.presentation.scientific import ContinuousTraitEncoding
from evo_engine.presentation.world import OrganismPrimitive, WorldPresentationFrame
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    MaxSpeedSweepResult,
    ReferenceRunResult,
    ReferenceStudyRevision,
    WorkbenchRunProvenance,
)
from evo_engine.workbench.results import AnalysisAvailability


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _native_shell() -> tuple[
    QGuiApplication,
    QQmlApplicationEngine,
    ApplicationController,
    PresentationController,
    list[str],
]:
    app = _app()
    engine = QQmlApplicationEngine()
    controller = ApplicationController()
    presentation = PresentationController(controller)
    warnings: list[str] = []

    def collect(errors) -> None:
        warnings.extend(error.toString() for error in errors)

    engine.warnings.connect(collect)
    engine.rootContext().setContextProperty("applicationController", controller)
    engine.rootContext().setContextProperty("presentationController", presentation)
    qml_path = Path(desktop_main.__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    app.processEvents()
    assert engine.rootObjects()
    assert warnings == []
    return app, engine, controller, presentation, warnings


def _run(controller: ApplicationController) -> RunController:
    return cast(RunController, controller.runController)


def _experiment(controller: ApplicationController) -> ExperimentAuthoringController:
    return cast(ExperimentAuthoringController, controller.experimentController)


def _provenance(
    revision: ReferenceStudyRevision | B3StudyRevision,
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
        experiment_id="q5-native-product",
        scenario_id="q5-product-scenario",
        treatment_id="q5-product-treatment",
        treatment_specification_json="{}",
        seed=7,
        horizon_step_index=2,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
        run_role="representative",
    )


def _reference_execution(
    artifact: ReferenceStudyRevision,
) -> tuple[ReferenceStudyRevision, ReferenceRunResult]:
    provenance = _provenance(artifact, run_id="q5-reference-run")
    result = ReferenceRunResult(
        provenance=provenance,
        scientific_provenance=_scientific_provenance(),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )
    return artifact.with_run(provenance), result


def _b3_execution(
    artifact: B3StudyRevision,
) -> tuple[B3StudyRevision, B3CuratedRunResult]:
    provenance = _provenance(artifact, run_id="q5-b3-run")
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=artifact.scenario_origin,
        scenario_identity=artifact.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    return artifact.with_run(provenance), result


def _frame(
    step: int,
    *,
    selected: int | None = None,
    encoding: ContinuousTraitEncoding | None = None,
    offset: int = 0,
) -> WorldPresentationFrame:
    return WorldPresentationFrame(
        committed_step_index=step,
        world_width=12,
        world_height=10,
        organisms=(
            OrganismPrimitive(
                organism_id=1,
                x=2 + step + offset,
                y=3,
                age=step,
                energy=50,
                body_mass=2,
                mating_type="A",
                marker_size=14,
                selected=selected == 1,
                focal_trait_value=3 if encoding is not None else None,
                focal_trait_normalized=0.5 if encoding is not None else None,
            ),
        ),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=selected,
        focal_encoding=encoding,
    )


def _wait_for_execution(app: QGuiApplication, run: RunController) -> None:
    loop = QEventLoop()

    def stop_when_finished() -> None:
        if not run.is_running():
            loop.quit()

    run.runningChanged.connect(stop_when_finished)
    QTimer.singleShot(5000, loop.quit)
    assert run.executePlan()
    loop.exec()
    app.processEvents()
    assert not run.is_running()


def test_reference_product_path_reaches_owned_results_and_committed_presentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _engine, controller, presentation, warnings = _native_shell()
    controller.showNewStudy()
    assert controller.createStudy("reference-ecology")
    parent = controller._artifact
    assert isinstance(parent, ReferenceStudyRevision)
    encoded_parent = parent.to_json()

    reference = controller._reference
    reference.set_draft_max_speed(4 if reference.draftMaxSpeed != 4 else 3)

    controller.runStudy()
    child = controller._artifact
    assert isinstance(child, ReferenceStudyRevision)
    assert child.parent_revision_id == parent.revision_id
    assert parent.to_json() == encoded_parent
    assert controller.runPlanOpen

    monkeypatch.setattr(
        run_module,
        "execute_artifact",
        lambda artifact: _reference_execution(cast(ReferenceStudyRevision, artifact)),
    )
    available = AnalysisAvailability(
        analysis_id="q5.reference.spatial",
        source_contract="Q5 product-transition fixture",
        required_evidence_ids=(),
    )
    monkeypatch.setattr(
        presentation_module,
        "inspect_reference_study_results",
        lambda *_: SimpleNamespace(
            spatial_availability=available,
            spatial_observations=(0, 1, 2),
        ),
    )
    monkeypatch.setattr(
        presentation_module,
        "available_step_indices",
        lambda observations: tuple(observations),
    )
    monkeypatch.setattr(
        presentation_module,
        "build_reference_workbench_world_presentation",
        lambda *_args, step_index, selected_organism_id=None, **_kwargs: (
            SimpleNamespace(frame=_frame(step_index, selected=selected_organism_id))
        ),
    )

    _wait_for_execution(app, _run(controller))

    assert controller.studySection == "Results"
    assert controller.hasResult
    assert controller.presentationOwner
    assert controller.selectSection("Presentation")
    app.processEvents()
    assert presentation.available
    assert presentation.committedStep == 2
    presentation.previousStep()
    assert presentation.committedStep == 1
    presentation.selectOrganism(1)
    assert presentation.inspectorTitle == "Organism 1"
    assert warnings == []


def test_canonical_b3_product_path_keeps_matched_seed_and_step_navigation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _engine, controller, presentation, warnings = _native_shell()
    assert controller.createStudy("b3-flagship")
    artifact = controller._artifact
    assert isinstance(artifact, B3StudyRevision)
    assert artifact.scenario_identity

    controller.runStudy()
    assert controller.runPlanOpen
    monkeypatch.setattr(
        run_module,
        "execute_artifact",
        lambda value: _b3_execution(cast(B3StudyRevision, value)),
    )

    pairs = tuple(
        SimpleNamespace(
            summary=SimpleNamespace(seed=seed),
            control_evidence=SimpleNamespace(spatial_observations=(0, 1, 2)),
            treatment_evidence=SimpleNamespace(spatial_observations=(0, 1, 2)),
        )
        for seed in (17, 23)
    )
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=9,
    )
    monkeypatch.setattr(
        presentation_module,
        "inspect_b3_results",
        lambda *_: SimpleNamespace(confirmation=pairs),
    )
    monkeypatch.setattr(
        presentation_module,
        "available_step_indices",
        lambda observations: tuple(observations),
    )

    def build_b3(
        *_args,
        seed: int,
        arm: str,
        step_index: int,
        selected_organism_id=None,
        **_kwargs,
    ):
        offset = 0 if arm == "control" else 2
        return SimpleNamespace(
            frame=_frame(
                step_index,
                selected=selected_organism_id,
                encoding=encoding,
                offset=offset,
            )
        )

    monkeypatch.setattr(
        presentation_module,
        "build_b3_workbench_world_presentation",
        build_b3,
    )

    _wait_for_execution(app, _run(controller))

    assert controller.studySection == "Results"
    assert controller.hasResult
    assert controller.selectSection("Presentation")
    app.processEvents()
    assert presentation.available
    assert presentation.family == "b3"
    assert presentation.b3Seed == 17
    assert presentation.committedStep == 0
    presentation.nextStep()
    assert presentation.committedStep == 1
    presentation.nextB3Seed()
    assert presentation.b3Seed == 23
    assert presentation.committedStep == 0
    presentation.selectTreatmentOrganism(1)
    assert presentation.treatmentInspectorTitle == "Organism 1"
    assert warnings == []


def test_e3_authoring_run_plan_execution_and_results_are_one_product_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _engine, controller, _presentation, warnings = _native_shell()
    assert controller.createStudy("max-speed-sweep")
    before = controller._artifact
    assert isinstance(before, MaxSpeedSweepDefinition)

    experiment = _experiment(controller)
    experiment.setReplicateSeeds("101, 202")
    assert experiment.draftDirty
    controller.runStudy()

    exact = controller._artifact
    assert isinstance(exact, MaxSpeedSweepDefinition)
    assert exact.seeds == (101, 202)
    assert exact != before
    assert controller.runPlanOpen
    assert cast(int, _run(controller).property("expandedRunCount")) > 0

    def execute_e3(
        artifact: ConcreteWorkbenchArtifact,
    ) -> tuple[ConcreteWorkbenchArtifact, object]:
        definition = cast(MaxSpeedSweepDefinition, artifact)
        return definition, MaxSpeedSweepResult(
            definition=definition,
            treatments=(),
            replicate_outcomes=(),
            treatment_summaries=(),
        )

    monkeypatch.setattr(run_module, "execute_artifact", execute_e3)
    _wait_for_execution(app, _run(controller))

    assert controller.studySection == "Results"
    assert controller.hasResult
    assert warnings == []


def test_blocked_e4_draft_stays_blocked_with_actionable_native_state() -> None:
    app, _engine, controller, _presentation, warnings = _native_shell()
    assert controller.createStudy("environment-selection-comparison")
    assert isinstance(controller._artifact, EnvironmentSelectionComparisonDefinition)
    experiment = _experiment(controller)

    experiment.setReplicateSeeds("")
    app.processEvents()

    assert not experiment.draftValid
    assert not controller.canRun
    controller.runStudy()
    app.processEvents()
    assert not controller.runPlanOpen
    assert controller.statusTone == "warning"
    assert "cannot be bound" in cast(str, controller.property("status"))
    assert warnings == []
