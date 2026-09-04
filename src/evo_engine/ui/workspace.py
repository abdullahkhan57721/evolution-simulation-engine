"""World-centered completed-result workspace for the interactive simulator."""

from __future__ import annotations

import time
from typing import Literal

import streamlit as st

from evo_engine.experiments import ReferenceExperimentResult
from evo_engine.genetics import MAX_INTAKE_RATE
from evo_engine.observation import PopulationObservation
from evo_engine.ui.charts import (
    allele_frequency_figure,
    environment_figure,
    event_activity_figure,
    experiment_outcomes_figure,
    experiment_population_figure,
    experiment_summary_rows,
    genotype_frequency_figure,
    mating_type_figure,
    mortality_figure,
    organism_summary_figure,
    population_size_figure,
    reproductive_success_figure,
    top_reproductive_success_rows,
    trait_distribution_figure,
    trait_mean_figure,
)
from evo_engine.ui.exports import build_experiment_downloads
from evo_engine.ui.models import (
    FLAGSHIP_MAX_INTAKE_SCENARIO,
    DashboardRun,
    parse_seed_list,
    run_dashboard_experiment,
)
from evo_engine.ui.world_presentation import (
    WorldPresentationFrame,
    available_step_indices,
    build_world_presentation,
    spatial_frame_for_step,
)
from evo_engine.ui.world_renderer import world_presentation_figure

WorkspaceAction = Literal["edit", "rerun", "new"] | None

_WORLD_STEP_KEY = "v2_world_step"
_WORLD_PLAYING_KEY = "v2_world_playing"
_WORLD_SPEED_KEY = "v2_world_speed"
_WORLD_NEXT_ADVANCE_KEY = "v2_world_next_advance"
_WORLD_SELECTED_ORGANISM_KEY = "v2_world_selected_organism"
_WORLD_RESOURCES_KEY = "v2_world_show_resources"
_WORLD_CARCASSES_KEY = "v2_world_show_carcasses"
_WORLD_TRAILS_KEY = "v2_world_show_trails"
_WORLD_TRAIL_LENGTH_KEY = "v2_world_trail_length"
_WORLD_LABELS_KEY = "v2_world_show_labels"
_WORLD_SESSION_KEYS = (
    _WORLD_STEP_KEY,
    _WORLD_PLAYING_KEY,
    _WORLD_SPEED_KEY,
    _WORLD_NEXT_ADVANCE_KEY,
    _WORLD_SELECTED_ORGANISM_KEY,
    _WORLD_RESOURCES_KEY,
    _WORLD_CARCASSES_KEY,
    _WORLD_TRAILS_KEY,
    _WORLD_TRAIL_LENGTH_KEY,
    _WORLD_LABELS_KEY,
)
_PLAYBACK_SPEEDS = (0.5, 1.0, 2.0)
_BASE_PLAYBACK_INTERVAL_SECONDS = 0.6


def render_simulation_workspace(
    run: DashboardRun,
    *,
    experiment_key: str,
) -> WorkspaceAction:
    """Render one completed immutable run as the world-centered workspace."""
    st.title("Evolution Simulation Engine")
    action = _workspace_header(run)
    if action is not None:
        return action

    if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO:
        st.caption(
            "Curated scenario · illustrative engine demonstration, not a calibrated "
            "ecological prediction."
        )
    else:
        st.caption(
            f"Custom experiment · seed {run.config.seed} · "
            f"{run.completed_steps} committed steps"
        )

    _world_and_headline_science(run)
    _analysis_tabs(run, experiment_key=experiment_key)
    return None


def reset_world_presentation_state() -> None:
    """Clear renderer/view state when a completed run is replaced."""
    for key in _WORLD_SESSION_KEYS:
        st.session_state.pop(key, None)


def _workspace_header(run: DashboardRun) -> WorkspaceAction:
    title_col, edit_col, rerun_col, new_col = st.columns([5, 1.4, 1.2, 1.4])
    title = (
        "Flagship evolutionary demonstration"
        if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO
        else "Reference ecology experiment"
    )
    title_col.subheader(title)
    if edit_col.button("Edit configuration", use_container_width=True):
        return "edit"
    if rerun_col.button("Rerun", use_container_width=True):
        return "rerun"
    if new_col.button("New simulation", use_container_width=True):
        return "new"
    return None


