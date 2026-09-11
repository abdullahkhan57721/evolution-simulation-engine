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
import evo_engine.workbench.execution as workbench_execution
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

    def success(self, value: object, **_: Any) -> None:
        self._record("success", value)

    def code(self, value: object, **_: Any) -> None:
        self._record("code", value)

    def divider(self) -> None:
        self._record("divider")

    def metric(self, label: object, value: object, **_: Any) -> None:
        self._record("metric", f"{label}: {value}")

    def table(self, value: object, **_: Any) -> None:
        self._record("table", value)

    def dataframe(self, value: object, **_: Any) -> None:
        self._record("dataframe", value)

    def checkbox(self, label: str, *, value: bool = False, **_: Any) -> bool:
        self._record("checkbox", label)
        return self.checkbox_values.get(label, value)

    def button(self, label: str, **_: Any) -> bool:
        self._record("button", label)
        return label in self.button_values

    def multiselect(
        self,
        label: str,
        options: list[int] | tuple[int, ...],
        *,
        default: list[int] | tuple[int, ...] | None = None,
        **_: Any,
    ) -> list[int]:
        self._record("multiselect", label)
        if label in self.multiselect_values:
            return self.multiselect_values[label]
        return list(default or options)

    def text_input(self, label: str, *, value: str = "", **_: Any) -> str:
        self._record("text_input", label)
        return self.text_input_values.get(label, value)

    def columns(self, count: int, **_: Any) -> tuple[_Context, ...]:
        return tuple(_Context() for _ in range(count))

    def expander(self, *_: Any, **__: Any) -> _Context:
        return _Context()


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> _FakeStreamlit:
    fake = _FakeStreamlit()
    for module in (evidence_page, experiment_page, run_page, run_binding):
        monkeypatch.setattr(module, "st", fake)
    return fake


def test_evidence_page_edits_reference_plan_and_saves_child(fake: _FakeStreamlit) -> None:
    revision = new_reference_ecology(revision_id="reference-evidence")
    initial_requested = revision.evidence_plan.requested
    option = evidence_authoring.evidence_options(revision)[-1]
    assert option.evidence_id == SPATIAL_EVIDENCE_ID
    fake.checkbox_values[option.label] = False
    fake.button_values.add("Save Evidence as child revision")

    updated = evidence_page.render_evidence_page(revision)

    assert updated is not None
    assert updated.parent_revision_id == revision.revision_id
    assert updated.evidence_plan.requested != initial_requested
    assert SPATIAL_EVIDENCE_ID not in updated.evidence_plan.requested


def test_evidence_page_reports_locked_experiment_evidence(fake: _FakeStreamlit) -> None:
    definition = new_max_speed_sweep()

    assert evidence_page.render_evidence_page(definition) is None

    assert any(
        kind == "info" and "locked" in value.lower() for kind, value in fake.calls
    )


def test_evidence_page_reports_required_missing_evidence(fake: _FakeStreamlit) -> None:
    revision = new_controlled_run(revision_id="controlled-evidence")
    fake.session_state["wu2_evidence_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_evidence_draft_plan"] = EvidencePlan(requested=())

    assert evidence_page.render_evidence_page(revision) is None

    assert any(
        kind == "warning" and "requires" in value.lower() for kind, value in fake.calls
    )


def test_experiment_page_max_speed_sweep_persists_valid_pending_definition(
    fake: _FakeStreamlit,
) -> None:
    definition = new_max_speed_sweep()
    fake.multiselect_values["Maximum speed levels"] = [1, 4]
    fake.text_input_values["Replicate seeds"] = "101, 202"

    experiment_page.render_experiment_page(definition)

    pending = experiment_page.pending_experiment_definition(definition)
    assert pending is not None
    assert pending.levels == (1, 4)
    assert pending.seeds == (101, 202)
    assert experiment_page.pending_experiment_error(definition) is None


def test_experiment_page_environment_selection_rejects_invalid_seed_input(
    fake: _FakeStreamlit,
) -> None:
    definition = new_environment_selection_comparison()
    fake.text_input_values["Replicate seeds"] = "not-an-int"

    experiment_page.render_experiment_page(definition)

    assert experiment_page.pending_experiment_definition(definition) is None
    assert experiment_page.pending_experiment_error(definition) is not None


