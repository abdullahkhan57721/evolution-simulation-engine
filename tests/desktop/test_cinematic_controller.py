from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QThreadPool
from PySide6.QtGui import QGuiApplication

import evo_engine.desktop.controllers.cinematic as cinematic_module
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan
from evo_engine.desktop.artifacts import (
    fork_supported_artifact,
    new_b3_flagship,
    serialize_concrete_artifact,
)
from evo_engine.desktop.controllers import ApplicationController, CinematicController
from evo_engine.workbench import B3CuratedRunResult, WorkbenchRunProvenance


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _result(revision, *, run_id: str = "q5-b3-run") -> B3CuratedRunResult:
    return B3CuratedRunResult(
        provenance=WorkbenchRunProvenance(
            run_id=run_id,
            study_revision_id=revision.revision_id,
            manifest_digest=revision.manifest.digest,
            evidence_ids=revision.evidence_plan.requested,
            evidence_references=(),
            result_references=(),
        ),
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )


def _bind_owner(app: ApplicationController, revision, result) -> None:
    app._artifact = revision
    app._result = result
    app._presentation_owner = f"{revision.revision_id}:q5"


def test_story_eligibility_is_distinct_from_renderer_presence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    revision = new_b3_flagship(revision_id="q5-canonical")
    _bind_owner(app, revision, _result(revision))
    plan = cast(B3FlagshipDirectorPlan, object())
    monkeypatch.setattr(
        cinematic_module,
        "prepare_b3_workbench_cinematic",
        lambda *_: plan,
    )
    monkeypatch.setattr(cinematic_module, "_renderer_available", lambda: False)

    cinematic = CinematicController(app)

    assert cinematic.storyAvailable
    assert not cinematic.rendererAvailable
    assert "handoff available" in cinematic.message
    assert "renderer is not installed" in cinematic.message


def test_radius_two_fork_cannot_claim_canonical_story() -> None:
    _app()
    app = ApplicationController()
    canonical = new_b3_flagship(revision_id="q5-canonical")
    fork = fork_supported_artifact(canonical, revision_id="q5-radius-two")
    _bind_owner(app, fork, _result(fork))

    cinematic = CinematicController(app)

    assert not cinematic.storyAvailable
    assert "does not inherit" in cinematic.message
    assert "headline-claim cinematic" in cinematic.message


def test_render_runs_off_gui_thread_and_never_mutates_scientific_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    qt_app = _app()
    app = ApplicationController()
    revision = new_b3_flagship(revision_id="q5-worker")
    result = _result(revision)
    _bind_owner(app, revision, result)
    before = serialize_concrete_artifact(revision)
    plan = cast(B3FlagshipDirectorPlan, object())
    monkeypatch.setattr(
        cinematic_module,
        "prepare_b3_workbench_cinematic",
        lambda *_: plan,
    )
    monkeypatch.setattr(cinematic_module, "_renderer_available", lambda: True)

    gui_thread_id = threading.get_ident()
    renderer_thread_ids: list[int] = []

    def renderer(
        received_plan,
        output_path,
        *,
        quality="medium",
    ) -> Path:
        assert received_plan is plan
        assert quality == "high"
        renderer_thread_ids.append(threading.get_ident())
        destination = Path(output_path)
        destination.write_bytes(b"q5-render")
        return destination

    pool = QThreadPool()
    cinematic = CinematicController(app, renderer=renderer, thread_pool=pool)
    destination = tmp_path / "story.mp4"

    assert cinematic.renderStory(str(destination), "high")
    assert cinematic.rendering
    assert pool.waitForDone(5000)
    for _ in range(5):
        qt_app.processEvents()
        if not cinematic.rendering:
            break

    assert renderer_thread_ids
    assert renderer_thread_ids[0] != gui_thread_id
    assert not cinematic.rendering
    assert cinematic.hasOutput
    assert cinematic.outputPath == str(destination)
    assert destination.read_bytes() == b"q5-render"
    assert app._artifact is revision
    assert app._result is result
    assert serialize_concrete_artifact(revision) == before
