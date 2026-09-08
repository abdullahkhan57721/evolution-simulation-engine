"""WU5 Presentation experience over exact authoritative Workbench results."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, cast

import streamlit as st

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_api import render_b3_flagship_cinematic
from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan
from evo_engine.cinematic.workbench import prepare_b3_workbench_cinematic
from evo_engine.ui.results_navigation import inspect_current_results
from evo_engine.ui.run_execution import is_authoritative_run_result
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact, artifact_run_count
from evo_engine.ui.workbench import (
    WorkbenchPresentationUnavailableError,
    WorkbenchWorldPresentation,
    build_b3_workbench_world_presentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.ui.world_explorer import (
    WorldViewOptions,
    advance_playback_if_due,
    common_step_indices,
    ensure_presentation_owner,
    initialize_world_state,
    observed_organism_ids,
    open_world_explorer,
    playback_interval,
    presentation_experience,
    render_committed_step_controls,
    render_organism_selector,
    render_view_controls,
    selected_b3_seed,
    set_presentation_focus_mode,
    show_presentation_landing,
)
from evo_engine.ui.world_presentation import (
    WorldPresentationFrame,
    available_step_indices,
)
from evo_engine.ui.world_renderer import world_presentation_figure
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    ReferenceRunResult,
    ReferenceStudyRevision,
)
from evo_engine.workbench.results import (
    AnalysisAvailability,
    B3ResultsView,
    ReferenceStudyResultsView,
)
from evo_engine.workbench.support import analysis_availability_diagnostic

CinematicOutputFormat = Literal["mp4", "gif"]

_RENDER_BYTES_KEY = "wu5_presentation_cinematic_bytes"
_RENDER_FORMAT_KEY = "wu5_presentation_cinematic_format"
_RENDER_QUALITY_KEY = "wu5_presentation_cinematic_rendered_quality"
_RENDER_FILENAME_KEY = "wu5_presentation_cinematic_filename"


def render_presentation_page(
    artifact: ConcreteWorkbenchArtifact,
    result: object,
    *,
    focus_mode: bool = False,
) -> None:
    """Render Presentation for the exact active Study/result association."""
    if focus_mode:
        _render_focus_header()
    else:
        st.header("Presentation")
        st.caption(
            "Explore authoritative committed evidence or use an existing validated "
            "scientific story. Presentation controls never change the Study's science."
        )

    if not is_authoritative_run_result(result):
        _render_no_current_result(artifact)
        return

    try:
        view = inspect_current_results(artifact, result)
    except (TypeError, ValueError) as exc:
        st.error("PRESENTATION UNAVAILABLE FOR THE ACTIVE STUDY")
        st.write(str(exc))
        st.caption(
            "The current-session result will not be displayed under a different "
            "scientific owner."
        )
        return

    if (
        isinstance(artifact, ReferenceStudyRevision)
        and isinstance(result, ReferenceRunResult)
        and isinstance(view, ReferenceStudyResultsView)
    ):
        ensure_presentation_owner(_owner_token(view.provenance))
        _render_reference_presentation(artifact, result, view, focus_mode=focus_mode)
        return

    if (
        isinstance(artifact, B3StudyRevision)
        and isinstance(result, B3CuratedRunResult)
        and isinstance(view, B3ResultsView)
    ):
        ensure_presentation_owner(_owner_token(view.provenance))
        _render_b3_presentation(artifact, result, view, focus_mode=focus_mode)
        return

    st.info(
        "No interactive world presentation is currently defined for this Study type. "
        "Its authoritative scientific Results remain available in Results."
    )


def b3_renderer_available() -> bool:
    """Return whether the optional Manim renderer can be discovered at runtime."""
    try:
        return find_spec("manim") is not None
    except (ImportError, ValueError):
        return False


def render_b3_story_artifact(
    plan: B3FlagshipDirectorPlan,
    *,
    quality: AnimationQuality,
    output_format: CinematicOutputFormat,
) -> tuple[bytes, str, str]:
    """Render the existing B3 director through the existing public renderer API."""
    if output_format not in ("mp4", "gif"):
        raise ValueError("output_format must be 'mp4' or 'gif'.")
    filename = f"b3_scientific_story.{output_format}"
    with TemporaryDirectory(prefix="evo-engine-b3-") as directory:
        destination = Path(directory) / filename
        rendered = render_b3_flagship_cinematic(
            plan,
            destination,
            quality=quality,
        )
        payload = rendered.read_bytes()
    mime = "video/mp4" if output_format == "mp4" else "image/gif"
    return payload, mime, filename


def _render_reference_presentation(
    revision: ReferenceStudyRevision,
    result: ReferenceRunResult,
    view: ReferenceStudyResultsView,
    *,
    focus_mode: bool,
) -> None:
    if presentation_experience() == "world" or focus_mode:
        _render_reference_world(revision, result, view, focus_mode=focus_mode)
        return

    st.subheader("Explore")
    st.markdown("### Interactive World")
    st.write("Replay recorded spatial evidence and inspect exact committed states.")
    if not view.spatial_availability.available:
        _render_unavailable_analysis(view.spatial_availability, world=True)
        return
    if st.button("Open World Explorer", type="primary", use_container_width=True):
        open_world_explorer()
        st.rerun(scope="app")


def _render_b3_presentation(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
    view: B3ResultsView,
    *,
    focus_mode: bool,
) -> None:
    if presentation_experience() == "world" or focus_mode:
        _render_b3_world(revision, result, view, focus_mode=focus_mode)
        return

    st.subheader("Explore")
    st.markdown("### Interactive World")
    st.write(
        "Inspect matched B3 confirmation control and treatment evidence at the same "
        "authoritative seed and committed step."
    )
    if view.confirmation:
        if st.button("Open World Explorer", type="primary", use_container_width=True):
            open_world_explorer()
            st.rerun(scope="app")
    else:
        st.info(
            "No B3 confirmation replay is present in the active authoritative result."
        )

    st.divider()
    st.subheader("Explain")
    st.markdown("### B3 Scientific Story")
    st.write(
        "Use the existing scenario-specific director selected by validated B3 science."
    )
    _render_b3_story(revision, result, view)


def _render_reference_world(
    revision: ReferenceStudyRevision,
    result: ReferenceRunResult,
    view: ReferenceStudyResultsView,
    *,
    focus_mode: bool,
) -> None:
    if not view.spatial_availability.available:
        _render_unavailable_analysis(view.spatial_availability, world=True)
        return
    steps = available_step_indices(view.spatial_observations)
    if not steps:
        st.error(
            "Interactive World is unavailable because no committed spatial frames "
            "exist."
        )
        return
    initialize_world_state(steps)
    _render_world_back_action(focus_mode=focus_mode)
    st.subheader("Reference Ecology · Interactive World")
    st.caption(
        f"Run `{view.provenance.run_id}` · seed {view.scientific_provenance.seed} · "
        "committed evidence only"
    )
    organism_ids = observed_organism_ids(view.spatial_observations)

    @st.fragment(run_every=playback_interval())
    def world_fragment() -> None:
        advance_playback_if_due(steps)
        st.markdown("### Scientific context")
        step = render_committed_step_controls(steps)
        st.markdown("### View")
        options = render_view_controls(steps)
        selected = render_organism_selector(
            organism_ids,
            key_suffix="reference",
        )
        try:
            presentation = build_reference_workbench_world_presentation(
                revision,
                result,
                step_index=step,
                selected_organism_id=selected,
                show_resources=options.show_resources,
                show_carcasses=options.show_carcasses,
                show_trails=options.show_trails,
                trail_length=options.trail_length,
            )
        except WorkbenchPresentationUnavailableError as exc:
            _render_workbench_diagnostic(exc)
            return
        _render_single_world(presentation, options, focus_mode=focus_mode)

    world_fragment()


def _render_b3_world(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
    view: B3ResultsView,
    *,
    focus_mode: bool,
) -> None:
    if not view.confirmation:
        st.error("No B3 confirmation evidence is available for interactive inspection.")
        return
    _render_world_back_action(focus_mode=focus_mode)
    st.subheader("B3 Confirmation · Matched Interactive World")
    st.caption(
        "Same confirmation seed · matched/blocked by seed · different environment. "
        "Treatment-driven trajectories are not assumed to remain RNG-identical."
    )
    st.markdown("### Scientific context")
    seeds = tuple(pair.summary.seed for pair in view.confirmation)
    seed = selected_b3_seed(seeds)
    pair = next(item for item in view.confirmation if item.summary.seed == seed)
    control_history = pair.control_evidence.spatial_observations
    treatment_history = pair.treatment_evidence.spatial_observations
    steps = common_step_indices(control_history, treatment_history)
    if not steps:
        st.error("The matched B3 arms have no shared recorded committed timestep.")
        return
    initialize_world_state(steps)
    control_ids = observed_organism_ids(control_history)
    treatment_ids = observed_organism_ids(treatment_history)

    @st.fragment(run_every=playback_interval())
    def world_fragment() -> None:
        advance_playback_if_due(steps)
        step = render_committed_step_controls(steps)
        st.markdown("### View")
        options = render_view_controls(steps)
        selection_columns = st.columns(2)
        with selection_columns[0]:
            control_selected = render_organism_selector(
                control_ids,
                key_suffix="b3_control",
                label="Control selected organism",
            )
        with selection_columns[1]:
            treatment_selected = render_organism_selector(
                treatment_ids,
                key_suffix="b3_treatment",
                label="Treatment selected organism",
            )
        try:
            control = build_b3_workbench_world_presentation(
                revision,
                result,
                seed=seed,
                arm="control",
                step_index=step,
                selected_organism_id=control_selected,
                show_resources=options.show_resources,
                show_carcasses=options.show_carcasses,
                show_trails=options.show_trails,
                trail_length=options.trail_length,
            )
            treatment = build_b3_workbench_world_presentation(
                revision,
                result,
                seed=seed,
                arm="treatment",
                step_index=step,
                selected_organism_id=treatment_selected,
                show_resources=options.show_resources,
                show_carcasses=options.show_carcasses,
                show_trails=options.show_trails,
                trail_length=options.trail_length,
            )
        except (KeyError, TypeError, ValueError) as exc:
            st.error(f"B3 matched world could not be prepared: {exc}")
            return
        _render_b3_pair(control, treatment, options, focus_mode=focus_mode)

    world_fragment()


def _render_single_world(
    presentation: WorkbenchWorldPresentation,
    options: WorldViewOptions,
    *,
    focus_mode: bool,
) -> None:
    widths = (5, 1) if focus_mode else (4, 1.2)
    world_column, inspector_column = st.columns(widths)
    with world_column:
        st.plotly_chart(
            world_presentation_figure(
                presentation.frame,
                show_labels=options.show_labels,
            ),
            use_container_width=True,
            key="wu5-reference-world",
        )
    with inspector_column:
        st.markdown("#### Context")
        st.write(f"**Seed:** {presentation.seed}")
        st.write(f"**Committed step:** {presentation.frame.committed_step_index}")
        _render_organism_inspector(presentation.frame)


def _render_b3_pair(
    control: WorkbenchWorldPresentation,
    treatment: WorkbenchWorldPresentation,
    options: WorldViewOptions,
    *,
    focus_mode: bool,
) -> None:
    if control.seed != treatment.seed:
        st.error("Matched B3 presentation rejected arms with different seeds.")
        return
    if control.frame.committed_step_index != treatment.frame.committed_step_index:
        st.error(
            "Matched B3 presentation rejected arms with different committed steps."
        )
        return
    if control.frame.focal_encoding != treatment.frame.focal_encoding:
        st.error(
            "Matched B3 presentation rejected inconsistent scientific trait scales."
        )
        return
    columns = st.columns(2)
    with columns[0]:
        st.markdown("#### CONTROL")
        st.caption(f"{control.environment} · seed {control.seed}")
        st.plotly_chart(
            world_presentation_figure(control.frame, show_labels=options.show_labels),
            use_container_width=True,
            key="wu5-b3-control-world",
        )
        _render_organism_inspector(control.frame)
    with columns[1]:
        st.markdown("#### TREATMENT")
        st.caption(f"{treatment.environment} · seed {treatment.seed}")
        st.plotly_chart(
            world_presentation_figure(treatment.frame, show_labels=options.show_labels),
            use_container_width=True,
            key="wu5-b3-treatment-world",
        )
        _render_organism_inspector(treatment.frame)
    encoding = control.frame.focal_encoding
    if encoding is not None:
        st.caption(
            f"Shared scientific encoding · {encoding.label}: "
            f"{encoding.lower_bound:g} → {encoding.upper_bound:g}. "
            "Both arms use the same fixed scale."
        )
    if focus_mode:
        st.caption("Focus Mode enlarges the presentation; it does not change evidence.")


def _render_organism_inspector(frame: WorldPresentationFrame) -> None:
    st.markdown("##### Selected organism")
    selected = frame.selected_organism()
    if frame.selected_organism_id is None:
        st.caption("Choose an organism to inspect its authoritative committed state.")
        return
    if selected is None:
        st.info(
            f"Organism {frame.selected_organism_id} is not active at committed step "
            f"{frame.committed_step_index}."
        )
        return
    st.write(f"**ID:** {selected.organism_id}")
    st.write(f"**Position:** ({selected.x:g}, {selected.y:g})")
    st.write(f"**Age:** {selected.age}")
    st.write(f"**Energy:** {selected.energy}")
    st.write(f"**Body mass:** {selected.body_mass}")
    st.write(f"**Mating type:** {selected.mating_type}")
    if frame.focal_encoding is not None:
        st.write(f"**{frame.focal_encoding.label}:** {selected.focal_trait_value}")


def _render_b3_story(
    revision: B3StudyRevision,
    result: B3CuratedRunResult,
    view: B3ResultsView,
) -> None:
    availability = view.cinematic_handoff_availability
    if not availability.available:
        _render_unavailable_analysis(availability, world=False)
        return
    try:
        plan = prepare_b3_workbench_cinematic(revision, result)
    except ValueError as exc:
        st.error(f"B3 scientific cinematic handoff could not be prepared: {exc}")
        return

    st.success("Validated flagship scientific handoff available.")
    st.caption(
        "Representative seed, scientific episodes, fixed trait scale, comparison "
        "structure, and bounded conclusion are selected by B3 science/director code."
    )
    if not b3_renderer_available():
        st.info(
            "Scientific cinematic is available, but this runtime does not have the "
            "optional Manim renderer installed."
        )
        return

    quality_column, output_column = st.columns(2)
    quality = cast(
        AnimationQuality,
        quality_column.selectbox(
            "Render quality",
            ("low", "medium", "high"),
            index=1,
            key="wu5_presentation_cinematic_quality",
        ),
    )
    output_format = cast(
        CinematicOutputFormat,
        output_column.selectbox(
            "Output",
            ("mp4", "gif"),
            format_func=lambda value: value.upper(),
            key="wu5_presentation_cinematic_output",
        ),
    )
    if st.button("Render B3 Scientific Story", type="primary"):
        try:
            with st.spinner("Rendering the validated B3 scientific story..."):
                payload, mime, filename = render_b3_story_artifact(
                    plan,
                    quality=quality,
                    output_format=output_format,
                )
        except (OSError, RuntimeError, ValueError) as exc:
            st.error(f"B3 renderer unavailable or failed: {exc}")
        else:
            st.session_state[_RENDER_BYTES_KEY] = payload
            st.session_state[_RENDER_FORMAT_KEY] = mime
            st.session_state[_RENDER_QUALITY_KEY] = quality
            st.session_state[_RENDER_FILENAME_KEY] = filename
    _render_cached_story()


def _render_cached_story() -> None:
    payload = st.session_state.get(_RENDER_BYTES_KEY)
    mime = st.session_state.get(_RENDER_FORMAT_KEY)
    filename = st.session_state.get(_RENDER_FILENAME_KEY)
    if (
        not isinstance(payload, bytes)
        or type(mime) is not str
        or type(filename) is not str
    ):
        return
    quality = st.session_state.get(_RENDER_QUALITY_KEY, "unknown")
    st.caption(f"Rendered artifact · {quality} quality · {filename}")
    if mime == "video/mp4":
        st.video(payload, format="video/mp4")
    else:
        st.image(payload, caption="Rendered B3 scientific story")
    st.download_button(
        "Download rendered artifact",
        data=payload,
        file_name=filename,
        mime=mime,
    )


def _render_unavailable_analysis(
    availability: AnalysisAvailability,
    *,
    world: bool,
) -> None:
    diagnostic = analysis_availability_diagnostic(availability)
    if diagnostic is None:
        return
    heading = (
        "INTERACTIVE WORLD UNAVAILABLE" if world else "B3 SCIENTIFIC STORY UNAVAILABLE"
    )
    st.error(heading)
    st.write(diagnostic.message)
    if availability.missing_evidence_ids:
        st.write(
            "**Required evidence:** " + ", ".join(availability.missing_evidence_ids)
        )
    if diagnostic.remediation is not None:
        st.info(diagnostic.remediation)


def _render_workbench_diagnostic(exc: WorkbenchPresentationUnavailableError) -> None:
    st.error("INTERACTIVE WORLD UNAVAILABLE")
    st.write(exc.diagnostic.message)
    if exc.diagnostic.remediation is not None:
        st.info(exc.diagnostic.remediation)


def _render_world_back_action(*, focus_mode: bool) -> None:
    if focus_mode:
        return
    if st.button("← Presentation", key="wu5_presentation_back_to_landing"):
        show_presentation_landing()
        st.rerun(scope="app")


def _render_focus_header() -> None:
    if st.button("← Back to Study", key="wu5_presentation_back_to_study"):
        set_presentation_focus_mode(False)
        st.rerun(scope="app")
    st.title("World Explorer")
    st.caption(
        "Focus Mode · exact committed scientific evidence remains authoritative."
    )


def _render_no_current_result(artifact: ConcreteWorkbenchArtifact) -> None:
    run_count = artifact_run_count(artifact)
    if run_count:
        st.info(
            "Presentation unavailable in this session. The saved Study records the "
            "historical run, but its full result/evidence payload is not loaded."
        )
        st.caption("Historical provenance references are not spatial replay data.")
        return
    st.info(
        "No completed scientific result is available in this session yet. Run this "
        "Study first, then return to Presentation."
    )


def _owner_token(provenance: object) -> str:
    revision_id = getattr(provenance, "study_revision_id", None)
    manifest_digest = getattr(provenance, "manifest_digest", None)
    run_id = getattr(provenance, "run_id", None)
    values = (revision_id, manifest_digest, run_id)
    if not all(type(value) is str and value for value in values):
        raise ValueError(
            "Presentation provenance is missing exact scientific ownership."
        )
    return f"{revision_id}:{manifest_digest}:{run_id}"


__all__ = [
    "b3_renderer_available",
    "render_b3_story_artifact",
    "render_presentation_page",
]
