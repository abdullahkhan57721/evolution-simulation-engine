from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

import attrs
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from evo_engine.desktop.artifacts import (
    STUDY_SECTIONS,
    artifact_kind,
    serialize_concrete_artifact,
)
from evo_engine.desktop.controllers import (
    ApplicationController,
    ReferenceStudyController,
)
from evo_engine.workbench import (
    B3_VALIDATED_SCENARIO_ID,
    EXPERIMENT_DEFINITION_FORMAT_ID,
    IncompatibleManifestError,
    ReferenceEvidencePlan,
    ReferenceStudyRevision,
    StudyRevision,
)
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID,
    SPATIAL_EVIDENCE_ID,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_study import (
    create_reference_study_revision,
    run_reference_study_revision,
)


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _controller() -> ApplicationController:
    _app()
    return ApplicationController()


def _active(controller: ApplicationController):
    assert controller._artifact is not None
    return controller._artifact


def _compact_reference_revision() -> ReferenceStudyRevision:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        width=12,
        height=12,
        founder_population=8,
        horizon=12,
        seed=1729,
    )
    return create_reference_study_revision(
        revision_id="reference-q1-application-test",
        intent=intent,
        evidence_plan=ReferenceEvidencePlan(
            requested=(POPULATION_EVIDENCE_ID, SPATIAL_EVIDENCE_ID)
        ),
    )


@pytest.mark.parametrize(
    ("kind", "expected"),
    (
        ("controlled-run", "controlled-run"),
        ("max-speed-sweep", "max-speed-sweep"),
        ("environment-selection-comparison", "environment-selection-comparison"),
        ("b3-flagship", "b3-flagship"),
        ("reference-ecology", "reference-ecology"),
    ),
)
def test_all_supported_new_study_families_activate_concrete_artifacts(
    kind: str,
    expected: str,
) -> None:
    controller = _controller()

    assert controller.createStudy(kind)

    assert controller.route == "study"
    assert controller.hasStudy
    assert controller.artifactKind == expected
    assert artifact_kind(_active(controller)) == expected
    assert controller.studySection == "Simulation"
    assert controller.readinessState == "ready"


def test_new_and_open_routes_are_transient_navigation_not_scientific_artifacts() -> None:
    controller = _controller()

    controller.showNewStudy()
    assert controller.route == "new"
    assert not controller.hasStudy

    controller.showOpenStudy()
    assert controller.route == "open"
    assert not controller.hasStudy

    controller.goHome()
    assert controller.route == "home"
    assert not controller.hasStudy


def test_section_navigation_never_mutates_active_science() -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    artifact = _active(controller)
    before = serialize_concrete_artifact(artifact)

    for section in STUDY_SECTIONS:
        assert controller.selectSection(section)
        assert controller.studySection == section
        assert serialize_concrete_artifact(_active(controller)) == before


def test_exact_save_and_load_round_trip_all_supported_families(tmp_path: Path) -> None:
    for kind in (
        "controlled-run",
        "max-speed-sweep",
        "environment-selection-comparison",
        "b3-flagship",
        "reference-ecology",
    ):
        source = _controller()
        assert source.createStudy(kind)
        expected = serialize_concrete_artifact(_active(source))
        path = tmp_path / f"{kind}.json"

        assert source.saveStudy(str(path))
        assert path.read_text(encoding="utf-8") == expected
        assert source.hasFileLocation

        loaded = _controller()
        assert loaded.openStudy(str(path))
        assert loaded.artifactKind == kind
        assert serialize_concrete_artifact(_active(loaded)) == expected
        assert loaded.fileLocation == str(path)


def test_open_unknown_experiment_pattern_is_atomic(tmp_path: Path) -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    before = serialize_concrete_artifact(_active(controller))
    path = tmp_path / "future-experiment.json"
    path.write_text(
        json.dumps(
            {
                "format_id": EXPERIMENT_DEFINITION_FORMAT_ID,
                "format_version": 1,
                "pattern_id": "future-pattern",
            }
        ),
        encoding="utf-8",
    )

    assert not controller.openStudy(str(path))

    assert controller.hasStudy
    assert serialize_concrete_artifact(_active(controller)) == before
    assert controller.statusTone == "error"