def test_experiment_page_b3_is_read_only_design(fake: _FakeStreamlit) -> None:
    revision = new_b3_flagship(revision_id="b3-experiment")

    experiment_page.render_experiment_page(revision)

    assert any(
        kind == "info" and "frozen" in value.lower() for kind, value in fake.calls
    )


def test_pending_experiment_definition_ignores_another_owner(fake: _FakeStreamlit) -> None:
    first = new_max_speed_sweep()
    second = attrs.evolve(first, seeds=(999,))
    fake.session_state["wu3_experiment_owner"] = experiment_page._owner_value(first)
    fake.session_state["wu3_experiment_candidate"] = second

    assert experiment_page.pending_experiment_definition(second) is None
    assert experiment_page.pending_experiment_error(second) is None


def test_run_plan_controlled_and_reference_surface_binding_notice(
    fake: _FakeStreamlit,
) -> None:
    controlled = new_controlled_run(revision_id="controlled-plan")
    reference = new_reference_ecology(revision_id="reference-plan")

    run_page.render_run_plan(
        controlled,
        readiness=run_binding.effective_readiness(controlled),
        binding_notice="controlled binding",
    )
    run_page.render_run_plan(
        reference,
        readiness=run_binding.effective_readiness(reference),
        binding_notice="reference binding",
    )

    values = [value for _, value in fake.calls]
    assert any("controlled binding" in value for value in values)
    assert any("reference binding" in value for value in values)


def test_run_plan_experiment_and_b3_surfaces_design(fake: _FakeStreamlit) -> None:
    sweep = new_max_speed_sweep()
    environment = new_environment_selection_comparison()
    b3 = new_b3_flagship(revision_id="b3-plan")

    run_page.render_run_plan(
        sweep,
        readiness=run_binding.effective_readiness(sweep),
        binding_notice=None,
    )
    run_page.render_run_plan(
        environment,
        readiness=run_binding.effective_readiness(environment),
        binding_notice=None,
    )
    run_page.render_run_plan(
        b3,
        readiness=run_binding.effective_readiness(b3),
        binding_notice=None,
    )

    values = [value for _, value in fake.calls]
    assert any("Maximum speed" in value for value in values)
    assert any("Resource geography" in value for value in values)
    assert any("Matched comparison" in value for value in values)


def test_run_plan_reports_not_ready_diagnostic(fake: _FakeStreamlit) -> None:
    revision = new_controlled_run(revision_id="controlled-not-ready")
    fake.session_state["wu2_evidence_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_evidence_draft_plan"] = EvidencePlan(requested=())

    readiness = run_binding.effective_readiness(revision)
    run_page.render_run_plan(revision, readiness=readiness, binding_notice=None)

    assert not readiness.is_ready
    assert any(kind == "warning" for kind, _ in fake.calls)


def test_run_plan_renders_reference_advisories(fake: _FakeStreamlit) -> None:
    revision = new_reference_ecology(revision_id="reference-advisory")
    fake.session_state["wu2_evidence_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_evidence_draft_plan"] = EvidencePlan(
        requested=("population",)
    )

    run_page.render_run_plan(
        revision,
        readiness=run_binding.effective_readiness(revision),
        binding_notice=None,
    )

    assert any(
        kind == "info" and "advisory" in value.lower() for kind, value in fake.calls
    )


