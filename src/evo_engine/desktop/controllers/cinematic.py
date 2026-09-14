"""Native B3 cinematic presentation bridge over the existing Workbench handoff.

This controller owns only transient desktop presentation state. Scientific story
eligibility is delegated to ``prepare_b3_workbench_cinematic`` and rendering is
delegated to the existing B3 renderer. Renderer choices and output locations are
never written into a Study artifact or scientific manifest.
"""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
from typing import Protocol, cast

from PySide6.QtCore import Property, QObject, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_api import render_b3_flagship_cinematic
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan
from evo_engine.cinematic.workbench import prepare_b3_workbench_cinematic
from evo_engine.desktop.controllers.application import ApplicationController
from evo_engine.workbench import B3CuratedRunResult, B3StudyRevision


class _B3Renderer(Protocol):
    def __call__(
        self,
        plan: B3FlagshipDirectorPlan,
        output_path: str | Path,
        *,
        quality: AnimationQuality = "medium",
    ) -> Path: ...


class _RenderSignals(QObject):
    completed = Signal(str)
    failed = Signal(str)


class _B3RenderTask(QRunnable):
    """Run optional Manim rendering away from the Qt GUI thread."""

    def __init__(
        self,
        *,
        renderer: _B3Renderer,
        plan: B3FlagshipDirectorPlan,
        destination: Path,
        quality: AnimationQuality,
    ) -> None:
        super().__init__()
        self.signals = _RenderSignals()
        self._renderer = renderer
        self._plan = plan
        self._destination = destination
        self._quality = quality

    @Slot()
    def run(self) -> None:
        try:
            rendered = self._renderer(
                self._plan,
                self._destination,
                quality=self._quality,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self.signals.failed.emit(str(exc))
            return
        self.signals.completed.emit(str(rendered))


class CinematicController(QObject):
    """Expose the validated B3 story as transient native presentation state."""

    stateChanged = Signal()

    def __init__(
        self,
        application: ApplicationController,
        parent: QObject | None = None,
        *,
        renderer: _B3Renderer = render_b3_flagship_cinematic,
        thread_pool: QThreadPool | None = None,
    ) -> None:
        super().__init__(parent)
        self._application = application
        self._renderer = renderer
        self._thread_pool = thread_pool or QThreadPool.globalInstance()
        self._plan: B3FlagshipDirectorPlan | None = None
        self._story_available = False
        self._message = "Run the canonical B3 flagship to prepare its scientific story."
        self._rendering = False
        self._output_path = ""
        self._render_owner = ""
        self._active_task: _B3RenderTask | None = None

        application.artifactChanged.connect(self.refresh)
        application.resultChanged.connect(self.refresh)
        application.presentationChanged.connect(self.refresh)
        self.refresh()

    @Property(bool, notify=stateChanged)
    def storyAvailable(self) -> bool:  # noqa: N802
        return self._story_available

    @Property(bool, constant=True)
    def rendererAvailable(self) -> bool:  # noqa: N802
        return _renderer_available()

    @Property(bool, notify=stateChanged)
    def rendering(self) -> bool:
        return self._rendering

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def outputPath(self) -> str:  # noqa: N802
        return self._output_path

    @Property(bool, notify=stateChanged)
    def hasOutput(self) -> bool:  # noqa: N802
        return bool(self._output_path)

    @Slot()
    def refresh(self) -> None:
        """Re-evaluate story eligibility from the exact active scientific owner."""
        artifact = self._application.active_artifact()
        result = self._application.active_result()
        plan: B3FlagshipDirectorPlan | None = None
        available = False

        if not isinstance(artifact, B3StudyRevision):
            message = "The scientific cinematic is available only for B3 Studies."
        elif not isinstance(result, B3CuratedRunResult):
            message = "Run this B3 Study before preparing its scientific cinematic."
        else:
            try:
                plan = prepare_b3_workbench_cinematic(artifact, result)
            except ValueError as exc:
                message = str(exc)
            else:
                available = True
                if self.rendererAvailable:
                    message = (
                        "Validated B3 scientific handoff available. Render quality and "
                        "file format affect presentation only."
                    )
                else:
                    message = (
                        "Validated B3 scientific handoff available, but the optional "
                        "Manim renderer is not installed in this runtime."
                    )

        changed = (
            available != self._story_available
            or message != self._message
            or plan is not self._plan
        )
        self._plan = plan
        self._story_available = available
        self._message = message
        if not available:
            self._output_path = ""
        if changed:
            self.stateChanged.emit()

    @Slot(str, str, result=bool)
    def renderStory(self, location: str, quality: str) -> bool:  # noqa: N802
        """Render the prepared story asynchronously to one user-selected file."""
        if self._rendering:
            self._set_message("A B3 cinematic render is already in progress.")
            return False
        plan = self._plan
        if not self._story_available or plan is None:
            self._set_message("The active Study does not have an eligible B3 story.")
            return False
        if not self.rendererAvailable:
            self._set_message(
                "The scientific story is eligible, but the optional Manim renderer "
                "is not installed."
            )
            return False
        if quality not in ("low", "medium", "high"):
            self._set_message("Render quality must be low, medium, or high.")
            return False
        try:
            destination = _path_from_location(location)
        except ValueError as exc:
            self._set_message(str(exc))
            return False
        if destination.suffix.lower() not in (".mp4", ".gif"):
            self._set_message("Choose an .mp4 or .gif output file.")
            return False

        task = _B3RenderTask(
            renderer=self._renderer,
            plan=plan,
            destination=destination,
            quality=cast(AnimationQuality, quality),
        )
        task.signals.completed.connect(self._on_render_completed)
        task.signals.failed.connect(self._on_render_failed)
        self._active_task = task
        self._render_owner = self._application.presentationOwner
        self._output_path = ""
        self._rendering = True
        self._message = "Rendering the validated B3 scientific story…"
        self.stateChanged.emit()
        self._thread_pool.start(task)
        return True

    @Slot(result=bool)
    def openOutput(self) -> bool:  # noqa: N802
        if not self._output_path:
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(self._output_path))

    @Slot(str)
    def _on_render_completed(self, rendered_path: str) -> None:
        owner_matches = self._render_owner == self._application.presentationOwner
        self._rendering = False
        self._active_task = None
        if owner_matches:
            self._output_path = rendered_path
            self._message = "B3 scientific story rendered successfully."
        else:
            self._output_path = ""
            self._message = (
                "Rendering completed for a previous scientific result. The active "
                "Study was not associated with that presentation artifact."
            )
        self.stateChanged.emit()

    @Slot(str)
    def _on_render_failed(self, message: str) -> None:
        self._rendering = False
        self._active_task = None
        self._output_path = ""
        self._message = f"B3 renderer failed: {message}"
        self.stateChanged.emit()

    def _set_message(self, value: str) -> None:
        if value == self._message:
            return
        self._message = value
        self.stateChanged.emit()


def _renderer_available() -> bool:
    try:
        return find_spec("manim") is not None
    except (ImportError, ValueError):
        return False


def _path_from_location(location: str) -> Path:
    if type(location) is not str or not location.strip():
        raise ValueError("Choose a non-empty cinematic output location.")
    if location.startswith("file:"):
        local = QUrl(location).toLocalFile()
        if not local:
            raise ValueError("Cinematic output URL is not a local file.")
        return Path(local).expanduser()
    return Path(location).expanduser()


__all__ = ["CinematicController"]