def test_exact_incompatible_open_preserves_current_study_and_surfaces_diagnostic(
    tmp_path: Path,
) -> None:
    controller = _controller()
    assert controller.createStudy("controlled-run")
    active = _active(controller)
    assert isinstance(active, StudyRevision)
    before = active.to_json()

    decoded = json.loads(before)
    manifest = json.loads(decoded["manifest_json"])
    manifest["recipe_version"] = 999
    decoded["manifest_json"] = json.dumps(manifest)
    path = tmp_path / "incompatible.json"
    path.write_text(json.dumps(decoded), encoding="utf-8")

    assert not controller.openStudy(str(path))

    assert isinstance(_active(controller), StudyRevision)
    assert serialize_concrete_artifact(_active(controller)) == before
    assert controller.status == "Exact reproduction unavailable."
    assert controller.statusTone == "error"
    assert controller.diagnosticMessage
    assert controller.diagnosticRemediation


def test_save_failure_is_atomic_and_does_not_replace_file_location(tmp_path: Path) -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    valid = tmp_path / "b3.json"
    assert controller.saveStudy(str(valid))
    before = serialize_concrete_artifact(_active(controller))
    before_location = controller.fileLocation

    impossible = tmp_path / "missing" / "nested" / "b3.json"
    assert not controller.saveStudy(str(impossible))

    assert serialize_concrete_artifact(_active(controller)) == before
    assert controller.fileLocation == before_location
    assert controller.statusTone == "error"


def test_canonical_b3_identity_and_supported_fork_are_truthfully_exposed() -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    parent = _active(controller)
    parent_revision = controller.revisionId

    assert controller.scenarioIdentity == B3_VALIDATED_SCENARIO_ID
    assert controller.canFork
    assert controller.forkStudy()

    child = _active(controller)
    assert controller.artifactKind == "b3-flagship"
    assert controller.parentRevisionId == parent_revision
    assert controller.scenarioOrigin
    assert controller.scenarioIdentity == ""
    assert not controller.canFork
    assert child != parent


def test_reference_scientific_change_clears_stale_result_run_plan_and_presentation(
    tmp_path: Path,
) -> None:
    revision = _compact_reference_revision()
    path = tmp_path / "reference.json"
    path.write_text(revision.to_json(), encoding="utf-8")
    controller = _controller()
    assert controller.openStudy(str(path))
    result = run_reference_study_revision(revision, run_id="q1-owner-test")
    assert controller.bind_result(result)
    controller.set_run_plan_open(True)
    owner = controller.presentationOwner
    epoch = controller.presentationEpoch
    assert owner
    assert controller.hasResult
    assert controller.runPlanOpen

    reference = cast(ReferenceStudyController, controller.referenceController)
    assert revision.intent.max_speed is not None
    reference.set_draft_max_speed(revision.intent.max_speed + 1)

    assert not controller.hasResult
    assert not controller.runPlanOpen
    assert controller.presentationOwner == ""
    assert controller.presentationEpoch > epoch


def test_replacing_active_artifact_rejects_old_result_and_resets_presentation(
    tmp_path: Path,
) -> None:
    revision = _compact_reference_revision()
    path = tmp_path / "reference.json"
    path.write_text(revision.to_json(), encoding="utf-8")
    controller = _controller()
    assert controller.openStudy(str(path))
    result = run_reference_study_revision(revision, run_id="q1-stale-test")
    assert controller.bind_result(result)
    epoch = controller.presentationEpoch

    assert controller.createStudy("b3-flagship")

    assert not controller.hasResult
    assert controller.presentationOwner == ""
    assert controller.presentationEpoch > epoch
    assert not controller.bind_result(result)
    assert controller.statusTone == "error"


def test_return_home_clears_active_artifact_and_family_specific_transient_state() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    reference = cast(ReferenceStudyController, controller.referenceController)
    assert reference.active
    assert reference._revision is not None
    assert reference._revision.intent.max_speed is not None
    reference.set_draft_max_speed(reference._revision.intent.max_speed + 1)
    assert reference.draftDirty

    controller.goHome()

    assert controller.route == "home"
    assert not controller.hasStudy
    assert not controller.hasResult
    assert not reference.active
    assert not reference.draftDirty


def test_reference_child_commit_becomes_new_active_exact_owner() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    reference = cast(ReferenceStudyController, controller.referenceController)
    parent_revision = controller.revisionId
    assert reference._revision is not None
    assert reference._revision.intent.max_speed is not None
    reference.set_draft_max_speed(reference._revision.intent.max_speed + 1)

    assert reference.saveChildRevision()

    assert controller.revisionId != parent_revision
    assert controller.parentRevisionId == parent_revision
    assert controller.fileLocation == ""
    assert not controller.hasResult
    assert controller.presentationOwner == ""


def test_incompatible_manifest_exception_type_remains_workbench_owned() -> None:
    assert issubclass(IncompatibleManifestError, ValueError)