def _world_and_headline_science(run: DashboardRun) -> None:
    steps = available_step_indices(run.spatial_history)
    if not steps:
        st.info("No spatial observations were recorded for this completed run.")
        return
    _initialize_world_state(steps)
    interval = _playback_interval() if st.session_state[_WORLD_PLAYING_KEY] else None

    @st.fragment(run_every=interval)
    def world_fragment() -> None:
        _advance_playback_if_due(steps)
        _world_controls(run, steps)
        selected_step = _selected_step(steps)
        presentation = build_world_presentation(
            run.spatial_history,
            step_index=selected_step,
            selected_organism_id=st.session_state[_WORLD_SELECTED_ORGANISM_KEY],
            show_resources=st.session_state[_WORLD_RESOURCES_KEY],
            show_carcasses=st.session_state[_WORLD_CARCASSES_KEY],
            show_trails=st.session_state[_WORLD_TRAILS_KEY],
            trail_length=st.session_state[_WORLD_TRAIL_LENGTH_KEY],
        )
        world_column, science_column = st.columns([4, 1.2])
        with world_column:
            _render_world(presentation)
        with science_column:
            _render_context(run, presentation)

    world_fragment()


def _initialize_world_state(steps: tuple[int, ...]) -> None:
    if _WORLD_STEP_KEY not in st.session_state:
        st.session_state[_WORLD_STEP_KEY] = steps[0]
    if st.session_state[_WORLD_STEP_KEY] not in steps:
        st.session_state[_WORLD_STEP_KEY] = steps[0]
    st.session_state.setdefault(_WORLD_PLAYING_KEY, False)
    st.session_state.setdefault(_WORLD_SPEED_KEY, 1.0)
    st.session_state.setdefault(_WORLD_SELECTED_ORGANISM_KEY, None)
    st.session_state.setdefault(_WORLD_RESOURCES_KEY, True)
    st.session_state.setdefault(_WORLD_CARCASSES_KEY, True)
    st.session_state.setdefault(_WORLD_TRAILS_KEY, True)
    st.session_state.setdefault(_WORLD_TRAIL_LENGTH_KEY, 5)
    st.session_state.setdefault(_WORLD_LABELS_KEY, False)


def _world_controls(run: DashboardRun, steps: tuple[int, ...]) -> None:
    selected_step = _selected_step(steps)
    previous_col, play_col, next_col, speed_col = st.columns([1, 1, 1, 1.4])
    if previous_col.button(
        "Previous",
        disabled=selected_step == steps[0],
        use_container_width=True,
    ):
        st.session_state[_WORLD_STEP_KEY] = _previous_step(steps, selected_step)
        st.session_state[_WORLD_PLAYING_KEY] = False
    if st.session_state[_WORLD_PLAYING_KEY]:
        if play_col.button("Pause", use_container_width=True):
            st.session_state[_WORLD_PLAYING_KEY] = False
            st.session_state.pop(_WORLD_NEXT_ADVANCE_KEY, None)
            st.rerun(scope="app")
    elif play_col.button(
        "Play",
        disabled=selected_step == steps[-1],
        use_container_width=True,
    ):
        st.session_state[_WORLD_PLAYING_KEY] = True
        st.session_state[_WORLD_NEXT_ADVANCE_KEY] = (
            time.monotonic() + _playback_interval()
        )
        st.rerun(scope="app")
    if next_col.button(
        "Next",
        disabled=selected_step == steps[-1],
        use_container_width=True,
    ):
        st.session_state[_WORLD_STEP_KEY] = _next_step(steps, selected_step)
        st.session_state[_WORLD_PLAYING_KEY] = False

    speed = speed_col.selectbox(
        "Playback speed",
        _PLAYBACK_SPEEDS,
        index=_PLAYBACK_SPEEDS.index(st.session_state[_WORLD_SPEED_KEY]),
        format_func=lambda value: f"{value:g}×",
    )
    if speed != st.session_state[_WORLD_SPEED_KEY]:
        st.session_state[_WORLD_SPEED_KEY] = speed
        if st.session_state[_WORLD_PLAYING_KEY]:
            st.session_state[_WORLD_NEXT_ADVANCE_KEY] = (
                time.monotonic() + _playback_interval()
            )
            st.rerun(scope="app")

    selected_step = st.select_slider(
        "Committed step",
        options=steps,
        value=_selected_step(steps),
    )
    if selected_step != st.session_state[_WORLD_STEP_KEY]:
        st.session_state[_WORLD_STEP_KEY] = selected_step
        st.session_state[_WORLD_PLAYING_KEY] = False
        st.session_state.pop(_WORLD_NEXT_ADVANCE_KEY, None)

    with st.expander("View configuration", expanded=False):
        view_columns = st.columns(4)
        st.session_state[_WORLD_RESOURCES_KEY] = view_columns[0].checkbox(
            "Resources",
            value=st.session_state[_WORLD_RESOURCES_KEY],
        )
        st.session_state[_WORLD_CARCASSES_KEY] = view_columns[1].checkbox(
            "Carcasses",
            value=st.session_state[_WORLD_CARCASSES_KEY],
        )
        st.session_state[_WORLD_TRAILS_KEY] = view_columns[2].checkbox(
            "Movement trails",
            value=st.session_state[_WORLD_TRAILS_KEY],
        )
        st.session_state[_WORLD_LABELS_KEY] = view_columns[3].checkbox(
            "Organism labels",
            value=st.session_state[_WORLD_LABELS_KEY],
        )
        st.session_state[_WORLD_TRAIL_LENGTH_KEY] = st.slider(
            "Trail length (committed frames)",
            min_value=2,
            max_value=12,
            value=st.session_state[_WORLD_TRAIL_LENGTH_KEY],
            disabled=not st.session_state[_WORLD_TRAILS_KEY],
        )

    organism_ids = _all_observed_organism_ids(run)
    selected_id = st.selectbox(
        "Selected organism",
        (None, *organism_ids),
        index=_selection_index(organism_ids),
        format_func=lambda value: "None" if value is None else f"Organism {value}",
        help=(
            "Selection is an interaction focus only. It changes the outline and "
            "inspector, never the organism's scientific fill encoding."
        ),
    )
    st.session_state[_WORLD_SELECTED_ORGANISM_KEY] = selected_id


