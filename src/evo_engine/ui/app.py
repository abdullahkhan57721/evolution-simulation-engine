"""Streamlit portfolio dashboard for the reference ecology."""

from __future__ import annotations

import streamlit as st

from evo_engine.experiments import ReferenceExperimentResult
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
    DashboardRun,
    build_curated_config,
    parse_seed_list,
    run_dashboard_experiment,
    run_dashboard_reference,
)

_RUN_KEY = "portfolio_dashboard_run"
_EXPERIMENT_KEY = "portfolio_experiment_result"


def main() -> None:
    """Render the complete interactive portfolio dashboard."""
    st.set_page_config(
        page_title="Evolution Simulation Engine",
        page_icon="🧬",
        layout="wide",
    )
    st.title("Evolution Simulation Engine")
    st.caption(
        "A reproducible reference ecology viewed through committed simulation "
        "observations — spatial dynamics, evolution, genetics, life history, "
        "experiments, and exports."
    )

    submitted_config = _configuration_controls()
    if submitted_config is not None:
        try:
            with st.spinner("Running reference ecology…"):
                st.session_state[_RUN_KEY] = run_dashboard_reference(submitted_config)
            st.session_state.pop(_EXPERIMENT_KEY, None)
        except (TypeError, ValueError) as exc:
            st.error(f"Simulation configuration could not be run: {exc}")

    run = st.session_state.get(_RUN_KEY)
    if not isinstance(run, DashboardRun):
        st.info(
            "Choose a curated configuration in the sidebar, then select "
            "**Run simulation** to create a committed result set."
        )
        _render_architecture_note()
        return

    _render_kpis(run)
    world_tab, population_tab, genetics_tab, events_tab, experiments_tab = st.tabs(
        [
            "World",
            "Population",
            "Genetics",
            "Events & Life History",
            "Experiments & Export",
        ]
    )

    with world_tab:
        _render_world(run)
    with population_tab:
        _render_population(run)
    with genetics_tab:
        _render_genetics(run)
    with events_tab:
        _render_events(run)
    with experiments_tab:
        _render_experiments(run)


def _configuration_controls():
    st.sidebar.header("Reference ecology")
    st.sidebar.caption(
        "A curated subset of validated model parameters. High-level choices "
        "show only controls that affect the active configuration."
    )

    seed = int(st.sidebar.number_input("Seed", value=42, step=1))
    max_steps = int(
        st.sidebar.number_input(
            "Steps",
            min_value=1,
            max_value=500,
            value=30,
            step=1,
        )
    )
    initial_population = int(
        st.sidebar.number_input(
            "Founder population",
            min_value=1,
            max_value=500,
            value=20,
            step=1,
        )
    )
    width = int(
        st.sidebar.number_input(
            "World width",
            min_value=1,
            max_value=50,
            value=12,
            step=1,
        )
    )
    height = int(
        st.sidebar.number_input(
            "World height",
            min_value=1,
            max_value=50,
            value=12,
            step=1,
        )
    )
    initial_energy = int(
        st.sidebar.number_input(
            "Founder energy",
            min_value=0,
            max_value=500,
            value=30,
            step=1,
        )
    )

    st.sidebar.markdown("**Evolutionary variation**")
    mutation_enabled = st.sidebar.checkbox(
        "Enable mutation",
        value=True,
        help="When disabled, mutation probability and maximum change are normalized to zero.",
    )
    mutation_percent: int | None = None
    mutation_max_change: int | None = None
    if mutation_enabled:
        mutation_percent = st.sidebar.slider(
            "Mutation probability (%)",
            min_value=0,
            max_value=100,
            value=1,
            step=1,
        )
        mutation_max_change = int(
            st.sidebar.number_input(
                "Maximum mutation step",
                min_value=0,
                max_value=20,
                value=1,
                step=1,
            )
        )

    recombination_enabled = st.sidebar.checkbox(
        "Enable recombination",
        value=True,
        help="When disabled, the configured crossover probability is normalized to zero.",
    )
    recombination_percent: int | None = None
    if recombination_enabled:
        recombination_percent = st.sidebar.slider(
            "Recombination probability (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=1,
        )

    st.sidebar.markdown("**Ecology and founder traits**")
    resource_generation_amount = int(
        st.sidebar.number_input(
            "Resource units per deposit",
            min_value=1,
            max_value=100,
            value=6,
            step=1,
        )
    )
    resource_deposits_per_step = int(
        st.sidebar.number_input(
            "Resource deposits per step",
            min_value=1,
            max_value=100,
            value=8,
            step=1,
        )
    )
    growth_rate = st.sidebar.slider(
        "Founder growth rate",
        min_value=0,
        max_value=4,
        value=1,
        step=1,
    )
    submitted = st.sidebar.button(
        "Run simulation",
        type="primary",
        use_container_width=True,
    )

    if not submitted:
        return None

    try:
        return build_curated_config(
            seed=seed,
            max_steps=max_steps,
            initial_population=initial_population,
            width=width,
            height=height,
            initial_energy=initial_energy,
            mutation_enabled=mutation_enabled,
            mutation_percent=mutation_percent,
            mutation_max_change=mutation_max_change,
            recombination_enabled=recombination_enabled,
            recombination_percent=recombination_percent,
            resource_generation_amount=resource_generation_amount,
            resource_deposits_per_step=resource_deposits_per_step,
            growth_rate=growth_rate,
        )
    except (TypeError, ValueError) as exc:
        st.sidebar.error(f"Invalid reference configuration: {exc}")
        return None


