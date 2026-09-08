"""Focused WU4 coverage for Results ownership, availability, and presentation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import attrs
import pytest

import evo_engine.ui.results_page as results_page
from evo_engine.experiments.e3_performance import E3TreatmentSummary, build_e3_treatment
from evo_engine.experiments.e4_selection import E4EnvironmentSummary
from evo_engine.ui.results_navigation import inspect_current_results, result_matches_artifact
from evo_engine.ui.results_tables import e3_summary_rows, e4_summary_rows
from evo_engine.ui.study_shell import (
    new_environment_selection_comparison,
    new_max_speed_sweep,
)
from evo_engine.workbench.controlled_locomotion import (
    POPULATION_EVIDENCE_ID,
    ControlledLocomotionIntent,
    EvidencePlan,
)
from evo_engine.workbench.experiments import (
    EnvironmentSelectionComparisonResult,
    MaxSpeedSweepResult,
)
from evo_engine.workbench.study import create_study_revision, run_study_revision


class _Context:
    def __enter__(self) -> _Context:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class _Column(_Context):
    def __init__(self, owner: _FakeStreamlit) -> None:
        self.owner = owner

    def metric(self, label: str, value: object, **_: Any) -> None:
        self.owner._record("metric", f"{label}: {value}")


class _FakeStreamlit:
    def __init__(self) -> None:
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

    def markdown(self, value: object, **_: Any) -> None:
        self._record("markdown", value)

    def code(self, value: object, **_: Any) -> None:
        self._record("code", value)

    def dataframe(self, value: object, **_: Any) -> None:
        self._record("dataframe", len(cast(Any, value)))

    def line_chart(self, value: object, **_: Any) -> None:
        self._record("line_chart", len(cast(Any, value)))

    def bar_chart(self, value: object, **_: Any) -> None:
        self._record("bar_chart", len(cast(Any, value)))

    def tabs(self, labels: tuple[str, ...]) -> tuple[_Context, ...]:
        self._record("tabs", " | ".join(labels))
        return tuple(_Context() for _ in labels)

    def columns(self, spec: int | tuple[int, ...]) -> tuple[_Column, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(_Column(self) for _ in range(count))

    def expander(self, label: str, **_: Any) -> _Context:
        self._record("expander", label)
        return _Context()


def _messages(fake: _FakeStreamlit, kind: str) -> list[str]:
    return [value for call_kind, value in fake.calls if call_kind == kind]


def test_controlled_missing_events_surfaces_unavailable_new_run_remediation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(results_page, "st", fake)
    revision = create_study_revision(
        revision_id="wu4-population-only",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=5,
        ),
        evidence_plan=EvidencePlan(requested=(POPULATION_EVIDENCE_ID,)),
    )
    result = run_study_revision(revision, run_id="wu4-population-only-run")

    results_page.render_results_page(revision, result)

    assert any("unavailable" in value.lower() for value in _messages(fake, "warning"))
    assert any("new run" in value.lower() for value in _messages(fake, "info"))
    assert any("retroactively" in value.lower() for value in _messages(fake, "info"))
    assert len(_messages(fake, "line_chart")) == 1


def test_results_reject_stale_revision_result_instead_of_displaying_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(results_page, "st", fake)
    first = create_study_revision(
        revision_id="wu4-first",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=5,
        ),
    )
    second = create_study_revision(
        revision_id="wu4-second",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=7,
        ),
    )
    result = run_study_revision(first, run_id="wu4-first-run")

    results_page.render_results_page(second, result)

    assert not result_matches_artifact(second, result)
    assert any("do not belong" in value.lower() for value in _messages(fake, "error"))
    assert not _messages(fake, "dataframe")


def test_reopened_revision_shows_provenance_only_without_rerun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(results_page, "st", fake)
    revision = create_study_revision(
        revision_id="wu4-history",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=5,
        ),
    )
    result = run_study_revision(revision, run_id="wu4-historical-run")
    reopened_shape = revision.with_run(result.provenance)

    results_page.render_results_page(reopened_shape, None)

    info = " ".join(_messages(fake, "info")).lower()
    assert "provenance references" in info
    assert "will not regenerate or rerun" in info
    assert _messages(fake, "dataframe")
    assert not _messages(fake, "line_chart")


def test_e3_and_e4_results_require_the_exact_immutable_definition() -> None:
    e3 = new_max_speed_sweep()
    e3_result = MaxSpeedSweepResult(
        definition=e3,
        treatments=(),
        replicate_outcomes=(),
        treatment_summaries=(),
    )
    changed_e3 = attrs.evolve(e3, levels=(1, 3))

    assert inspect_current_results(e3, e3_result).definition is e3
    with pytest.raises(ValueError, match="different immutable Experiment"):
        inspect_current_results(changed_e3, e3_result)

    e4 = new_environment_selection_comparison()
    e4_result = EnvironmentSelectionComparisonResult(
        definition=e4,
        treatments=(),
        replicate_outcomes=(),
        environment_summaries=cast(Any, ()),
    )
    changed_e4 = attrs.evolve(e4, seeds=(*e4.seeds, 997))

    assert inspect_current_results(e4, e4_result).definition is e4
    with pytest.raises(ValueError, match="different immutable Experiment"):
        inspect_current_results(changed_e4, e4_result)


def test_e3_summary_rows_copy_authoritative_treatment_values() -> None:
    treatment = build_e3_treatment(max_speed=3, environment="separated_corridor")
    summary = E3TreatmentSummary(
        treatment=treatment,
        replicate_count=2,
        seeds=(17, 29),
        birth_counts=(4, 8),
        mean_cumulative_birth_count=6.0,
        mean_final_population_size=7.5,
        mean_total_resource_consumed=19.0,
        mean_total_realized_distance=31.25,
        mean_total_locomotion_energy_expenditure=42.5,
        extinction_count=1,
    )

    row = e3_summary_rows((summary,))[0]

    assert row["Maximum speed"] == summary.treatment.max_speed
    assert row["Mean cumulative births"] == summary.mean_cumulative_birth_count
    assert row["Mean realized distance"] == summary.mean_total_realized_distance
    assert row["Extinctions"] == summary.extinction_count


def test_e4_summary_rows_preserve_environment_and_strategy_separation() -> None:
    summary = E4EnvironmentSummary(
        environment="separated_corridor",
        replicate_count=2,
        seeds=(5, 7),
        founder_speed_orders=((1, 3, 9), (3, 9, 1)),
        mean_final_frequencies=(0.1, 0.3, 0.6),
        mean_frequency_changes=(-0.2, 0.0, 0.2),
        defined_endpoint_count=2,
        extinction_count=0,
        mean_births_by_speed=(1.0, 2.0, 3.0),
        mean_resources_by_speed=(4.0, 5.0, 6.0),
        mean_realized_distance_by_speed=(7.0, 8.0, 9.0),
        mean_locomotion_energy_by_speed=(10.0, 11.0, 12.0),
    )

    rows = e4_summary_rows((summary,))

    assert tuple(row["Maximum speed strategy"] for row in rows) == (1, 3, 9)
    assert all(row["Environment"] == "Separated Corridor" for row in rows)
    assert tuple(row["Mean frequency change"] for row in rows) == (
        summary.mean_frequency_changes
    )
    assert all("Founder" not in key for row in rows for key in row)


def test_results_modules_do_not_execute_engine_or_define_scientific_estimators() -> None:
    root = Path(__file__).resolve().parents[2]
    sources = tuple(
        (root / path).read_text(encoding="utf-8")
        for path in (
            "src/evo_engine/ui/results_navigation.py",
            "src/evo_engine/ui/results_page.py",
            "src/evo_engine/ui/results_tables.py",
        )
    )

    assert all("SimulationEngine" not in source for source in sources)
    assert all("from evo_engine.engine" not in source for source in sources)
    assert all("summarize_e3_treatment" not in source for source in sources)
    assert all("summarize_e4_environment" not in source for source in sources)
    assert all("summarize_locomotion_replicate" not in source for source in sources)
    assert "Primary confirmation" in sources[1]
    assert "Radius sensitivity" in sources[1]
    assert "Founder-label counterbalance" in sources[1]
