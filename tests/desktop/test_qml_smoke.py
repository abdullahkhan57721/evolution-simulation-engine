from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from evo_engine.desktop.main import create_engine


def test_qml_application_engine_loads_offscreen() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    engine, controller = create_engine()
    app.processEvents()

    assert engine.rootObjects()
    assert not controller.hasStudy
