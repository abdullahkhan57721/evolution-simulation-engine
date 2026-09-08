from __future__ import annotations

import os
import time
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from evo_engine.desktop.controllers import StudyController
from evo_engine.desktop.models import WorldOrganismModel, WorldResourceModel
from evo_engine.workbench.results import inspect_reference_study_results


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def test_semantic_draft_does_not_mutate_active_scientific_identity() -> None:
    _app()
    controller = StudyController()
    controller.createStudy()
    assert controller._revision is not None
    parent = controller._revision
    parent_json = parent.to_json()
    parent_digest = controller.manifestDigest
    assert parent.intent.max_speed is not None

    controller.set_draft_max_speed(parent.intent.max_speed + 1)

    assert controller.draftDirty
    assert controller._revision.to_json() == parent_json
    assert controller.manifestDigest == parent_digest
    assert controller.saveChildRevision()
    assert controller._revision is not None
    assert controller._revision.parent_revision_id == parent.revision_id
    assert parent.to_json() == parent_json
    assert controller.manifestDigest != parent_digest


def test_exact_save_load_round_trip_uses_persisted_manifest(tmp_path) -> None:
    _app()
    source = StudyController()
    source.createStudy()
    assert source._revision is not None
    expected = source._revision.to_json()
    path = tmp_path / "study.json"

    assert source.saveStudy(str(path))
    loaded = StudyController()
    assert loaded.openStudy(str(path))
    assert loaded._revision is not None
    assert loaded._revision.to_json() == expected


def test_worker_run_surfaces_authoritative_result_and_world_frame() -> None:
    app = _app()
    controller = StudyController()
    controller.createStudy()
    controller.runStudy()
    deadline = time.monotonic() + 20.0
    while controller.running and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    app.processEvents()

    assert not controller.running
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
