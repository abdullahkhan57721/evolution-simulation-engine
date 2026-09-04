"""World-centered completed-result workspace for the interactive simulator."""

from __future__ import annotations

from typing import Literal

import streamlit as st

from evo_engine.experiments import ReferenceExperimentResult
from evo_engine.genetics import MAX_INTAKE_RATE
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
    spatial_world_figure,
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

WorkspaceAction = Literal["edit", "rerun", "new"] | None


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
    world_column, science_column = st.columns([4, 1.2])
    with world_column:
        st.subheader("World")
        st.caption(
            "Committed spatial observations are authoritative. This Plotly surface "
            "is the migration-stage world renderer for I1; the later V2 primitive "
            "ticket owns the renderer upgrade."
        )
        st.plotly_chart(
            spatial_world_figure(run.spatial_history),
            use_container_width=True,
            key="spatial-world-workspace",
        )
    with science_column:
        st.subheader("Key science")
        st.metric("Completed steps", run.completed_steps)
        st.metric("Population", run.final_population_size)
        st.metric("Resources", run.final_total_resources)
        st.metric("Mean energy", _final_mean_energy(run))
        st.metric("Births", run.total_births)
        st.metric("Deaths", run.total_deaths)


def _final_mean_energy(run: DashboardRun) -> str:
    if not run.population_history:
        return "0.0"
    return f"{run.population_history[-1].energy.mean:.1f}"


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
