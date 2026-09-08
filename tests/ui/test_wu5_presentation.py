"""Focused WU5 tests for Presentation routing and renderer integration."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import evo_engine.ui.presentation_page as presentation_page
from evo_engine.experiments.science import ScientificRunProvenance
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


def _reference_fixture() -> tuple[
    Any,
    ReferenceRunResult,
    ReferenceStudyResultsView,
]:
    revision = new_reference_ecology(revision_id="wu5-reference")
    provenance = _provenance(
        revision.revision_id,
        revision.manifest.digest,
        revision.evidence_plan.requested,
    )
    result = ReferenceRunResult(
        provenance=provenance,
        scientific_provenance=_scientific_provenance(11),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )
    view = ReferenceStudyResultsView(
        provenance=provenance,
        scientific_provenance=result.scientific_provenance,
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
    return revision, result, view


def _b3_fixture() -> tuple[Any, B3CuratedRunResult, B3ResultsView]:
    revision = new_b3_flagship(revision_id="wu5-b3")
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
    return revision, result, view


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

    marker = object()

    def fake_render(plan: object, destination: Path, *, quality: str) -> Path:
        assert plan is marker
        assert quality == "medium"
        destination.write_bytes(b"cinematic")
        return destination

    monkeypatch.setattr(
        presentation_page,
        "render_b3_flagship_cinematic",
        fake_render,
    )
    payload, mime, filename = presentation_page.render_b3_story_artifact(
        cast(Any, marker),
        quality="medium",
        output_format="mp4",
    )
    assert (payload, mime, filename) == (
        b"cinematic",
        "video/mp4",
        "b3_scientific_story.mp4",
    )
    payload, mime, filename = presentation_page.render_b3_story_artifact(
        cast(Any, marker),
        quality="medium",
        output_format="gif",
    )
    assert payload == b"cinematic"
    assert mime == "image/gif"
    assert filename.endswith(".gif")
    with pytest.raises(ValueError, match="output_format"):
        presentation_page.render_b3_story_artifact(
            cast(Any, marker),
            quality="medium",
            output_format=cast(Any, "avi"),
        )


def test_owner_token_and_no_current_result_are_exact_and_truthful(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    provenance = SimpleNamespace(
        study_revision_id="rev",
        manifest_digest="digest",
        run_id="run",
    )
    assert presentation_page._owner_token(provenance) == "rev:digest:run"
    with pytest.raises(ValueError, match="exact scientific ownership"):
        presentation_page._owner_token(SimpleNamespace(run_id="run"))

    artifact = object()
    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 1)
    presentation_page._render_no_current_result(cast(Any, artifact))
    assert any(
        "historical run" in value.lower() for value in _messages(fake, "info")
    )
    assert any(
        "not spatial replay data" in value.lower()
        for value in _messages(fake, "caption")
    )

    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 0)
    presentation_page._render_no_current_result(cast(Any, artifact))
    assert any(
        "run this study first" in value.lower() for value in _messages(fake, "info")
    )


def test_unavailable_diagnostics_and_navigation_actions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    presentation_page._render_unavailable_analysis(_unavailable(), world=True)
    assert any(
        "INTERACTIVE WORLD UNAVAILABLE" in value
        for value in _messages(fake, "error")
    )
    assert any("Required evidence" in value for value in _messages(fake, "write"))
    presentation_page._render_unavailable_analysis(_unavailable(), world=False)
    assert any(
        "B3 SCIENTIFIC STORY UNAVAILABLE" in value
        for value in _messages(fake, "error")
    )
    presentation_page._render_unavailable_analysis(_available(), world=True)

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
    fake.buttons["wu5_presentation_back_to_landing"] = True
    presentation_page._render_world_back_action(focus_mode=False)
    assert "landing" in calls
    presentation_page._render_world_back_action(focus_mode=True)


def test_organism_inspector_and_world_renderers_use_committed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    presentation_page._render_organism_inspector(_frame(selected_id=None))
    assert any(
        "choose an organism" in value.lower()
        for value in _messages(fake, "caption")
    )

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
    assert "**Maximum speed:** 3" in written

    monkeypatch.setattr(
        presentation_page,
        "world_presentation_figure",
        lambda *_a, **_k: object(),
    )
    provenance = _provenance("rev", "digest", ())
    options = WorldViewOptions(
        show_resources=True,
        show_carcasses=True,
        show_trails=False,
        trail_length=3,
        show_labels=True,
    )
    presentation_page._render_single_world(
        _world_presentation(provenance, seed=17, step=4),
        options,
        focus_mode=False,
    )
    written = " ".join(_messages(fake, "write"))
    assert "**Seed:** 17" in written
    assert "**Committed step:** 4" in written


def test_b3_pair_rejects_mismatch_and_uses_one_fixed_encoding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    monkeypatch.setattr(
        presentation_page,
        "world_presentation_figure",
        lambda *_a, **_k: object(),
    )
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
    assert any(
        "different committed steps" in value for value in _messages(fake, "error")
    )

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
    assert any(
        "inconsistent scientific trait scales" in value
        for value in _messages(fake, "error")
    )

    treatment = _world_presentation(
        provenance,
        seed=11,
        arm="treatment",
        environment="compact",
        encoding=encoding,
    )
    presentation_page._render_b3_pair(control, treatment, options, focus_mode=True)
    assert len(_messages(fake, "plotly_chart")) == 2
    assert any(
        "same fixed scale" in value.lower() for value in _messages(fake, "caption")
    )
    assert any(
        "focus mode enlarges" in value.lower()
        for value in _messages(fake, "caption")
    )


def test_reference_landing_and_world_paths_use_existing_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, view = _reference_fixture()

    monkeypatch.setattr(presentation_page, "presentation_experience", lambda: "landing")
    presentation_page._render_reference_presentation(
        revision,
        result,
        view,
        focus_mode=False,
    )
    assert any(
        "INTERACTIVE WORLD UNAVAILABLE" in value for value in _messages(fake, "error")
    )

    available_view = cast(
        ReferenceStudyResultsView,
        SimpleNamespace(
            spatial_availability=_available(),
            spatial_observations=(SimpleNamespace(step_index=0, organisms=()),),
            provenance=view.provenance,
            scientific_provenance=view.scientific_provenance,
        ),
    )
    fake.buttons["Open World Explorer"] = True
    opened: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "open_world_explorer",
        lambda: opened.append("world"),
    )
    presentation_page._render_reference_presentation(
        revision,
        result,
        available_view,
        focus_mode=False,
    )
    assert opened == ["world"]

    fake.buttons.clear()
    monkeypatch.setattr(presentation_page, "presentation_experience", lambda: "world")
    routed: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "_render_reference_world",
        lambda *_a, **_k: routed.append("reference-world"),
    )
    presentation_page._render_reference_presentation(
        revision,
        result,
        available_view,
        focus_mode=False,
    )
    assert routed == ["reference-world"]


def test_reference_world_selects_exact_step_and_passes_view_only_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, view = _reference_fixture()
    spatial = (SimpleNamespace(step_index=0, organisms=()),)
    available_view = cast(
        ReferenceStudyResultsView,
        SimpleNamespace(
            spatial_availability=_available(),
            spatial_observations=spatial,
            provenance=view.provenance,
            scientific_provenance=view.scientific_provenance,
        ),
    )
    monkeypatch.setattr(
        presentation_page,
        "available_step_indices",
        lambda _: (0, 2),
    )
    monkeypatch.setattr(presentation_page, "initialize_world_state", lambda _: None)
    monkeypatch.setattr(presentation_page, "playback_interval", lambda: None)
    monkeypatch.setattr(presentation_page, "advance_playback_if_due", lambda _: None)
    monkeypatch.setattr(
        presentation_page,
        "render_committed_step_controls",
        lambda _: 2,
    )
    options = WorldViewOptions(
        show_resources=False,
        show_carcasses=False,
        show_trails=True,
        trail_length=7,
        show_labels=True,
    )
    monkeypatch.setattr(presentation_page, "render_view_controls", lambda _: options)
    monkeypatch.setattr(
        presentation_page,
        "observed_organism_ids",
        lambda _: (7,),
    )
    monkeypatch.setattr(
        presentation_page,
        "render_organism_selector",
        lambda *_a, **_k: 7,
    )
    provenance = _provenance("rev", "digest", ())
    built = _world_presentation(provenance, seed=11, step=2)
    captured: dict[str, Any] = {}

    def build(*_: object, **kwargs: Any) -> WorkbenchWorldPresentation:
        captured.update(kwargs)
        return built

    monkeypatch.setattr(
        presentation_page,
        "build_reference_workbench_world_presentation",
        build,
    )
    monkeypatch.setattr(
        presentation_page,
        "_render_single_world",
        lambda *_a, **_k: None,
    )
    presentation_page._render_reference_world(
        revision,
        result,
        available_view,
        focus_mode=False,
    )
    assert captured == {
        "step_index": 2,
        "selected_organism_id": 7,
        "show_resources": False,
        "show_carcasses": False,
        "show_trails": True,
        "trail_length": 7,
    }
    assert fake.reruns == 0

    monkeypatch.setattr(presentation_page, "available_step_indices", lambda _: ())
    presentation_page._render_reference_world(
        revision,
        result,
        available_view,
        focus_mode=False,
    )
    assert any("no committed spatial frames" in value for value in _messages(fake, "error"))


def test_b3_landing_and_world_paths_are_scenario_specific(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, view = _b3_fixture()
    monkeypatch.setattr(presentation_page, "presentation_experience", lambda: "landing")
    story_calls: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "_render_b3_story",
        lambda *_: story_calls.append("story"),
    )
    presentation_page._render_b3_presentation(
        revision,
        result,
        view,
        focus_mode=False,
    )
    assert any(
        "No B3 confirmation replay" in value for value in _messages(fake, "info")
    )
    assert story_calls == ["story"]

    confirmation_view = cast(
        B3ResultsView,
        SimpleNamespace(confirmation=(object(),)),
    )
    fake.buttons["Open World Explorer"] = True
    opened: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "open_world_explorer",
        lambda: opened.append("world"),
    )
    presentation_page._render_b3_presentation(
        revision,
        result,
        confirmation_view,
        focus_mode=False,
    )
    assert opened == ["world"]

    monkeypatch.setattr(presentation_page, "presentation_experience", lambda: "world")
    routed: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "_render_b3_world",
        lambda *_a, **_k: routed.append("b3-world"),
    )
    presentation_page._render_b3_presentation(
        revision,
        result,
        confirmation_view,
        focus_mode=False,
    )
    assert routed == ["b3-world"]


def test_b3_world_synchronizes_seed_step_and_builds_arms_independently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, _ = _b3_fixture()
    summary = SimpleNamespace(seed=13)
    control_evidence = SimpleNamespace(spatial_observations=(SimpleNamespace(step_index=0, organisms=()),))
    treatment_evidence = SimpleNamespace(spatial_observations=(SimpleNamespace(step_index=0, organisms=()),))
    pair = SimpleNamespace(
        summary=summary,
        control_evidence=control_evidence,
        treatment_evidence=treatment_evidence,
    )
    view = cast(B3ResultsView, SimpleNamespace(confirmation=(pair,)))
    monkeypatch.setattr(presentation_page, "selected_b3_seed", lambda _: 13)
    monkeypatch.setattr(presentation_page, "common_step_indices", lambda *_: (0, 2))
    monkeypatch.setattr(presentation_page, "initialize_world_state", lambda _: None)
    monkeypatch.setattr(presentation_page, "playback_interval", lambda: None)
    monkeypatch.setattr(presentation_page, "advance_playback_if_due", lambda _: None)
    monkeypatch.setattr(presentation_page, "render_committed_step_controls", lambda _: 2)
    options = WorldViewOptions(
        show_resources=True,
        show_carcasses=False,
        show_trails=True,
        trail_length=6,
        show_labels=False,
    )
    monkeypatch.setattr(presentation_page, "render_view_controls", lambda _: options)
    monkeypatch.setattr(presentation_page, "observed_organism_ids", lambda _: (7,))
    selections = iter((7, None))
    monkeypatch.setattr(
        presentation_page,
        "render_organism_selector",
        lambda *_a, **_k: next(selections),
    )
    provenance = _provenance("rev", "digest", ())
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=4,
    )
    calls: list[dict[str, Any]] = []

    def build(*_: object, **kwargs: Any) -> WorkbenchWorldPresentation:
        calls.append(kwargs)
        return _world_presentation(
            provenance,
            seed=13,
            step=2,
            arm=cast(str, kwargs["arm"]),
            environment=cast(str, kwargs["arm"]),
            encoding=encoding,
        )

    monkeypatch.setattr(
        presentation_page,
        "build_b3_workbench_world_presentation",
        build,
    )
    monkeypatch.setattr(presentation_page, "_render_b3_pair", lambda *_a, **_k: None)
    presentation_page._render_b3_world(
        revision,
        result,
        view,
        focus_mode=False,
    )
    assert [call["arm"] for call in calls] == ["control", "treatment"]
    assert {call["seed"] for call in calls} == {13}
    assert {call["step_index"] for call in calls} == {2}
    assert calls[0]["selected_organism_id"] == 7
    assert calls[1]["selected_organism_id"] is None

    monkeypatch.setattr(presentation_page, "common_step_indices", lambda *_: ())
    presentation_page._render_b3_world(
        revision,
        result,
        view,
        focus_mode=False,
    )
    assert any("no shared recorded" in value for value in _messages(fake, "error"))


def test_b3_story_distinguishes_science_from_optional_renderer_and_view_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, view = _b3_fixture()
    unavailable_view = cast(
        B3ResultsView,
        SimpleNamespace(cinematic_handoff_availability=_unavailable("b3.story")),
    )
    presentation_page._render_b3_story(revision, result, unavailable_view)
    assert any(
        "B3 SCIENTIFIC STORY UNAVAILABLE" in value
        for value in _messages(fake, "error")
    )

    marker = object()
    monkeypatch.setattr(
        presentation_page,
        "prepare_b3_workbench_cinematic",
        lambda *_: marker,
    )
    monkeypatch.setattr(presentation_page, "b3_renderer_available", lambda: False)
    presentation_page._render_b3_story(revision, result, view)
    assert any(
        "scientific cinematic is available" in value.lower()
        for value in _messages(fake, "info")
    )

    fake.calls.clear()

    def bad_prepare(*_: object) -> object:
        raise ValueError("invalid handoff")

    monkeypatch.setattr(
        presentation_page,
        "prepare_b3_workbench_cinematic",
        bad_prepare,
    )
    presentation_page._render_b3_story(revision, result, view)
    assert any(
        "handoff could not be prepared" in value.lower()
        for value in _messages(fake, "error")
    )

    monkeypatch.setattr(
        presentation_page,
        "prepare_b3_workbench_cinematic",
        lambda *_: marker,
    )
    monkeypatch.setattr(presentation_page, "b3_renderer_available", lambda: True)
    fake.selections["wu5_presentation_cinematic_quality"] = "high"
    fake.selections["wu5_presentation_cinematic_output"] = "gif"
    fake.buttons["Render B3 Scientific Story"] = True
    monkeypatch.setattr(
        presentation_page,
        "render_b3_story_artifact",
        lambda *_a, **_k: (b"story", "image/gif", "b3_scientific_story.gif"),
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


def test_cached_story_previews_video_and_gif(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_presentation_page_rejects_stale_result_and_routes_supported_families(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision, result, view = _reference_fixture()
    monkeypatch.setattr(
        presentation_page,
        "is_authoritative_run_result",
        lambda _: True,
    )

    def stale(*_: object) -> object:
        raise ValueError("different scientific owner")

    monkeypatch.setattr(presentation_page, "inspect_current_results", stale)
    presentation_page.render_presentation_page(revision, result)
    assert any(
        "PRESENTATION UNAVAILABLE" in value for value in _messages(fake, "error")
    )

    routed: list[str] = []
    monkeypatch.setattr(
        presentation_page,
        "inspect_current_results",
        lambda *_: view,
    )
    monkeypatch.setattr(
        presentation_page,
        "ensure_presentation_owner",
        lambda _: routed.append("owner"),
    )
    monkeypatch.setattr(
        presentation_page,
        "_render_reference_presentation",
        lambda *_a, **_k: routed.append("reference"),
    )
    presentation_page.render_presentation_page(revision, result)
    assert routed == ["owner", "reference"]

    b3_revision, b3_result, b3_view = _b3_fixture()
    routed.clear()
    monkeypatch.setattr(
        presentation_page,
        "inspect_current_results",
        lambda *_: b3_view,
    )
    monkeypatch.setattr(
        presentation_page,
        "_render_b3_presentation",
        lambda *_a, **_k: routed.append("b3"),
    )
    presentation_page.render_presentation_page(
        b3_revision,
        b3_result,
        focus_mode=True,
    )
    assert routed == ["owner", "b3"]


def test_presentation_page_without_session_result_never_reruns_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    revision = new_reference_ecology(revision_id="wu5-no-result")
    monkeypatch.setattr(
        presentation_page,
        "is_authoritative_run_result",
        lambda _: False,
    )
    monkeypatch.setattr(presentation_page, "artifact_run_count", lambda _: 1)
    presentation_page.render_presentation_page(revision, None)
    assert any(
        "historical run" in value.lower() for value in _messages(fake, "info")
    )
    assert not fake.reruns
