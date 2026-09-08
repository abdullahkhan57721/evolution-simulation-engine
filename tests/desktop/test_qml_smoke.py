from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from evo_engine.desktop.main import create_engine


def test_qml_application_engine_loads_native_shell_offscreen() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    engine, controller = create_engine()
    app.processEvents()

    assert engine.rootObjects()
    assert controller.route == "home"
    assert not controller.hasStudy


def test_qml_shell_survives_all_five_native_authoring_families_offscreen() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    engine, controller = create_engine()

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

        for section in ("Simulation", "Evidence", "Experiment"):
            assert controller.selectSection(section)
            app.processEvents()
            assert controller.studySection == section
            assert engine.rootObjects()


def test_qml_authoring_navigation_does_not_mutate_exact_artifact() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    engine, controller = create_engine()
    assert controller.createStudy("reference-ecology")
    before = controller._artifact.to_json()

    for section in ("Simulation", "Evidence", "Experiment", "Simulation"):
        assert controller.selectSection(section)
        app.processEvents()

    assert controller._artifact.to_json() == before
    assert engine.rootObjects()
