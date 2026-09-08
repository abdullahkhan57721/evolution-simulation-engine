"""Focused WU4 coverage for Results ownership, availability, and presentation."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import attrs
import pytest

import evo_engine.ui.results_page as results_page
from evo_engine.experiments.e3_performance import E3TreatmentSummary, build_e3_treatment
from evo_engine.experiments.e4_selection import E4EnvironmentSummary
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.ui.results_navigation import (
    inspect_current_results,
    result_matches_artifact,
)
from evo_engine.ui.results_tables import e3_summary_rows, e4_summary_rows
from evo_engine.ui.study_shell import (
    new_b3_flagship,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
)
from evo_engine.workbench.b3_curated import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3CuratedRunResult,
    B3MatchedRunArtifacts,
    B3SingleRunArtifacts,
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
from evo_engine.workbench.reference_study import ReferenceRunResult
from evo_engine.workbench.results import (
    AnalysisAvailability,
    B3ResultsView,
    EnvironmentSelectionResultsView,
    MaxSpeedSweepResultsView,
    ReferenceStudyResultsView,
)
from evo_engine.workbench.study import (
    WorkbenchRunProvenance,
    create_study_revision,
    run_study_revision,
)


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
        self.selections: dict[str, object] = {}

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

    def tabs(self, labels: Sequence[str]) -> tuple[_Context, ...]:
        self._record("tabs", " | ".join(labels))
        return tuple(_Context() for _ in labels)

    def columns(self, spec: int | Sequence[int]) -> tuple[_Column, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(_Column(self) for _ in range(count))

    def expander(self, label: str, **_: Any) -> _Context:
        self._record("expander", label)
        return _Context()

    def selectbox(
        self,
        label: str,
        options: Sequence[Any],
        *,
        key: str | None = None,
        **_: Any,
    ) -> Any:
        self._record("selectbox", label)
        if key is not None and key in self.selections:
            return self.selections[key]
        return options[0]

    def radio(
        self,
        label: str,
        options: Sequence[Any],
        *,
        key: str | None = None,
        **_: Any,
    ) -> Any:
        self._record("radio", label)
        if key is not None and key in self.selections:
            return self.selections[key]
        return options[0]

    def select_slider(
        self,
        label: str,
        *,
        options: Sequence[Any],
        value: Any,
        key: str | None = None,
        **_: Any,
    ) -> Any:
        self._record("select_slider", label)
        if key is not None and key in self.selections:
            return self.selections[key]
        return value


def _messages(fake: _FakeStreamlit, kind: str) -> list[str]:
    return [value for call_kind, value in fake.calls if call_kind == kind]


def _scientific_provenance(*, seed: int = 5) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="wu4-test",
        scenario_id="wu4-test",
        treatment_id="wu4-treatment",
        treatment_specification_json="{}",
        seed=seed,
        horizon_step_index=2,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
    )


def _workbench_provenance(
    *,
    revision_id: str = "wu4-revision",
    evidence_ids: tuple[str, ...] = ("population",),
) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id="wu4-run",
        study_revision_id=revision_id,
        manifest_digest="wu4-manifest",
        evidence_ids=evidence_ids,
        evidence_references=("wu4:evidence",),
        result_references=("wu4:result",),
    )


def _available(analysis_id: str) -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="WU4 synthetic authoritative evidence",
        required_evidence_ids=(),
    )


def _unavailable(analysis_id: str, evidence_id: str) -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="WU4 synthetic authoritative evidence",
        required_evidence_ids=(evidence_id,),
        missing_evidence_ids=(evidence_id,),
    )


def _patch_result_view(
    monkeypatch: pytest.MonkeyPatch,
    fake: _FakeStreamlit,
    view: object,
) -> None:
    monkeypatch.setattr(results_page, "st", fake)
    monkeypatch.setattr(results_page, "is_authoritative_run_result", lambda _: True)
    monkeypatch.setattr(results_page, "inspect_current_results", lambda *_: view)
    monkeypatch.setattr(results_page, "artifact_title", lambda _: "WU4 test artifact")
    monkeypatch.setattr(results_page, "evidence_options", lambda _: ())


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


def test_empty_revision_and_experiment_without_session_result_are_honest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    monkeypatch.setattr(results_page, "st", fake)
    revision = create_study_revision(
        revision_id="wu4-never-run",
        intent=ControlledLocomotionIntent(seed=3),
    )

    results_page.render_results_page(revision, None)
    results_page.render_results_page(new_max_speed_sweep(), None)

    info = " ".join(_messages(fake, "info")).lower()
    assert "no completed run payload" in info
    assert "does not serialize durable result payloads" in info


def test_e3_and_e4_results_require_the_exact_immutable_definition() -> None:
    e3 = new_max_speed_sweep()
    e3_result = MaxSpeedSweepResult(
        definition=e3,
        treatments=(),
        replicate_outcomes=(),
        treatment_summaries=(),
    )
    changed_e3 = attrs.evolve(e3, levels=(1, 3))

    e3_view = inspect_current_results(e3, e3_result)
    assert isinstance(e3_view, MaxSpeedSweepResultsView)
    assert e3_view.definition is e3
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

    e4_view = inspect_current_results(e4, e4_result)
    assert isinstance(e4_view, EnvironmentSelectionResultsView)
    assert e4_view.definition is e4
    with pytest.raises(ValueError, match="different immutable Experiment"):
        inspect_current_results(changed_e4, e4_result)


def test_reference_and_b3_navigation_preserve_exact_revision_association() -> None:
    reference = new_reference_ecology(revision_id="wu4-reference")
    reference_provenance = WorkbenchRunProvenance(
        run_id="wu4-reference-run",
        study_revision_id=reference.revision_id,
        manifest_digest=reference.manifest.digest,
        evidence_ids=reference.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )
    reference_result = ReferenceRunResult(
        provenance=reference_provenance,
        scientific_provenance=_scientific_provenance(seed=11),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )
    reference_view = inspect_current_results(reference, reference_result)

    assert isinstance(reference_view, ReferenceStudyResultsView)
    assert reference_view.provenance is reference_provenance
    with pytest.raises(ValueError, match="different Study revision"):
        inspect_current_results(
            new_reference_ecology(revision_id="wu4-reference-other"),
            reference_result,
        )

    b3 = new_b3_flagship(revision_id="wu4-b3")
    b3_provenance = WorkbenchRunProvenance(
        run_id="wu4-b3-run",
        study_revision_id=b3.revision_id,
        manifest_digest=b3.manifest.digest,
        evidence_ids=B3_REQUIRED_EVIDENCE_IDS,
        evidence_references=(),
        result_references=(),
    )
    confirmation = (cast(B3MatchedRunArtifacts, object()),)
    sensitivity = (cast(B3SingleRunArtifacts, object()),)
    counterbalanced = (cast(B3MatchedRunArtifacts, object()),)
    b3_result = B3CuratedRunResult(
        provenance=b3_provenance,
        scenario_origin=b3.scenario_origin,
        scenario_identity=b3.scenario_identity,
        confirmation=confirmation,
        radius_sensitivity=sensitivity,
        counterbalanced=counterbalanced,
    )
    b3_view = inspect_current_results(b3, b3_result)

    assert isinstance(b3_view, B3ResultsView)
    assert b3_view.confirmation is confirmation
    assert b3_view.radius_sensitivity is sensitivity
    assert b3_view.counterbalanced is counterbalanced
    assert b3_view.cinematic_handoff_availability.available
    with pytest.raises(ValueError, match="different Study revision"):
        inspect_current_results(new_b3_flagship(revision_id="wu4-b3-other"), b3_result)


def test_reference_results_render_recorded_streams_and_missing_spatial_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    provenance = _workbench_provenance(
        evidence_ids=("population", "events", "pedigree", "genetics")
    )
    population = SimpleNamespace(
        step_index=1,
        population_size=4,
        carcass_count=1,
        total_resources=8.0,
        age=SimpleNamespace(mean=2.0),
        energy=SimpleNamespace(mean=70.0),
        body_mass=SimpleNamespace(mean=1.5),
    )
    event = SimpleNamespace(
        event_step_index=0,
        completed_step_index=1,
        stage_index=2,
        process_name="movement",
        event_name="MoveEvent",
        effects=(object(),),
    )
    pedigree = SimpleNamespace(
        organism_id=7,
        is_founder=False,
        parent_ids=(1, 2),
        entry_step=1,
        birth_step=1,
        death_step=None,
        death_cause=None,
        offspring_ids=(9,),
        realized_reproductive_success=1,
        lifetime_reproductive_success=None,
    )
    allele = SimpleNamespace(value=3, count=4, frequency=0.5)
    genotype = SimpleNamespace(allele_values=(1, 3), count=2, frequency=0.5)
    locus = SimpleNamespace(
        locus_name="max_speed",
        alleles=(allele,),
        genotypes=(genotype,),
    )
    genetics = SimpleNamespace(step_index=1, population_size=4, loci=(locus,))
    spatial = SimpleNamespace(
        step_index=1,
        world_width=10,
        world_height=8,
        organisms=(
            SimpleNamespace(
                organism_id=7,
                x=2.0,
                y=3.0,
                age=2,
                energy=70.0,
                body_mass=1.5,
                mating_type="A",
            ),
        ),
        resources=(SimpleNamespace(x=4.0, y=5.0, amount=2.0),),
        carcasses=(
            SimpleNamespace(carcass_id=3, x=6.0, y=7.0, resource_units=1.0),
        ),
    )
    view = ReferenceStudyResultsView(
        provenance=provenance,
        scientific_provenance=_scientific_provenance(),
        population_observations=cast(Any, (population,)),
        applied_events=cast(Any, (event,)),
        pedigree_records=cast(Any, (pedigree,)),
        genetic_observations=cast(Any, (genetics,)),
        spatial_observations=cast(Any, (spatial,)),
        population_availability=_available("population"),
        event_availability=_available("events"),
        pedigree_availability=_available("pedigree"),
        genetic_availability=_available("genetics"),
        spatial_availability=_available("spatial"),
    )
    _patch_result_view(monkeypatch, fake, view)

    results_page.render_results_page(cast(Any, object()), object())

    assert _messages(fake, "selectbox") == ["Process filter"]
    assert _messages(fake, "select_slider") == ["Inspect committed spatial frame"]
    assert len(_messages(fake, "dataframe")) >= 8
    assert _messages(fake, "line_chart")

    missing_view = attrs.evolve(
        view,
        spatial_observations=(),
        spatial_availability=_unavailable("spatial", "reference.spatial"),
    )
    _patch_result_view(monkeypatch, fake, missing_view)
    results_page.render_results_page(cast(Any, object()), object())

    assert any("reference.spatial" in value for value in _messages(fake, "write"))
    assert any("new run" in value.lower() for value in _messages(fake, "info"))


def test_e3_results_render_factor_replicate_summary_and_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    definition = new_max_speed_sweep()
    factor_level = definition.levels[0]
    seed = definition.seeds[0]
    treatment = build_e3_treatment(
        max_speed=factor_level,
        environment=definition.base_intent.resource_geography,
    )
    scientific = _scientific_provenance(seed=seed)
    locomotion = SimpleNamespace(
        applied_movement_count=4,
        total_attempted_distance=8.0,
        total_realized_distance=7.0,
        mean_realized_distance_per_applied_movement=1.75,
        total_locomotion_energy_expenditure=3.0,
        mean_locomotion_energy_expenditure_per_applied_movement=0.75,
    )
    outcome = SimpleNamespace(
        final_population_size=6,
        final_total_population_energy=120.0,
        cumulative_birth_count=4,
        total_resource_consumed=9.0,
        boundary_clipping_event_count=1,
        extinction=SimpleNamespace(observed_step_index=None, right_censored=True),
        energy_trajectory=(
            SimpleNamespace(
                step_index=1,
                population_size=6,
                total_population_energy=120.0,
            ),
        ),
        locomotion=locomotion,
        provenance=scientific,
    )
    replicate = SimpleNamespace(
        factor_level=factor_level,
        seed=seed,
        treatment_id=treatment.treatment_id,
        manifest_digest="wu4-e3-manifest",
        outcome=outcome,
    )
    summary = E3TreatmentSummary(
        treatment=treatment,
        replicate_count=1,
        seeds=(seed,),
        birth_counts=(4,),
        mean_cumulative_birth_count=4.0,
        mean_final_population_size=6.0,
        mean_total_resource_consumed=9.0,
        mean_total_realized_distance=7.0,
        mean_total_locomotion_energy_expenditure=3.0,
        extinction_count=0,
    )
    view = MaxSpeedSweepResultsView(
        definition=definition,
        replicates=cast(Any, (replicate,)),
        treatment_summaries=(summary,),
    )
    _patch_result_view(monkeypatch, fake, view)

    results_page.render_results_page(definition, object())

    assert _messages(fake, "selectbox").count("Maximum-speed factor level") == 2
    assert _messages(fake, "selectbox").count("Replicate seed") == 2
    assert len(_messages(fake, "line_chart")) == 2
    assert len(_messages(fake, "dataframe")) >= 7
    assert any("independent replicates" in value for value in _messages(fake, "caption"))


def test_e4_results_keep_factor_arm_counterbalance_and_standing_composition_distinct(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    definition = new_environment_selection_comparison()
    seed = definition.seeds[0]
    scientific = _scientific_provenance(seed=seed)
    trajectory = SimpleNamespace(
        step_index=1,
        population_size=9,
        counts=(3, 4, 2),
        frequencies=(1 / 3, 4 / 9, 2 / 9),
    )
    mechanisms = tuple(
        SimpleNamespace(
            max_speed=speed,
            applied_movement_count=3,
            total_realized_distance=float(speed),
            total_locomotion_energy_expenditure=float(speed) / 2,
            total_resource_consumed=float(speed) + 1,
            cumulative_birth_count=speed,
        )
        for speed in definition.focal_speeds
    )
    outcome = SimpleNamespace(
        focal_trajectory=(trajectory,),
        mechanisms=mechanisms,
        provenance=scientific,
    )
    replicate = SimpleNamespace(
        role="control",
        factor_level=definition.control_environment,
        seed=seed,
        treatment_id="wu4-e4-control",
        founder_speed_order=(1, 3, 9),
        standing_focal_composition=definition.focal_speeds,
        outcome=outcome,
    )
    control_summary = E4EnvironmentSummary(
        environment=definition.control_environment,
        replicate_count=1,
        seeds=(seed,),
        founder_speed_orders=((1, 3, 9),),
        mean_final_frequencies=(0.2, 0.5, 0.3),
        mean_frequency_changes=(-0.1, 0.2, -0.1),
        defined_endpoint_count=1,
        extinction_count=0,
        mean_births_by_speed=(1.0, 2.0, 1.0),
        mean_resources_by_speed=(2.0, 3.0, 2.0),
        mean_realized_distance_by_speed=(3.0, 4.0, 5.0),
        mean_locomotion_energy_by_speed=(1.0, 2.0, 3.0),
    )
    treatment_summary = attrs.evolve(
        control_summary,
        environment=definition.treatment_environment,
    )
    view = EnvironmentSelectionResultsView(
        definition=definition,
        replicates=cast(Any, (replicate,)),
        environment_summaries=(control_summary, treatment_summary),
    )
    _patch_result_view(monkeypatch, fake, view)

    results_page.render_results_page(definition, object())

    assert _messages(fake, "radio").count("Arm") == 2
    assert _messages(fake, "selectbox").count("Replicate seed") == 2
    assert len(_messages(fake, "line_chart")) == 1
    assert len(_messages(fake, "bar_chart")) == 1
    captions = " ".join(_messages(fake, "caption")).lower()
    assert "counterbalance metadata, not another experimental factor" in captions
    assert "standing composition" in captions


def test_b3_results_keep_scientific_roles_and_scenario_identity_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeStreamlit()
    provenance = _workbench_provenance(evidence_ids=B3_REQUIRED_EVIDENCE_IDS)

    def run_summary(
        *,
        environment: str,
        high_speed_frequency: float,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            seed=5,
            environment=environment,
            founder_assignment="canonical",
            primary_high_speed_frequency=high_speed_frequency,
            extinction_step=None,
            population_trajectory=(
                SimpleNamespace(
                    step_index=1,
                    population_size=8,
                    total_resources=12.0,
                    mean_energy=65.0,
                    mean_max_speed_capacity=2.5,
                ),
            ),
            genetic_trajectory=(
                SimpleNamespace(
                    step_index=1,
                    population_size=8,
                    high_speed_allele_frequency=high_speed_frequency,
                ),
            ),
            founder_reproductive_success=SimpleNamespace(
                low_speed_count=2,
                low_speed_mean=1.0,
                high_speed_count=2,
                high_speed_mean=2.0,
            ),
        )

    control = run_summary(environment="uniform_resources", high_speed_frequency=0.4)
    treatment = run_summary(environment="compact_patches", high_speed_frequency=0.7)
    pair_summary = SimpleNamespace(
        seed=5,
        founder_assignment="canonical",
        control=control,
        treatment=treatment,
        primary_effect=0.3,
    )
    pair = SimpleNamespace(summary=pair_summary)
    sensitivity = SimpleNamespace(summary=treatment)
    view = B3ResultsView(
        provenance=provenance,
        scenario_origin="b3.flagship",
        scenario_identity="b3.flagship.radius-1.v1",
        confirmation=cast(Any, (pair,)),
        radius_sensitivity=cast(Any, (sensitivity,)),
        counterbalanced=cast(Any, (pair,)),
        cinematic_handoff_availability=_available("b3-cinematic"),
    )
    _patch_result_view(monkeypatch, fake, view)

    results_page.render_results_page(cast(Any, object()), object())
    fake.selections["wu4_b3_role"] = "Radius sensitivity"
    results_page.render_results_page(cast(Any, object()), object())
    fake.selections["wu4_b3_role"] = "Founder-label counterbalance"
    results_page.render_results_page(cast(Any, object()), object())

    radios = _messages(fake, "radio")
    assert radios.count("Scientific run role") == 3
    assert "Arm" in radios
    assert _messages(fake, "success").count(
        "Canonical B3 cinematic scientific handoff is available."
    ) == 3
    captions = " ".join(_messages(fake, "caption")).lower()
    assert "sensitivity remains secondary" in captions
    assert "counterbalance evidence" in captions

    noncanonical = attrs.evolve(
        view,
        scenario_identity=None,
        cinematic_handoff_availability=AnalysisAvailability(
            analysis_id="b3-cinematic",
            source_contract="canonical B3 scenario identity",
            required_evidence_ids=(),
            unavailable_reason="Validated canonical scenario identity is absent.",
        ),
    )
    fake.selections["wu4_b3_role"] = "Primary confirmation"
    _patch_result_view(monkeypatch, fake, noncanonical)
    results_page.render_results_page(cast(Any, object()), object())

    writes = " ".join(_messages(fake, "write"))
    assert "No validated canonical identity" in writes
    assert any("unavailable" in value.lower() for value in _messages(fake, "warning"))


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