def test_bind_pending_scientific_state_combines_controlled_drafts(
    fake: _FakeStreamlit,
) -> None:
    revision = new_controlled_run(revision_id="controlled-bind")
    simulation_intent = attrs.evolve(revision.intent, max_speed=7)
    evidence_plan = EvidencePlan(requested=("population",))
    fake.session_state["wu2_simulation_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = simulation_intent
    fake.session_state["wu2_evidence_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_evidence_draft_plan"] = evidence_plan

    bound, notice = run_binding.bind_pending_scientific_state(revision)

    assert bound.revision_id != revision.revision_id
    assert bound.parent_revision_id == revision.revision_id
    assert bound.intent.max_speed == 7
    assert bound.evidence_plan == evidence_plan
    assert notice is not None
    assert "Simulation" in notice and "Evidence" in notice


def test_bind_pending_scientific_state_combines_reference_drafts(
    fake: _FakeStreamlit,
) -> None:
    revision = new_reference_ecology(revision_id="reference-bind")
    simulation_intent = attrs.evolve(revision.intent, max_speed=4)
    evidence_plan = EvidencePlan(requested=("population",))
    fake.session_state["wu2_simulation_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_simulation_draft_intent"] = simulation_intent
    fake.session_state["wu2_evidence_draft_revision_id"] = revision.revision_id
    fake.session_state["wu2_evidence_draft_plan"] = evidence_plan

    bound, notice = run_binding.bind_pending_scientific_state(revision)

    assert bound.revision_id != revision.revision_id
    assert bound.parent_revision_id == revision.revision_id
    assert bound.intent.max_speed == 4
    assert bound.evidence_plan == evidence_plan
    assert notice is not None
    assert "Simulation" in notice and "Evidence" in notice


def test_bind_pending_scientific_state_uses_pending_experiment_definition(
    fake: _FakeStreamlit,
) -> None:
    definition = new_max_speed_sweep()
    pending = attrs.evolve(definition, seeds=(101, 202))
    fake.session_state["wu3_experiment_owner"] = experiment_page._owner_value(definition)
    fake.session_state["wu3_experiment_candidate"] = pending

    bound, notice = run_binding.bind_pending_scientific_state(definition)

    assert bound == pending
    assert notice is not None
    assert "Experiment" in notice


def test_bind_pending_scientific_state_blocks_invalid_experiment_draft(
    fake: _FakeStreamlit,
) -> None:
    definition = new_max_speed_sweep()
    fake.session_state["wu3_experiment_owner"] = experiment_page._owner_value(definition)
    fake.session_state["wu3_experiment_invalid"] = "invalid pending experiment"

    with pytest.raises(WorkbenchNotReadyError, match="invalid pending experiment"):
        run_binding.bind_pending_scientific_state(definition)


def test_effective_readiness_respects_pending_experiment_definition(
    fake: _FakeStreamlit,
) -> None:
    definition = new_max_speed_sweep()
    fake.session_state["wu3_experiment_owner"] = experiment_page._owner_value(definition)
    fake.session_state["wu3_experiment_invalid"] = "invalid pending experiment"

    readiness = run_binding.effective_readiness(definition)

    assert not readiness.is_ready
    assert readiness.blocking_diagnostics[0].message == "invalid pending experiment"


def test_evidence_authoring_helpers_preserve_locked_experiment_plans() -> None:
    definition = new_max_speed_sweep()

    assert evidence_authoring.make_editable_evidence_plan(definition) is None
    assert evidence_authoring.requested_evidence_ids(definition) == (
        definition.evidence_plan.requested
    )
    assert evidence_authoring.evidence_advisories_for_artifact(definition) == ()


def test_experiment_authoring_helpers_cover_design_rows_and_parsers() -> None:
    sweep = new_max_speed_sweep()
    environment = new_environment_selection_comparison()

    updated_sweep = experiment_authoring.update_max_speed_sweep(
        sweep,
        levels=(1, 4),
        seeds=(101, 202),
    )
    assert updated_sweep.levels == (1, 4)
    assert updated_sweep.seeds == (101, 202)
    assert experiment_authoring.max_speed_run_rows(updated_sweep)

    updated_environment = experiment_authoring.update_environment_selection_comparison(
        environment,
        seeds=(101, 202),
    )
    assert updated_environment.seeds == (101, 202)
    assert experiment_authoring.environment_run_rows(updated_environment)
    assert experiment_authoring.e4_counterbalance_label(updated_environment)
    assert experiment_authoring.b3_case_counts(new_b3_flagship())
    assert experiment_authoring.parse_integer_sequence("1, 2, 3", field="Seeds") == (
        1,
        2,
        3,
    )
    with pytest.raises(ValueError, match="at least one integer"):
        experiment_authoring.parse_integer_sequence("", field="Seeds")
    with pytest.raises(ValueError, match="integers"):
        experiment_authoring.parse_integer_sequence("one", field="Seeds")


def test_run_binding_private_pending_helpers_validate_owner(fake: _FakeStreamlit) -> None:
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

    monkeypatch.setattr(workbench_execution, "WorkbenchRunResult", RevisionResult)
    monkeypatch.setattr(workbench_execution, "ReferenceRunResult", ReferenceResult)
    monkeypatch.setattr(workbench_execution, "B3CuratedRunResult", B3Result)
    monkeypatch.setattr(workbench_execution, "MaxSpeedSweepResult", ExperimentResult)
    monkeypatch.setattr(
        workbench_execution,
        "EnvironmentSelectionComparisonResult",
        ExperimentResult,
    )
    monkeypatch.setattr(
        workbench_execution,
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