def _render_world(presentation: WorldPresentationFrame) -> None:
    st.subheader("World")
    st.caption(
        "Positions, resources, carcasses, and inspector values come from the selected "
        "committed state. Trails and selection are display-only presentation."
    )
    st.plotly_chart(
        world_presentation_figure(
            presentation,
            show_labels=st.session_state[_WORLD_LABELS_KEY],
        ),
        use_container_width=True,
        key="interactive-world-workspace",
    )


def _render_context(run: DashboardRun, presentation: WorldPresentationFrame) -> None:
    observation = _population_observation_for_step(
        run,
        step_index=presentation.committed_step_index,
    )
    st.subheader("Key science")
    st.metric("Committed step", presentation.committed_step_index)
    if observation is None:
        spatial = spatial_frame_for_step(
            run.spatial_history,
            step_index=presentation.committed_step_index,
        )
        st.metric("Population", len(spatial.organisms))
        st.metric("Resources", sum(item.amount for item in spatial.resources))
        st.metric("Mean energy", "—")
        st.metric("Mean body mass", "—")
        st.metric("Carcasses", len(spatial.carcasses))
    else:
        st.metric("Population", observation.population_size)
        st.metric("Resources", observation.total_resources)
        st.metric("Mean energy", _summary_mean(observation.energy.mean))
        st.metric("Mean body mass", _summary_mean(observation.body_mass.mean))
        st.metric("Carcasses", observation.carcass_count)
    st.markdown("#### Selected organism")
    selected = presentation.selected_organism()
    if presentation.selected_organism_id is None:
        st.caption("Choose an organism to inspect its authoritative committed state.")
    elif selected is None:
        st.info(
            f"Organism {presentation.selected_organism_id} is not active at committed "
            f"step {presentation.committed_step_index}."
        )
    else:
        st.write(f"**ID:** {selected.organism_id}")
        st.write(f"**Position:** ({selected.x:g}, {selected.y:g})")
        st.write(f"**Age:** {selected.age}")
        st.write(f"**Energy:** {selected.energy}")
        st.write(f"**Body mass:** {selected.body_mass}")
        st.write(f"**Mating type:** {selected.mating_type}")


