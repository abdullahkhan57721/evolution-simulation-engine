"""Focused WU3 tests for concrete run routing and immutable provenance attachment."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, TypeAlias

import pytest

import evo_engine.ui.run_execution as run_execution
from evo_engine.ui.run_execution import execute_artifact
from evo_engine.ui.study_shell import (
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
)
from evo_engine.workbench import (
    B3StudyRevision,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchRunProvenance,
)

RevisionOwnedArtifact: TypeAlias = StudyRevision | ReferenceStudyRevision | B3StudyRevision


def _provenance(
    revision: RevisionOwnedArtifact,
    *,
    run_id: str,
) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )


@pytest.mark.parametrize(
    ("factory", "runner_name"),
    (
        (lambda: new_controlled_run(revision_id="controlled"), "run_study_revision"),
        (
            lambda: new_reference_ecology(revision_id="reference"),
            "run_reference_study_revision",
        ),
        (lambda: new_b3_flagship(revision_id="b3"), "run_b3_study_revision"),
    ),
)
def test_revision_owned_execution_attaches_authoritative_run_provenance(
    monkeypatch: pytest.MonkeyPatch,
    factory: Callable[[], RevisionOwnedArtifact],
    runner_name: str,
) -> None:
    revision = factory()
    provenance = _provenance(revision, run_id=f"run-{runner_name}")
    result = SimpleNamespace(provenance=provenance)
    calls: list[object] = []

    def fake_runner(value: object) -> object:
        calls.append(value)
        return result

    monkeypatch.setattr(run_execution, runner_name, fake_runner)

    updated, returned = execute_artifact(revision)

    assert calls == [revision]
    assert returned is result
    assert revision.runs == ()
    assert updated.revision_id == revision.revision_id
    assert updated.manifest == revision.manifest
    assert updated.evidence_plan == revision.evidence_plan
    assert updated.runs == (provenance,)


def test_e3_and_e4_execution_delegate_to_existing_experiment_runners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    e3 = new_max_speed_sweep()
    e4 = new_environment_selection_comparison()
    e3_result = object()
    e4_result = object()
    calls: list[tuple[str, object]] = []

    def fake_e3(value: object) -> object:
        calls.append(("e3", value))
        return e3_result

    def fake_e4(value: object) -> object:
        calls.append(("e4", value))
        return e4_result

    monkeypatch.setattr(run_execution, "run_max_speed_sweep", fake_e3)
    monkeypatch.setattr(run_execution, "run_environment_selection_comparison", fake_e4)

    updated_e3, returned_e3 = execute_artifact(e3)
    updated_e4, returned_e4 = execute_artifact(e4)

    assert calls == [("e3", e3), ("e4", e4)]
    assert updated_e3 is e3
    assert updated_e4 is e4
    assert returned_e3 is e3_result
    assert returned_e4 is e4_result


def test_execution_failure_does_not_mutate_saved_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = new_controlled_run(revision_id="compile-failure")
    encoded = revision.to_json()

    def fail(_: object) -> object:
        raise RuntimeError("authoritative preflight rejected resolved configuration")

    monkeypatch.setattr(run_execution, "run_study_revision", fail)

    with pytest.raises(RuntimeError, match="authoritative preflight"):
        execute_artifact(revision)

    assert revision.to_json() == encoded
    assert revision.runs == ()
