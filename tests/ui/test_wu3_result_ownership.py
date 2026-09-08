"""WU3 tests for clearing session results when scientific ownership changes."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import attrs
import pytest

import evo_engine.ui.run_binding as run_binding
from evo_engine.ui.experiment_authoring import update_max_speed_sweep
from evo_engine.ui.study_shell import new_controlled_run, new_max_speed_sweep

_RESULT_KEY = "wu1_current_result"
_SIMULATION_DRAFT_INTENT_KEY = "wu2_simulation_draft_intent"
_SIMULATION_DRAFT_REVISION_KEY = "wu2_simulation_draft_revision_id"


def test_binding_new_revision_clears_result_owned_by_previous_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = new_controlled_run(revision_id="controlled-parent")
    prior_result = object()
    session_state: dict[str, Any] = {
        _RESULT_KEY: prior_result,
        _SIMULATION_DRAFT_REVISION_KEY: parent.revision_id,
        _SIMULATION_DRAFT_INTENT_KEY: attrs.evolve(
            parent.intent,
            seed=cast(int, parent.intent.seed) + 1,
        ),
    }
    monkeypatch.setattr(run_binding, "st", SimpleNamespace(session_state=session_state))
    monkeypatch.setattr(run_binding, "pending_evidence_plan", lambda _: None)

    child, notice = run_binding.bind_pending_scientific_state(
        parent,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )

    assert child is not parent
    assert notice is not None
    assert _RESULT_KEY not in session_state


def test_binding_new_experiment_definition_clears_previous_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = new_max_speed_sweep()
    candidate = update_max_speed_sweep(
        definition,
        levels=(1, 3),
        seeds=(7,),
    )
    prior_result = object()
    session_state: dict[str, Any] = {_RESULT_KEY: prior_result}
    monkeypatch.setattr(run_binding, "st", SimpleNamespace(session_state=session_state))
    monkeypatch.setattr(run_binding, "pending_experiment_error", lambda _: None)
    monkeypatch.setattr(
        run_binding,
        "pending_experiment_definition",
        lambda _: candidate,
    )

    bound, notice = run_binding.bind_pending_scientific_state(
        definition,
        new_revision_id=lambda prefix: prefix,
    )

    assert bound == candidate
    assert notice is not None
    assert _RESULT_KEY not in session_state


def test_unchanged_owner_preserves_current_result_until_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = new_controlled_run(revision_id="controlled-unchanged")
    prior_result = object()
    session_state: dict[str, Any] = {_RESULT_KEY: prior_result}
    monkeypatch.setattr(run_binding, "st", SimpleNamespace(session_state=session_state))
    monkeypatch.setattr(run_binding, "pending_evidence_plan", lambda _: None)

    bound, notice = run_binding.bind_pending_scientific_state(
        parent,
        new_revision_id=lambda prefix: f"{prefix}-unused",
    )

    assert bound is parent
    assert notice is None
    assert session_state[_RESULT_KEY] is prior_result