def _advance_playback_if_due(steps: tuple[int, ...]) -> None:
    if not st.session_state[_WORLD_PLAYING_KEY]:
        return
    current = _selected_step(steps)
    if current == steps[-1]:
        st.session_state[_WORLD_PLAYING_KEY] = False
        st.session_state.pop(_WORLD_NEXT_ADVANCE_KEY, None)
        st.rerun(scope="app")
    deadline = st.session_state.get(_WORLD_NEXT_ADVANCE_KEY)
    if not isinstance(deadline, float):
        st.session_state[_WORLD_NEXT_ADVANCE_KEY] = (
            time.monotonic() + _playback_interval()
        )
        return
    if time.monotonic() < deadline:
        return
    next_step = _next_step(steps, current)
    st.session_state[_WORLD_STEP_KEY] = next_step
    if next_step == steps[-1]:
        st.session_state[_WORLD_PLAYING_KEY] = False
        st.session_state.pop(_WORLD_NEXT_ADVANCE_KEY, None)
        st.rerun(scope="app")
    st.session_state[_WORLD_NEXT_ADVANCE_KEY] = time.monotonic() + _playback_interval()


def _playback_interval() -> float:
    return _BASE_PLAYBACK_INTERVAL_SECONDS / float(st.session_state[_WORLD_SPEED_KEY])


def _selected_step(steps: tuple[int, ...]) -> int:
    value = st.session_state[_WORLD_STEP_KEY]
    return value if isinstance(value, int) and value in steps else steps[0]


def _previous_step(steps: tuple[int, ...], current: int) -> int:
    index = steps.index(current)
    return steps[max(0, index - 1)]


def _next_step(steps: tuple[int, ...], current: int) -> int:
    index = steps.index(current)
    return steps[min(len(steps) - 1, index + 1)]


def _all_observed_organism_ids(run: DashboardRun) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                organism.organism_id
                for frame in run.spatial_history
                for organism in frame.organisms
            }
        )
    )


def _selection_index(organism_ids: tuple[int, ...]) -> int:
    selected = st.session_state[_WORLD_SELECTED_ORGANISM_KEY]
    if selected is None:
        return 0
    try:
        return organism_ids.index(selected) + 1
    except ValueError:
        st.session_state[_WORLD_SELECTED_ORGANISM_KEY] = None
        return 0


def _population_observation_for_step(
    run: DashboardRun,
    *,
    step_index: int,
) -> PopulationObservation | None:
    for observation in run.population_history:
        if observation.step_index == step_index:
            return observation
    return None


def _summary_mean(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f}"


def _analysis_tabs(run: DashboardRun, *, experiment_key: str) -> None:
    (
        overview_tab,
        evolution_tab,
        genetics_tab,
        lineage_tab,
        experiments_tab,
        reports_tab,
    ) = st.tabs(
        [
            "Overview / Ecology",
            "Evolution",
            "Genetics",
            "Lineages / Life history",
            "Experiments",
            "Reports / Export",
        ]
    )
    with overview_tab:
        _overview(run)
    with evolution_tab:
        _evolution(run)
    with genetics_tab:
        _genetics(run)
    with lineage_tab:
        _life_history(run)
    with experiments_tab:
        _experiments(run, experiment_key=experiment_key)
    with reports_tab:
        _reports(experiment_key=experiment_key)


def _overview(run: DashboardRun) -> None:
    st.subheader("Ecology overview")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            population_size_figure(run.population_history),
            use_container_width=True,
            key="population-size",
        )
        st.plotly_chart(
            organism_summary_figure(run.population_history),
            use_container_width=True,
            key="organism-summary",
        )
    with right:
        st.plotly_chart(
            environment_figure(run.population_history),
            use_container_width=True,
            key="environment-history",
        )
        st.plotly_chart(
            mating_type_figure(run.population_history),
            use_container_width=True,
            key="mating-type-history",
        )


def _evolution(run: DashboardRun) -> None:
    st.subheader("Evolutionary change")
    trait_names = _trait_names(run)
    if not trait_names:
        st.info("No heritable trait summaries were recorded.")
        return
    preferred = (
        MAX_INTAKE_RATE
        if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO
        else "growth_rate"
    )
    trait_name = st.selectbox(
        "Inspect heritable trait",
        trait_names,
        index=_preferred_index(trait_names, preferred),
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            trait_mean_figure(run.population_history, trait_name=trait_name),
            use_container_width=True,
            key="trait-mean",
        )
    with right:
        st.plotly_chart(
            trait_distribution_figure(run.population_history, trait_name=trait_name),
            use_container_width=True,
            key="trait-distribution",
        )


