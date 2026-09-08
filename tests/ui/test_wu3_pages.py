"""Behavioral coverage for WU3 Evidence, Experiment, Run Plan, and binding UI."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import attrs
import pytest

import evo_engine.ui.evidence_authoring as evidence_authoring
import evo_engine.ui.evidence_page as evidence_page
import evo_engine.ui.experiment_authoring as experiment_authoring
import evo_engine.ui.experiment_page as experiment_page
import evo_engine.ui.run_binding as run_binding
import evo_engine.ui.run_execution as run_execution
import evo_engine.ui.run_page as run_page
from evo_engine.ui.study_shell import (
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
)
from evo_engine.workbench import (
    ControlledLocomotionIntent,
    EvidencePlan,
    WorkbenchNotReadyError,
)
from evo_engine.workbench.reference_ecology import SPATIAL_EVIDENCE_ID


class _Context:
    def __enter__(self) -> _Context:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class _FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, Any] = {}
        self.checkbox_values: dict[str, bool] = {}
        self.button_values: set[str] = set()
        self.multiselect_values: dict[str, list[int]] = {}
        self.text_input_values: dict[str, str] = {}
        self.calls: list[tuple[str, str]] = []

    def _record(self, kind: str, value: object = "") -> None:
        self.calls.append((kind, str(value)))

    def header(self, value: object, **_: Any) -> None:
        self._record("header", value)

    def subheader(self, value: object, **_: Any) -> None:
        self._record("subheader", value)

    def write(self, value: object, **_: Any) -> None:
        self._record("write", value)

    def caption(self, value: object, **_: Any) -> None:
        self._record("caption", value)

    def info(self, value: object, **_: Any) -> None:
        self._record("info", value)

    def warning(self, value: object, **_: Any) -> None:
        self._record("warning", value)

    def error(self, value: object, **_: Any) -> None:
        self._record("error", value)

    def markdown(self, value: object, **_: Any) -> None:
        self._record("markdown", value)

    def code(self, value: object, **_: Any) -> None:
        self._record("code", value)

    def divider(self) -> None:
        self._record("divider")

    def dataframe(self, value: object, **_: Any) -> None:
        self._record("dataframe", len(cast(Any, value)))

    def checkbox(self, label: str, *, value: bool = False, **_: Any) -> bool:
        self._record("checkbox", label)
        return self.checkbox_values.get(label, value)

    def button(self, label: str, **_: Any) -> bool:
        self._record("button", label)
        return label in self.button_values

    def multiselect(
        self,
        label: str,
        _options: object,
        *,
        default: list[int],
        **_: Any,
    ) -> list[int]:
        self._record("multiselect", label)
        return self.multiselect_values.get(label, default)

    def text_input(self, label: str, *, value: str, **_: Any) -> str:
        self._record("text_input", label)
        return self.text_input_values.get(label, value)

    def columns(self, spec: int | tuple[int, ...]) -> tuple[_Context, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(_Context() for _ in range(count))

    def expander(self, label: str, **_: Any) -> _Context:
        self._record("expander", label)
        return _Context()


def _messages(fake: _FakeStreamlit, kind: str) -> list[str]:
    return [value for call_kind, value in fake.calls if call_kind == kind]


def test_evidence_page_edits_controlled_revision_and_clears_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(evidence_page, "st", fake)
    parent = new_controlled_run(revision_id="controlled-parent")
    fake.checkbox_values["Committed events"] = False
    fake.button_values.add("Save Evidence as new revision")

    child = evidence_page.render_evidence_page(
        parent,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )

    assert child is not None
    assert child.parent_revision_id == parent.revision_id
    assert child.evidence_plan.requested == (parent.evidence_plan.requested[0],)
    assert evidence_page.pending_evidence_plan(parent) is not None
    fake.session_state["wu3_evidence_extra"] = object()
    evidence_page.clear_evidence_authoring_state()
    assert not any(str(key).startswith("wu3_evidence_") for key in fake.session_state)


def test_evidence_page_reference_advisory_and_locked_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(evidence_page, "st", fake)
    reference = new_reference_ecology(revision_id="reference-parent")
    fake.checkbox_values["Spatial history"] = True
    fake.button_values.add("Save Evidence as new revision")

    child = evidence_page.render_evidence_page(
        reference,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )

    assert child is not None
    assert SPATIAL_EVIDENCE_ID in child.evidence_plan.requested
    assert any("volume" in message.lower() for message in _messages(fake, "warning"))

    for artifact in (
        new_b3_flagship(revision_id="b3-locked"),
        new_max_speed_sweep(),
        new_environment_selection_comparison(),
    ):
        evidence_page.render_evidence_page(
            artifact,
            new_revision_id=lambda prefix: f"{prefix}-unused",
        )
    assert _messages(fake, "checkbox")


def test_evidence_authoring_rejects_wrong_concrete_types() -> None:
    controlled = new_controlled_run(revision_id="controlled")
    reference = new_reference_ecology(revision_id="reference")

    with pytest.raises(TypeError, match="revision-backed"):
        evidence_authoring.make_editable_evidence_plan(
            cast(Any, new_max_speed_sweep()),
            (),
        )
    with pytest.raises(TypeError, match="Unsupported artifact"):
        evidence_authoring.evidence_options(cast(Any, object()))
    with pytest.raises(TypeError, match="Reference Ecology advisories"):
        evidence_authoring.evidence_advisories_for_artifact(
            reference,
            plan=cast(Any, EvidencePlan()),
        )
    assert evidence_authoring.evidence_advisories_for_artifact(controlled) == ()


def test_experiment_page_renders_nonexperiment_and_b3_modes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(experiment_page, "st", fake)

    assert (
        experiment_page.render_experiment_page(new_controlled_run(revision_id="single"))
        is None
    )
    assert (
        experiment_page.render_experiment_page(
            new_reference_ecology(revision_id="reference")
        )
        is None
    )
    assert (
        experiment_page.render_experiment_page(new_b3_flagship(revision_id="b3"))
        is None
    )
    assert any("frozen" in message.lower() for message in _messages(fake, "info"))


def test_experiment_page_applies_e3_and_e4_definitions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(experiment_page, "st", fake)
    e3 = new_max_speed_sweep()
    fake.multiselect_values["Maximum-speed levels"] = [1, 3, 5]
    fake.text_input_values["Replicate seeds"] = "17, 29"
    fake.button_values.add("Apply experiment design")

    e3_candidate = experiment_page.render_experiment_page(e3)

    assert e3_candidate is not None
    assert e3_candidate.levels == (1, 3, 5)
    assert e3_candidate.seeds == (17, 29)
    assert experiment_page.pending_experiment_definition(e3) == e3_candidate

    fake = _FakeStreamlit()
    monkeypatch.setattr(experiment_page, "st", fake)
    e4 = new_environment_selection_comparison()
    fake.text_input_values["Replicate seeds"] = "101, 202"
    fake.button_values.add("Apply experiment design")

    e4_candidate = experiment_page.render_experiment_page(e4)

    assert e4_candidate is not None
    assert e4_candidate.seeds == (101, 202)
    assert experiment_page.pending_experiment_definition(e4) == e4_candidate


def test_experiment_page_invalid_draft_is_owned_and_clearable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(experiment_page, "st", fake)
    e3 = new_max_speed_sweep()
    fake.text_input_values["Replicate seeds"] = "17,,29"

    assert experiment_page.render_experiment_page(e3) is None
    assert experiment_page.pending_experiment_definition(e3) is None
    assert experiment_page.pending_experiment_error(e3) is not None
    assert _messages(fake, "error")

    fake.session_state["wu3_experiment_extra"] = object()
    experiment_page.clear_experiment_authoring_state()
    assert not any(str(key).startswith("wu3_experiment_") for key in fake.session_state)


def test_experiment_authoring_parser_and_type_guards() -> None:
    assert experiment_authoring.parse_integer_sequence("", name="Seeds") == ()
    assert experiment_authoring.parse_integer_sequence("1, 2", name="Seeds") == (1, 2)
    with pytest.raises(TypeError, match="string"):
        experiment_authoring.parse_integer_sequence(cast(Any, 1), name="Seeds")
    with pytest.raises(TypeError, match="non-empty"):
        experiment_authoring.parse_integer_sequence("1", name="")
    with pytest.raises(ValueError, match="empty value"):
        experiment_authoring.parse_integer_sequence("1,,2", name="Seeds")
    with pytest.raises(ValueError, match="not an integer"):
        experiment_authoring.parse_integer_sequence("one", name="Seeds")
    with pytest.raises(TypeError, match="MaxSpeedSweepDefinition"):
        experiment_authoring.update_max_speed_sweep(
            cast(Any, object()),
            levels=(1,),
            seeds=(1,),
        )
    with pytest.raises(TypeError, match="EnvironmentSelectionComparisonDefinition"):
        experiment_authoring.update_environment_selection_comparison(
            cast(Any, object()),
            seeds=(1,),
        )
    with pytest.raises(TypeError, match="B3StudyRevision"):
        experiment_authoring.b3_case_counts(cast(Any, object()))


def test_run_plan_renders_every_supported_concrete_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(run_page, "st", fake)
    reference = new_reference_ecology(revision_id="reference-plan")
    reference_with_spatial = evidence_authoring.save_evidence_child(
        reference,
        requested=(*reference.evidence_plan.requested, SPATIAL_EVIDENCE_ID),
        revision_id="reference-spatial",
    )

    for artifact in (
        new_controlled_run(revision_id="controlled-plan"),
        reference_with_spatial,
        new_b3_flagship(revision_id="b3-plan"),
        new_max_speed_sweep(),
        new_environment_selection_comparison(),
    ):
        assert (
            run_page.render_run_plan(artifact, binding_notice="Bound exact draft")
            is None
        )

    assert len(_messages(fake, "subheader")) == 5
    assert _messages(fake, "dataframe")
    assert any(
        "advis" in message.lower() or "volume" in message.lower()
        for message in _messages(fake, "warning")
    )


def test_run_plan_cancel_run_and_unsupported_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = new_controlled_run(revision_id="controlled-actions")
    fake = _FakeStreamlit()
    fake.button_values.add("Cancel Run Plan")
    monkeypatch.setattr(run_page, "st", fake)
    assert run_page.render_run_plan(artifact) == "cancel"

    fake = _FakeStreamlit()
    fake.button_values.add("Run Study")
    monkeypatch.setattr(run_page, "st", fake)
    assert run_page.render_run_plan(artifact) == "run"

    with pytest.raises(TypeError, match="Unsupported Workbench artifact"):
        run_page.render_run_plan(cast(Any, object()))


def test_run_binding_revision_experiment_and_b3_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(run_binding, "st", fake)
    monkeypatch.setattr(run_binding, "pending_evidence_plan", lambda _: None)
    controlled = new_controlled_run(revision_id="controlled-bind")

    unchanged, notice = run_binding.bind_pending_scientific_state(
        controlled,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )
    assert unchanged is controlled
    assert notice is None

    fake.session_state["wu2_simulation_draft_revision_id"] = controlled.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = attrs.evolve(
        controlled.intent,
        seed=cast(int, controlled.intent.seed) + 1,
    )
    child, notice = run_binding.bind_pending_scientific_state(
        controlled,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )
    assert child is not controlled
    assert notice is not None

    e3 = new_max_speed_sweep()
    candidate = experiment_authoring.update_max_speed_sweep(
        e3,
        levels=(1, 3),
        seeds=(7,),
    )
    monkeypatch.setattr(run_binding, "pending_experiment_error", lambda _: None)
    monkeypatch.setattr(
        run_binding, "pending_experiment_definition", lambda _: candidate
    )
    bound_e3, notice = run_binding.bind_pending_scientific_state(
        e3,
        new_revision_id=lambda prefix: prefix,
    )
    assert bound_e3 == candidate
    assert notice is not None

    b3 = new_b3_flagship(revision_id="b3-bind")
    assert run_binding.bind_pending_scientific_state(
        b3,
        new_revision_id=lambda prefix: prefix,
    ) == (b3, None)


def test_run_binding_reference_blocked_error_and_readiness_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(run_binding, "st", fake)
    monkeypatch.setattr(run_binding, "pending_evidence_plan", lambda _: None)
    reference = new_reference_ecology(revision_id="reference-bind")
    fake.session_state["wu2_simulation_draft_revision_id"] = reference.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = attrs.evolve(
        reference.intent,
        seed=cast(int, reference.intent.seed) + 1,
    )

    child, notice = run_binding.bind_pending_scientific_state(
        reference,
        new_revision_id=lambda prefix: f"{prefix}-child",
    )
    assert child is not reference
    assert notice is not None

    controlled = new_controlled_run(revision_id="blocked")
    fake.session_state["wu2_simulation_draft_revision_id"] = controlled.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = ControlledLocomotionIntent()
    with pytest.raises(WorkbenchNotReadyError):
        run_binding.bind_pending_scientific_state(
            controlled,
            new_revision_id=lambda prefix: prefix,
        )

    e4 = new_environment_selection_comparison()
    monkeypatch.setattr(run_binding, "pending_experiment_error", lambda _: "bad seeds")
    with pytest.raises(ValueError, match="bad seeds"):
        run_binding.bind_pending_scientific_state(
            e4,
            new_revision_id=lambda prefix: prefix,
        )

    for artifact in (
        controlled,
        reference,
        new_b3_flagship(revision_id="b3-ready"),
        new_max_speed_sweep(),
        e4,
    ):
        run_binding.effective_readiness(artifact)
    with pytest.raises(TypeError, match="Unsupported Workbench artifact"):
        run_binding.effective_readiness(cast(Any, object()))


def test_run_binding_private_pending_intent_ownership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(run_binding, "st", fake)
    controlled = new_controlled_run(revision_id="controlled-private")
    reference = new_reference_ecology(revision_id="reference-private")

    assert run_binding._pending_controlled_intent(controlled) is None
    assert run_binding._pending_reference_intent(reference) is None

    fake.session_state["wu2_simulation_draft_revision_id"] = controlled.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = controlled.intent
    assert run_binding._pending_controlled_intent(controlled) == controlled.intent

    fake.session_state["wu2_simulation_draft_revision_id"] = reference.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = reference.intent
    assert run_binding._pending_reference_intent(reference) == reference.intent


def test_run_execution_result_helpers_cover_all_owned_result_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class RevisionResult:
        def __init__(self) -> None:
            self.provenance = SimpleNamespace(
                run_id="run-1",
                study_revision_id="revision-1",
                evidence_ids=("population", "events"),
            )

    class ReferenceResult:
        def __init__(self) -> None:
            self.provenance = SimpleNamespace(
                run_id="run-reference",
                study_revision_id="reference-1",
                evidence_ids=("reference-population",),
            )

    class B3Result:
        def __init__(self) -> None:
            self.provenance = SimpleNamespace(
                run_id="run-b3",
                study_revision_id="b3-1",
                evidence_ids=("b3-population",),
            )
            self.confirmation = (1, 2)
            self.radius_sensitivity = (1,)
            self.counterbalanced = (1, 2, 3)

    class ExperimentResult:
        def __init__(self) -> None:
            self.definition = SimpleNamespace(
                evidence_plan=SimpleNamespace(requested=("experiment-evidence",))
            )
            self.treatments = (1, 2, 3, 4)

    monkeypatch.setattr(run_execution, "WorkbenchRunResult", RevisionResult)
    monkeypatch.setattr(run_execution, "ReferenceRunResult", ReferenceResult)
    monkeypatch.setattr(run_execution, "B3CuratedRunResult", B3Result)
    monkeypatch.setattr(run_execution, "MaxSpeedSweepResult", ExperimentResult)
    monkeypatch.setattr(
        run_execution,
        "EnvironmentSelectionComparisonResult",
        ExperimentResult,
    )
    monkeypatch.setattr(
        run_execution,
        "_RESULT_TYPES",
        (RevisionResult, ReferenceResult, B3Result, ExperimentResult),
    )

    revision: Any = RevisionResult()
    reference: Any = ReferenceResult()
    b3: Any = B3Result()
    experiment: Any = ExperimentResult()

    assert run_execution.is_authoritative_run_result(revision)
    assert not run_execution.is_authoritative_run_result(object())
    assert run_execution.result_run_id(revision) == "run-1"
    assert run_execution.result_run_id(experiment) is None
    assert run_execution.result_revision_id(reference) == "reference-1"
    assert run_execution.result_revision_id(experiment) is None
    assert run_execution.result_evidence_ids(b3) == ("b3-population",)
    assert run_execution.result_evidence_ids(experiment) == ("experiment-evidence",)
    assert run_execution.result_simulation_count(revision) == 1
    assert run_execution.result_simulation_count(reference) == 1
    assert run_execution.result_simulation_count(b3) == 11
    assert run_execution.result_simulation_count(experiment) == 4

    with pytest.raises(TypeError, match="Unsupported Workbench artifact"):
        run_execution.execute_artifact(cast(Any, object()))
