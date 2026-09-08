"""Focused WU5 tests for Presentation routing and renderer integration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import evo_engine.ui.presentation_page as presentation_page
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.ui.study_shell import new_b3_flagship, new_reference_ecology
from evo_engine.ui.workbench import WorkbenchWorldPresentation
from evo_engine.ui.world_explorer import WorldViewOptions
from evo_engine.ui.world_presentation import OrganismPrimitive, WorldPresentationFrame
from evo_engine.workbench import B3CuratedRunResult, ReferenceRunResult
from evo_engine.workbench.results import (
    AnalysisAvailability,
    B3ResultsView,
    ReferenceStudyResultsView,
)
from evo_engine.workbench.study import WorkbenchRunProvenance
from evo_engine.experiments.science import ScientificRunProvenance


class _Context:
    def __enter__(self) -> _Context:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class _FakeStreamlit(_Context):
    def __init__(self) -> None:
        self.session_state: dict[str, Any] = {}
        self.calls: list[tuple[str, str]] = []
        self.buttons: dict[str, bool] = {}
        self.selections: dict[str, Any] = {}
        self.reruns = 0

    def _record(self, kind: str, value: object = "") -> None:
        self.calls.append((kind, str(value)))

    def __getattr__(self, name: str) -> Any:
        if name in {
            "header",
            "caption",
            "subheader",
            "markdown",
            "write",
            "info",
            "warning",
            "error",
            "success",
            "title",
            "divider",
            "video",
            "image",
            "download_button",
            "plotly_chart",
        }:
            def recorder(value: object = "", *_: Any, **__: Any) -> None:
                self._record(name, value)

            return recorder
        raise AttributeError(name)

    def button(self, label: str, *, key: str | None = None, **_: Any) -> bool:
        self._record("button", label)
        return self.buttons.get(key or label, False)

    def columns(self, spec: int | Sequence[Any]) -> tuple[_FakeStreamlit, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(self for _ in range(count))

    def selectbox(
        self,
        label: str,
        options: Sequence[Any],
        *,
        key: str | None = None,
        index: int = 0,
        **_: Any,
    ) -> Any:
        self._record("selectbox", label)
        if key is not None and key in self.selections:
            return self.selections[key]
        return options[index]

    def spinner(self, value: str) -> _Context:
        self._record("spinner", value)
        return self

    def fragment(self, **_: Any) -> Any:
        def decorator(func: Any) -> Any:
            return func

        return decorator

    def rerun(self, **_: Any) -> None:
        self.reruns += 1


def _patch_streamlit(monkeypatch: pytest.MonkeyPatch) -> _FakeStreamlit:
    fake = _FakeStreamlit()
    monkeypatch.setattr(presentation_page, "st", fake)
    return fake


def _messages(fake: _FakeStreamlit, kind: str) -> list[str]:
    return [value for call_kind, value in fake.calls if call_kind == kind]


def _scientific_provenance(seed: int = 5) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="wu5-test",
        scenario_id="wu5-test",
        treatment_id="wu5-treatment",
        treatment_specification_json="{}",
        seed=seed,
        horizon_step_index=2,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
    )


def _provenance(
    revision_id: str,
    manifest_digest: str,
    evidence_ids: tuple[str, ...],
    *,
    run_id: str = "wu5-run",
) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision_id,
        manifest_digest=manifest_digest,
        evidence_ids=evidence_ids,
        evidence_references=("wu5:evidence",),
        result_references=("wu5:result",),
    )


def _available(analysis_id: str = "wu5.available") -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="WU5 synthetic evidence",
        required_evidence_ids=(),
    )


def _unavailable(analysis_id: str = "wu5.unavailable") -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="WU5 synthetic evidence",
        required_evidence_ids=("spatial",),
        missing_evidence_ids=("spatial",),
    )


def _frame(
    *,
    step: int = 2,
    selected_id: int | None = 7,
    encoding: ContinuousTraitEncoding | None = None,
) -> WorldPresentationFrame:
    organism = OrganismPrimitive(
        organism_id=7,
        x=1.0,
        y=2.0,
        age=3,
        energy=40,
        body_mass=5,
        mating_type="A",
        marker_size=10,
        selected=selected_id == 7,
        focal_trait_value=3 if encoding is not None else None,
        focal_trait_normalized=0.67 if encoding is not None else None,
    )
    return WorldPresentationFrame(
        committed_step_index=step,
        world_width=10,
        world_height=10,
        organisms=(organism,),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=selected_id,
        focal_encoding=encoding,
    )


def _world_presentation(
    provenance: WorkbenchRunProvenance,
    *,
    seed: int = 11,
    step: int = 2,
    arm: str | None = None,
    environment: str | None = None,
    encoding: ContinuousTraitEncoding | None = None,
) -> WorkbenchWorldPresentation:
    return WorkbenchWorldPresentation(
        provenance=provenance,
        seed=seed,
        arm=arm,
        environment=environment,
        frame=_frame(step=step, encoding=encoding),
    )


def test_renderer_discovery_and_public_render_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(presentation_page, "find_spec", lambda _: object())
    assert presentation_page.b3_renderer_available() is True
    monkeypatch.setattr(presentation_page, "find_spec", lambda _: None)
    assert presentation_page.b3_renderer_available() is False

    def broken_find(_: str) -> object:
        raise ImportError("broken")

    monkeypatch.setattr(presentation_page, "find_spec", broken_find)
    assert presentation_page.b3_renderer_available() is False

    def fake_render(plan: object, destination: Path, *, quality: str) -> Path:
        assert plan is marker
        assert quality == "medium"
        destination.write_bytes(b"cinematic")
        return destination

    marker = object()
    monkeypatch.setattr(presentation_page, "render_b3_flagship_cinematic", fake_render)
    payload, mime, filename = presentation_page.render_b3_story_artifact(
        cast(Any, marker), quality="medium", output_format="mp4"
    )
    assert (payload, mime, filename) == (
        b"cinematic",
        "video/mp4",
        "b3_scientific_story.mp4",
    )
    payload, mime, filename = presentation_page.render_b3_story_artifact(
        cast(Any, marker), quality="medium", output_format="gif"
    )
    assert payload == b"cinematic"
    assert mime == "image/gif"
    assert filename.endswith(".gif")
    with pytest.raises(ValueError, match="output_format"):
        presentation_page.render_b3_story_artifact(
            cast(Any, marker), quality="medium", output_format=cast(Any, "avi")
        )


def test_owner_token_requires_exact_scientific_owner() -> None:
    provenance = SimpleNamespace(
        study_revision_id="rev",
        manifest_digest="digest",
        run_id="run",
    )
    assert presentation_page._owner_token(provenance) == "rev:digest:run"
    with pytest.raises(ValueError, match="exact scientific ownership"):
        presentation_page._owner_token(SimpleNamespace(run_id="run"))


def test_no_current_result_and_unavailable_diagnostics_are_truthful(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    artifact = object()
    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 1)
    presentation_page._render_no_current_result(cast(Any, artifact))
    assert any("historical run" in value.lower() for value in _messages(fake, "info"))
    assert any("not spatial replay data" in value.lower() for value in _messages(fake, "caption"))

    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 0)
    presentation_page._render_no_current_result(cast(Any, artifact))
    assert any("run this study first" in value.lower() for value in _messages(fake, "info"))

    presentation_page._render_unavailable_analysis(_unavailable(), world=True)
    assert any("INTERACTIVE WORLD UNAVAILABLE" in value for value in _messages(fake, "error"))
    assert any("Required evidence" in value for value in _messages(fake, "write"))
    presentation_page._render_unavailable_analysis(_unavailable(), world=False)
    assert any("B3 SCIENTIFIC STORY UNAVAILABLE" in value for value in _messages(fake, "error"))
    presentation_page._render_unavailable_analysis(_available(), world=True)


def test_focus_and_back_actions_only_change_view_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    calls: list[object] = []
    monkeypatch.setattr(
        presentation_page,
        "set_presentation_focus_mode",
        lambda enabled: calls.append(("focus", enabled)),
    )
    monkeypatch.setattr(
        presentation_page,
        "show_presentation_landing",
        lambda: calls.append("landing"),
    )

    fake.buttons["wu5_presentation_back_to_study"] = True
    presentation_page._render_focus_header()
    assert ("focus", False) in calls
    assert fake.reruns == 1

    fake.buttons["wu5_presentation_back_to_landing"] = True
    presentation_page._render_world_back_action(focus_mode=False)
    assert "landing" in calls
    presentation_page._render_world_back_action(focus_mode=True)


def test_organism_inspector_reports_committed_values_and_missing_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    presentation_page._render_organism_inspector(_frame(selected_id=None))
    assert any("choose an organism" in value.lower() for value in _messages(fake, "caption"))

    missing = WorldPresentationFrame(
        committed_step_index=4,
        world_width=10,
        world_height=10,
        organisms=(),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=99,
    )
    presentation_page._render_organism_inspector(missing)
    assert any("not active" in value.lower() for value in _messages(fake, "info"))

    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=4,
    )
    presentation_page._render_organism_inspector(_frame(encoding=encoding))
    written = " ".join(_messages(fake, "write"))
    assert "**ID:** 7" in written
    assert "**Position:** (1, 2)" in written
    assert "**Energy:** 40" in written
    assert "**Maximum speed:** 3" in written


def test_b3_pair_rejects_mismatches_and_uses_one_fixed_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    monkeypatch.setattr(presentation_page, "world_presentation_figure", lambda *_a, **_k: object())
    provenance = _provenance("rev", "digest", ())
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=4,
    )
    options = WorldViewOptions(
        show_resources=True,
        show_carcasses=True,
        show_trails=True,
        trail_length=5,
        show_labels=False,
    )
    control = _world_presentation(
        provenance,
        seed=11,
        arm="control",
        environment="uniform",
        encoding=encoding,
    )
    treatment = _world_presentation(
        provenance,
        seed=13,
        arm="treatment",
        environment="compact",
        encoding=encoding,
    )
    presentation_page._render_b3_pair(control, treatment, options, focus_mode=False)
    assert any("different seeds" in value for value in _messages(fake, "error"))

    treatment = _world_presentation(
        provenance,
        seed=11,
        step=3,
        arm="treatment",
        environment="compact",
        encoding=encoding,
    )
    presentation_page._render_b3_pair(control, treatment, options, focus_mode=False)
    assert any("different committed steps" in value for value in _messages(fake, "error"))

    other_encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=0,
        upper_bound=5,
    )
    treatment = _world_presentation(
        provenance,
        seed=11,
        arm="treatment",
        environment="compact",
        encoding=other_encoding,
    )
    presentation_page._render_b3_pair(control, treatment, options, focus_mode=False)
    assert any("inconsistent scientific trait scales" in value for value in _messages(fake, "error"))

    treatment = _world_presentation(
        provenance,
        seed=11,
        arm="treatment",
        environment="compact",
        encoding=encoding,
    )
    presentation_page._render_b3_pair(control, treatment, options, focus_mode=True)
    assert len(_messages(fake, "plotly_chart")) == 2
    assert any("same fixed scale" in value.lower() for value in _messages(fake, "caption"))
    assert any("focus mode enlarges" in value.lower() for value in _messages(fake, "caption"))


def test_single_world_keeps_exact_seed_step_and_inspector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    monkeypatch.setattr(presentation_page, "world_presentation_figure", lambda *_a, **_k: object())
    provenance = _provenance("rev", "digest", ())
    presentation = _world_presentation(provenance, seed=17, step=4)
    options = WorldViewOptions(
        show_resources=True,
        show_carcasses=True,
        show_trails=False,
        trail_length=3,
        show_labels=True,
    )
    presentation_page._render_single_world(presentation, options, focus_mode=False)
    written = " ".join(_messages(fake, "write"))
    assert "**Seed:** 17" in written
    assert "**Committed step:** 4" in written
    assert len(_messages(fake, "plotly_chart")) == 1


def test_cached_story_previews_video_or_image_without_changing_science(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    presentation_page._render_cached_story()
    assert not _messages(fake, "download_button")

    fake.session_state.update(
        {
            "wu5_presentation_cinematic_bytes": b"video",
            "wu5_presentation_cinematic_format": "video/mp4",
            "wu5_presentation_cinematic_rendered_quality": "high",
            "wu5_presentation_cinematic_filename": "story.mp4",
        }
    )
    presentation_page._render_cached_story()
    assert _messages(fake, "video")
    assert _messages(fake, "download_button")

    fake.calls.clear()
    fake.session_state["wu5_presentation_cinematic_format"] = "image/gif"
    fake.session_state["wu5_presentation_cinematic_filename"] = "story.gif"
    presentation_page._render_cached_story()
    assert _messages(fake, "image")


def test_b3_story_distinguishes_scientific_and_renderer_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision = new_b3_flagship(revision_id="wu5-b3-story")
    provenance = _provenance(
        revision.revision_id,
        revision.manifest.digest,
        revision.evidence_plan.requested,
    )
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    unavailable_view = B3ResultsView(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
        cinematic_handoff_availability=_unavailable("b3.story"),
    )
    presentation_page._render_b3_story(revision, result, unavailable_view)
    assert any("B3 SCIENTIFIC STORY UNAVAILABLE" in value for value in _messages(fake, "error"))

    available_view = B3ResultsView(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
        cinematic_handoff_availability=_available("b3.story"),
    )
    monkeypatch.setattr(presentation_page, "prepare_b3_workbench_cinematic", lambda *_: object())
    monkeypatch.setattr(presentation_page, "b3_renderer_available", lambda: False)
    presentation_page._render_b3_story(revision, result, available_view)
    assert any("scientific cinematic is available" in value.lower() for value in _messages(fake, "info"))

    def bad_prepare(*_: object) -> object:
        raise ValueError("invalid handoff")

    fake.calls.clear()
    monkeypatch.setattr(presentation_page, "prepare_b3_workbench_cinematic", bad_prepare)
    presentation_page._render_b3_story(revision, result, available_view)
    assert any("handoff could not be prepared" in value.lower() for value in _messages(fake, "error"))


def test_b3_story_renderer_controls_are_renderer_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision = new_b3_flagship(revision_id="wu5-b3-render")
    provenance = _provenance(
        revision.revision_id,
        revision.manifest.digest,
        revision.evidence_plan.requested,
    )
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    view = B3ResultsView(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
        cinematic_handoff_availability=_available("b3.story"),
    )
    marker = object()
    monkeypatch.setattr(presentation_page, "prepare_b3_workbench_cinematic", lambda *_: marker)
    monkeypatch.setattr(presentation_page, "b3_renderer_available", lambda: True)
    fake.selections["wu5_presentation_cinematic_quality"] = "high"
    fake.selections["wu5_presentation_cinematic_output"] = "gif"
    fake.buttons["Render B3 Scientific Story"] = True
    monkeypatch.setattr(
        presentation_page,
        "render_b3_story_artifact",
        lambda plan, **_: (b"story", "image/gif", "b3_scientific_story.gif"),
    )
    digest_before = revision.manifest.digest
    evidence_before = revision.evidence_plan
    identity_before = revision.scenario_identity

    presentation_page._render_b3_story(revision, result, view)

    assert fake.session_state["wu5_presentation_cinematic_bytes"] == b"story"
    assert fake.session_state["wu5_presentation_cinematic_rendered_quality"] == "high"
    assert revision.manifest.digest == digest_before
    assert revision.evidence_plan == evidence_before
    assert revision.scenario_identity == identity_before


def test_presentation_page_rejects_stale_result_and_routes_supported_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    reference = new_reference_ecology(revision_id="wu5-reference-route")
    reference_provenance = _provenance(
        reference.revision_id,
        reference.manifest.digest,
        reference.evidence_plan.requested,
    )
    reference_result = ReferenceRunResult(
        provenance=reference_provenance,
        scientific_provenance=_scientific_provenance(11),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )
    reference_view = ReferenceStudyResultsView(
        provenance=reference_provenance,
        scientific_provenance=reference_result.scientific_provenance,
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
        population_availability=_available(),
        event_availability=_available(),
        pedigree_availability=_available(),
        genetic_availability=_available(),
        spatial_availability=_unavailable(),
    )
    monkeypatch.setattr(presentation_page, "is_authoritative_run_result", lambda _: True)

    def stale(*_: object) -> object:
        raise ValueError("different scientific owner")

    monkeypatch.setattr(presentation_page, "inspect_current_results", stale)
    presentation_page.render_presentation_page(reference, reference_result)
    assert any("PRESENTATION UNAVAILABLE" in value for value in _messages(fake, "error"))

    routed: list[str] = []
    monkeypatch.setattr(presentation_page, "inspect_current_results", lambda *_: reference_view)
    monkeypatch.setattr(presentation_page, "ensure_presentation_owner", lambda _: routed.append("owner"))
    monkeypatch.setattr(
        presentation_page,
        "_render_reference_presentation",
        lambda *_a, **_k: routed.append("reference"),
    )
    presentation_page.render_presentation_page(reference, reference_result)
    assert routed == ["owner", "reference"]

    b3 = new_b3_flagship(revision_id="wu5-b3-route")
    b3_provenance = _provenance(
        b3.revision_id,
        b3.manifest.digest,
        b3.evidence_plan.requested,
        run_id="wu5-b3-run",
    )
    b3_result = B3CuratedRunResult(
        provenance=b3_provenance,
        scenario_origin=b3.scenario_origin,
        scenario_identity=b3.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )
    b3_view = B3ResultsView(
        provenance=b3_provenance,
        scenario_origin=b3.scenario_origin,
        scenario_identity=b3.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
        cinematic_handoff_availability=_available("b3.story"),
    )
    routed.clear()
    monkeypatch.setattr(presentation_page, "inspect_current_results", lambda *_: b3_view)
    monkeypatch.setattr(
        presentation_page,
        "_render_b3_presentation",
        lambda *_a, **_k: routed.append("b3"),
    )
    presentation_page.render_presentation_page(b3, b3_result, focus_mode=True)
    assert routed == ["owner", "b3"]


def test_presentation_page_without_session_result_never_reruns_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    reference = new_reference_ecology(revision_id="wu5-no-result")
    monkeypatch.setattr(presentation_page, "is_authoritative_run_result", lambda _: False)
    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 1)

    presentation_page.render_presentation_page(reference, None)

    assert any("historical run" in value.lower() for value in _messages(fake, "info"))
    assert not fake.reruns