def _genetics(run: DashboardRun) -> None:
    st.subheader("Raw genetic composition")
    st.caption(
        "Allele and genotype views read inherited genomes directly, preserving "
        "genetic variation that expression may map to the same phenotype."
    )
    locus_names = _locus_names(run)
    if not locus_names:
        st.info("No genetic loci were recorded.")
        return
    preferred = (
        MAX_INTAKE_RATE
        if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO
        else "growth_rate"
    )
    locus_name = st.selectbox(
        "Inspect locus",
        locus_names,
        index=_preferred_index(locus_names, preferred),
    )
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            allele_frequency_figure(run.genetic_history, locus_name=locus_name),
            use_container_width=True,
            key="allele-frequency",
        )
    with right:
        st.plotly_chart(
            genotype_frequency_figure(run.genetic_history, locus_name=locus_name),
            use_container_width=True,
            key="genotype-frequency",
        )


def _life_history(run: DashboardRun) -> None:
    st.subheader("Committed events and life history")
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            event_activity_figure(run.telemetry_steps),
            use_container_width=True,
            key="event-activity",
        )
        st.plotly_chart(
            mortality_figure(run.life_histories),
            use_container_width=True,
            key="mortality-causes",
        )
    with right:
        st.plotly_chart(
            reproductive_success_figure(run.life_histories),
            use_container_width=True,
            key="reproductive-success",
        )
        st.markdown("**Highest observed reproductive success**")
        st.dataframe(
            top_reproductive_success_rows(run.life_histories),
            use_container_width=True,
            hide_index=True,
        )
    st.markdown("**Committed event counts by process**")
    st.dataframe(
        tuple({"process": name, "events": count} for name, count in run.event_counts),
        use_container_width=True,
        hide_index=True,
    )


def _experiments(run: DashboardRun, *, experiment_key: str) -> None:
    st.subheader("Reproducible multi-seed experiments")
    if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO:
        default_seeds = "11, 23, 37, 41, 59, 73, 89, 101"
    else:
        default_seeds = "11, 22, 33"
    seed_text = st.text_input("Experiment seeds", value=default_seeds)
    if st.button("Run experiment", type="primary"):
        try:
            seeds = parse_seed_list(seed_text)
            with st.spinner("Running independent replicates…"):
                st.session_state[experiment_key] = run_dashboard_experiment(
                    run.config,
                    seeds=seeds,
                    scenario=run.scenario,
                )
        except (TypeError, ValueError) as exc:
            st.error(f"Experiment could not be run: {exc}")

    experiment = st.session_state.get(experiment_key)
    if not isinstance(experiment, ReferenceExperimentResult):
        st.info("Run a seed set to compare replicate outcomes and enable exports.")
        return
    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            experiment_population_figure(experiment),
            use_container_width=True,
            key="experiment-populations",
        )
    with right:
        st.plotly_chart(
            experiment_outcomes_figure(experiment),
            use_container_width=True,
            key="experiment-outcomes",
        )
    st.dataframe(
        experiment_summary_rows(experiment),
        use_container_width=True,
        hide_index=True,
    )


def _reports(*, experiment_key: str) -> None:
    st.subheader("Reports and export")
    experiment = st.session_state.get(experiment_key)
    if not isinstance(experiment, ReferenceExperimentResult):
        st.info(
            "Run a multi-seed experiment first. Existing canonical JSON/CSV exports "
            "will appear here without rerunning the simulation."
        )
        return
    download_columns = st.columns(3)
    for column, artifact in zip(
        download_columns,
        build_experiment_downloads(experiment),
        strict=True,
    ):
        column.download_button(
            label=f"Download {artifact.filename}",
            data=artifact.data,
            file_name=artifact.filename,
            mime=artifact.mime_type,
            use_container_width=True,
        )


def _trait_names(run: DashboardRun) -> tuple[str, ...]:
    if not run.population_history:
        return ()
    return tuple(item.trait_name for item in run.population_history[0].traits)


def _locus_names(run: DashboardRun) -> tuple[str, ...]:
    if not run.genetic_history:
        return ()
    return tuple(item.locus_name for item in run.genetic_history[0].loci)


def _preferred_index(values: tuple[str, ...], preferred: str) -> int:
    try:
        return values.index(preferred)
    except ValueError:
        return 0
