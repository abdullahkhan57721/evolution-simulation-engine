"""Launch the native PySide6 / Qt Quick Evolution Experiment Workbench."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from evo_engine.desktop.controllers import ApplicationController, PresentationController


def create_engine() -> tuple[
    QQmlApplicationEngine,
    ApplicationController,
    PresentationController,
]:
    """Create and load the QML engine with native application/presentation state."""
    engine = QQmlApplicationEngine()
    controller = ApplicationController()
    presentation = PresentationController(controller)
    engine.rootContext().setContextProperty("applicationController", controller)
    engine.rootContext().setContextProperty("presentationController", presentation)
    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load desktop QML from {qml_path}.")
    return engine, controller, presentation


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
    engine, controller, presentation = create_engine()
    # Keep Python-owned objects alive for the full QML engine lifetime.
    app.setProperty("q1Engine", engine)
    app.setProperty("q1ApplicationController", controller)
    app.setProperty("q4PresentationController", presentation)
    if args.smoke_test:
        QTimer.singleShot(250, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
