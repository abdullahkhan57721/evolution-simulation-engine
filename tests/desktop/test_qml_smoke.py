from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import evo_engine.desktop.main as desktop_main
from evo_engine.desktop.controllers import ApplicationController, PresentationController
from evo_engine.desktop.main import create_engine
from evo_engine.workbench import ReferenceStudyRevision


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _strict_engine() -> tuple[
    QQmlApplicationEngine,
    ApplicationController,
    list[str],
]:
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
    return engine, controller, warnings


def test_qml_application_engine_loads_native_shell_offscreen() -> None:
    app = _app()
    engine, controller, warnings = _strict_engine()
    app.processEvents()

    assert engine.rootObjects()
    assert controller.route == "home"
    assert not controller.hasStudy
    assert warnings == []


def test_qml_shell_survives_all_five_native_authoring_families_without_warnings() -> (
    None
):
    app = _app()
    engine, controller, warnings = _strict_engine()

    for kind in (
        "controlled-run",
        "max-speed-sweep",
        "environment-selection-comparison",
        "b3-flagship",
        "reference-ecology",
    ):
        assert controller.createStudy(kind)
        app.processEvents()
        assert controller.route == "study"
        assert controller.artifactKind == kind

        for section in (
            "Simulation",
            "Evidence",
            "Experiment",
            "Results",
            "Presentation",
        ):
            assert controller.selectSection(section)
            app.processEvents()
            assert controller.studySection == section
            assert engine.rootObjects()
            assert warnings == []


def test_qml_route_replacement_moves_focus_to_live_content() -> None:
    app = _app()
    engine, controller, warnings = _strict_engine()
    window = engine.rootObjects()[0]

    home_new = window.findChild(QObject, "homeNewStudy")
    assert home_new is not None
    assert home_new.property("activeFocus")

    controller.showNewStudy()
    app.processEvents()
    new_b3 = window.findChild(QObject, "newB3Study")
    assert new_b3 is not None
    assert new_b3.property("activeFocus")

    assert controller.createStudy("reference-ecology")
    app.processEvents()
    section_loader = window.findChild(QObject, "sectionLoader")
    assert section_loader is not None
    assert section_loader.property("activeFocus")
    assert warnings == []


def test_qml_run_plan_popup_and_results_surface_load_offscreen() -> None:
    app = _app()
    engine, controller = create_engine()
    assert controller.createStudy("controlled-run")

    controller.runStudy()
    app.processEvents()

    assert controller.runPlanOpen
    assert engine.rootObjects()

    controller.set_run_plan_open(False)
    assert controller.selectSection("Results")
    app.processEvents()

    assert not controller.runPlanOpen
    assert controller.studySection == "Results"
    assert engine.rootObjects()


def test_qml_authoring_navigation_does_not_mutate_exact_artifact() -> None:
    app = _app()
    engine, controller = create_engine()
    assert controller.createStudy("reference-ecology")
    artifact = controller._artifact
    assert isinstance(artifact, ReferenceStudyRevision)
    before = artifact.to_json()

    for section in (
        "Simulation",
        "Evidence",
        "Experiment",
        "Results",
        "Presentation",
        "Simulation",
    ):
        assert controller.selectSection(section)
        app.processEvents()

    active = controller._artifact
    assert isinstance(active, ReferenceStudyRevision)
    assert active.to_json() == before
    assert engine.rootObjects()
