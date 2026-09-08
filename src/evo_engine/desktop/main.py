"""Launch the native PySide6 / Qt Quick Evolution Experiment Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from evo_engine.desktop.controllers import StudyController


def create_engine() -> tuple[QQmlApplicationEngine, StudyController]:
    """Create and load the QML engine with one deliberately narrow controller."""
    engine = QQmlApplicationEngine()
    controller = StudyController()
    engine.rootContext().setContextProperty("studyController", controller)
    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load desktop QML from {qml_path}.")
    return engine, controller


def main(argv: list[str] | None = None) -> int:
    """Run the native desktop application."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Load the native application and exit automatically after startup.",
    )
    args, qt_args = parser.parse_known_args(argv)
    app = QGuiApplication([sys.argv[0], *qt_args])
    engine, controller = create_engine()
    # Keep Python-owned objects alive for the full QML engine lifetime.
    app.setProperty("q0Engine", engine)
    app.setProperty("q0StudyController", controller)
    if args.smoke_test:
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