def _render_kpis(run: DashboardRun) -> None:
    columns = st.columns(5)
    columns[0].metric("Completed steps", run.completed_steps)
    columns[1].metric("Final population", run.final_population_size)
    columns[2].metric("Births", run.total_births)
    columns[3].metric("Deaths", run.total_deaths)
    columns[4].metric("Final resources", run.final_total_resources)


def _render_world(run: DashboardRun) -> None:
    st.subheader("Committed spatial dynamics")
    st.caption(
        "Every frame is an immutable post-commit observation. Marker size reflects "
        "organism body mass or resource amount; hover an organism for individual state."
    )
    st.plotly_chart(
        spatial_world_figure(run.spatial_history),
        use_container_width=True,
        key="spatial-world",
    )
    st.caption(
        "The viewer never reconstructs history from mutable live worlds. Births, "
        "deaths, resources, and carcasses appear only after the corresponding state commits."
    )


def _render_population(run: DashboardRun) -> None:
    st.subheader("Population and ecological state")
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

    trait_names = _trait_names(run)
    if not trait_names:
        st.info("No heritable trait summaries were recorded.")
        return
    trait_name = st.selectbox(
        "Inspect heritable trait",
        trait_names,
        index=_preferred_index(trait_names, "growth_rate"),
    )
    trait_left, trait_right = st.columns(2)
    with trait_left:
        st.plotly_chart(
            trait_mean_figure(run.population_history, trait_name=trait_name),
            use_container_width=True,
            key="trait-mean",
        )
    with trait_right:
        st.plotly_chart(
            trait_distribution_figure(run.population_history, trait_name=trait_name),
            use_container_width=True,
            key="trait-distribution",
        )


def _render_genetics(run: DashboardRun) -> None:
    st.subheader("Raw genetic composition")
    st.caption(
        "Allele and genotype views read inherited genomes directly, so hidden "
        "genetic variation remains visible even when expression maps genotypes together."
    )
    locus_names = _locus_names(run)
    if not locus_names:
        st.info("No genetic loci were recorded.")
        return
    locus_name = st.selectbox(
        "Inspect locus",
        locus_names,
        index=_preferred_index(locus_names, "growth_rate"),
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


def _render_events(run: DashboardRun) -> None:
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


def _render_experiments(run: DashboardRun) -> None:
    st.subheader("Reproducible multi-seed experiments")
    st.caption(
        "Replicates are executed by `evo_engine.experiments.run_reference_replicates`; "
        "the dashboard does not duplicate experiment orchestration."
    )
    seed_text = st.text_input("Experiment seeds", value="11, 22, 33")
    if st.button("Run experiment", type="primary"):
        try:
            seeds = parse_seed_list(seed_text)
            with st.spinner("Running independent replicates…"):
                st.session_state[_EXPERIMENT_KEY] = run_dashboard_experiment(
                    run.config,
                    seeds=seeds,
                )
        except (TypeError, ValueError) as exc:
            st.error(f"Experiment could not be run: {exc}")

    experiment = st.session_state.get(_EXPERIMENT_KEY)
    if not isinstance(experiment, ReferenceExperimentResult):
        st.info(
            "Run a small seed set to compare replicate outcomes and enable exports."
        )
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

    st.markdown("**Export the existing experiment result formats**")
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


def _render_architecture_note() -> None:
    with st.expander("What this dashboard demonstrates"):
        st.markdown(
            """
- **Domain-neutral orchestration:** the frozen kernel runs configured processes without UI knowledge.
- **Transactional state:** observations are offered only after a successful commit.
- **Separated evidence:** spatial frames, phenotype summaries, raw genetics, causal events, and pedigree/life history retain distinct responsibilities.
- **Reproducibility:** seeded multi-run experiments reuse the engine's experiment API and canonical exports.
            """
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


if __name__ == "__main__":
    main()
