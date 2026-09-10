from __future__ import annotations

import os
import time
from typing import cast

import attrs
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QSignalSpy

from evo_engine.desktop.controllers import ReferenceStudyController
from evo_engine.desktop.models import WorldOrganismModel, WorldResourceModel
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID,
    SPATIAL_EVIDENCE_ID,
    ReferenceEvidencePlan,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_study import (
    create_reference_study_revision,
    run_reference_study_revision,
)
from evo_engine.workbench.results import inspect_reference_study_results


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _compact_reference_revision():
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        width=12,
        height=12,
        founder_population=8,
        horizon=12,
        seed=1729,
    )
    return create_reference_study_revision(
        revision_id="reference-q1-test",
        intent=intent,
        evidence_plan=ReferenceEvidencePlan(
            requested=(POPULATION_EVIDENCE_ID, SPATIAL_EVIDENCE_ID)
        ),
    )


def _compact_reference_without_spatial():
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        width=12,
        height=12,
        founder_population=8,
        horizon=12,
        seed=1730,
    )
    return create_reference_study_revision(
        revision_id="reference-q3-no-spatial",
        intent=intent,
        evidence_plan=ReferenceEvidencePlan(requested=(POPULATION_EVIDENCE_ID,)),
    )


def test_controller_emits_active_and_draft_change_signals() -> None:
    _app()
    controller = ReferenceStudyController()
    active_spy = QSignalSpy(controller.activeChanged)
    draft_spy = QSignalSpy(controller.draftChanged)
    revision = _compact_reference_revision()

    controller.activate_revision(revision)

    assert active_spy.count() == 1
    assert draft_spy.count() == 1
    assert controller._revision == revision
    assert revision.intent.max_speed is not None

    controller.set_draft_max_speed(revision.intent.max_speed + 1)

    assert active_spy.count() == 1
    assert draft_spy.count() == 2
    assert controller.is_draft_dirty()


def test_semantic_draft_does_not_mutate_active_scientific_identity() -> None:
    _app()
    controller = ReferenceStudyController()
    revision = _compact_reference_revision()
    controller.activate_revision(revision)
    parent_json = revision.to_json()
    parent_digest = revision.manifest.digest
    assert revision.intent.max_speed is not None

    controller.set_draft_max_speed(revision.intent.max_speed + 1)

    assert controller.is_draft_dirty()
    assert controller._revision is not None
    assert controller._revision.to_json() == parent_json
    assert controller._revision.manifest.digest == parent_digest
    assert controller.saveChildRevision()
    assert controller._revision is not None
    assert controller._revision.parent_revision_id == revision.revision_id
    assert revision.to_json() == parent_json
    assert controller._revision.manifest.digest != parent_digest


def test_clearing_reference_owner_discards_transient_result_and_draft() -> None:
    _app()
    controller = ReferenceStudyController()
    revision = _compact_reference_revision()
    controller.activate_revision(revision)
    assert revision.intent.max_speed is not None
    controller.set_draft_max_speed(revision.intent.max_speed + 1)

    controller.clear()

    assert not controller.is_active()
    assert not controller.is_draft_dirty()
    assert not controller.hasResult
    assert not controller.hasWorld


def test_worker_run_surfaces_authoritative_result_and_world_frame() -> None:
    app = _app()
    controller = ReferenceStudyController()
    controller.activate_revision(_compact_reference_revision())
    controller.runStudy()
    deadline = time.monotonic() + 20.0
    while controller.is_running() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()

    assert not controller.is_running()
    assert controller._revision is not None
    assert controller._result is not None
    view = inspect_reference_study_results(controller._revision, controller._result)
    assert view.population_observations
    assert view.spatial_observations
    assert (
        controller.finalPopulation == view.population_observations[-1].population_size
    )
    assert controller._presentation is not None
    assert controller.worldStep == view.spatial_observations[-1].step_index
    organism_model = cast(WorldOrganismModel, controller.organismModel)
    resource_model = cast(WorldResourceModel, controller.resourceModel)
    assert organism_model.rowCount() == len(controller._presentation.frame.organisms)
    assert resource_model.rowCount() == len(controller._presentation.frame.resources)


def test_reference_result_without_spatial_evidence_does_not_invent_world() -> None:
    _app()
    revision = _compact_reference_without_spatial()
    result = run_reference_study_revision(revision, run_id="q3-no-spatial")
    completed = revision.with_run(result.provenance)
    controller = ReferenceStudyController()
    controller.activate_revision(completed)

    controller.accept_run_result(completed, result)

    assert controller.hasResult
    assert not controller.hasWorld
    assert controller._presentation is None
