"""Build Plotly figures from immutable dashboard and experiment records."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

import plotly.graph_objects as go

from evo_engine.experiments import ReferenceExperimentResult
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import StepTelemetry


def spatial_world_figure(history: tuple[SpatialObservation, ...]) -> go.Figure:
    """Build a fixed-bounds animation from committed spatial observations."""
    if not history:
        return _empty_figure("No spatial observations were recorded.")

    width = history[0].world_width
    height = history[0].world_height
    frames = tuple(
        go.Frame(
            name=str(frame.step_index),
            data=_spatial_traces(frame),
        )
        for frame in history
    )
    figure = go.Figure(data=_spatial_traces(history[0]), frames=frames)
    figure.update_layout(
        title="Reference ecology world",
        xaxis={
            "title": "x",
            "range": [-0.5, width - 0.5],
            "dtick": 1,
            "fixedrange": True,
        },
        yaxis={
            "title": "y",
            "range": [height - 0.5, -0.5],
            "dtick": 1,
            "fixedrange": True,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        height=max(500, min(760, height * 42)),
        margin={"l": 35, "r": 20, "t": 55, "b": 35},
        legend={"orientation": "h", "y": 1.08},
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0.0,
                "y": -0.12,
                "showactive": False,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 350, "redraw": True},
                                "transition": {"duration": 0},
                                "fromcurrent": True,
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Committed step "},
                "pad": {"t": 45},
                "steps": [
                    {
                        "label": str(frame.step_index),
                        "method": "animate",
                        "args": [
                            [str(frame.step_index)],
                            {
                                "mode": "immediate",
                                "frame": {"duration": 0, "redraw": True},
                                "transition": {"duration": 0},
                            },
                        ],
                    }
                    for frame in history
                ],
            }
        ],
    )
    return figure


def population_size_figure(history: tuple[PopulationObservation, ...]) -> go.Figure:
    """Plot population size over committed steps."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[item.step_index for item in history],
            y=[item.population_size for item in history],
            mode="lines+markers",
            name="Population",
        )
    )
    return _finish_timeseries(figure, title="Population size", y_title="organisms")


def environment_figure(history: tuple[PopulationObservation, ...]) -> go.Figure:
    """Plot environmental resources and carcass count over time."""
    figure = go.Figure()
    steps = [item.step_index for item in history]
    figure.add_trace(
        go.Scatter(
            x=steps,
            y=[item.total_resources for item in history],
            mode="lines",
            name="Resource units",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=steps,
            y=[item.carcass_count for item in history],
            mode="lines",
            name="Carcasses",
        )
    )
    return _finish_timeseries(
        figure,
        title="Resources and carcasses",
        y_title="count / resource units",
    )


def organism_summary_figure(history: tuple[PopulationObservation, ...]) -> go.Figure:
    """Plot mean age, energy, and body mass for active organisms."""
    figure = go.Figure()
    metrics = (
        ("Mean age", [item.age.mean for item in history]),
        ("Mean energy", [item.energy.mean for item in history]),
        ("Mean body mass", [item.body_mass.mean for item in history]),
    )
    steps = [item.step_index for item in history]
    for name, values in metrics:
        figure.add_trace(go.Scatter(x=steps, y=values, mode="lines", name=name))
    return _finish_timeseries(
        figure,
        title="Active-organism state",
        y_title="mean value",
    )


def mating_type_figure(history: tuple[PopulationObservation, ...]) -> go.Figure:
    """Plot active mating-type counts through time."""
    names = sorted(
        {
            name
            for observation in history
            for name, _ in observation.mating_type_counts.value_counts
        }
    )
    figure = go.Figure()
    steps = [item.step_index for item in history]
    for name in names:
        figure.add_trace(
            go.Scatter(
                x=steps,
                y=[item.mating_type_counts.count_for(name) for item in history],
                mode="lines",
                name=name,
            )
        )
    if not names:
        return _empty_figure("No active mating types were observed.")
    return _finish_timeseries(
        figure,
        title="Mating-type composition",
        y_title="organisms",
    )


def trait_mean_figure(
    history: tuple[PopulationObservation, ...],
    *,
    trait_name: str,
) -> go.Figure:
    """Plot one selected expressed heritable-trait mean through time."""
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[item.step_index for item in history],
            y=[item.trait(trait_name).summary.mean for item in history],
            mode="lines+markers",
            name=trait_name,
        )
    )
    return _finish_timeseries(
        figure,
        title=f"Heritable trait trajectory — {trait_name}",
        y_title="population mean",
    )


def trait_distribution_figure(
    history: tuple[PopulationObservation, ...],
    *,
    trait_name: str,
) -> go.Figure:
    """Plot the final recorded value distribution for one selected trait."""
    if not history:
        return _empty_figure("No population observations were recorded.")
    distribution = history[-1].trait(trait_name).value_counts
    figure = go.Figure(
        data=[
            go.Bar(
                x=[value for value, _ in distribution],
                y=[count for _, count in distribution],
                name=trait_name,
            )
        ]
    )
    figure.update_layout(
        title=f"Final trait distribution — {trait_name}",
        xaxis_title="trait value",
        yaxis_title="organisms",
        margin={"l": 45, "r": 20, "t": 55, "b": 45},
    )
    return figure


def allele_frequency_figure(
    history: tuple[GeneticCompositionObservation, ...],
    *,
    locus_name: str,
) -> go.Figure:
    """Plot raw allele frequencies for one locus over time."""
    allele_values = _allele_values(history, locus_name=locus_name)
    if not allele_values:
        return _empty_figure(f"No alleles were observed at {locus_name}.")

    figure = go.Figure()
    for value in allele_values:
        figure.add_trace(
            go.Scatter(
                x=[item.step_index for item in history],
                y=[item.locus(locus_name).allele_frequency(value) for item in history],
                mode="lines",
                name=repr(value),
            )
        )
    figure.update_yaxes(range=[0.0, 1.0])
    return _finish_timeseries(
        figure,
        title=f"Allele frequencies — {locus_name}",
        y_title="frequency",
    )


def genotype_frequency_figure(
    history: tuple[GeneticCompositionObservation, ...],
    *,
    locus_name: str,
) -> go.Figure:
    """Plot the final observed genotype composition for one locus."""
    if not history:
        return _empty_figure("No genetic observations were recorded.")
    composition = history[-1].locus(locus_name)
    if not composition.genotypes:
        return _empty_figure(f"No active genotypes remain at {locus_name}.")
    labels = [
        " / ".join(repr(value) for value in item.allele_values)
        for item in composition.genotypes
    ]
    figure = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=[item.frequency for item in composition.genotypes],
                name="Genotype frequency",
            )
        ]
    )
    figure.update_layout(
        title=f"Final genotype frequencies — {locus_name}",
        xaxis_title="unphased genotype",
        yaxis_title="frequency",
        yaxis={"range": [0.0, 1.0]},
        margin={"l": 45, "r": 20, "t": 55, "b": 65},
    )
    return figure


def event_activity_figure(steps: tuple[StepTelemetry, ...]) -> go.Figure:
    """Plot committed event activity by producing process through time."""
    process_names = sorted(
        {event.process_name for step in steps for event in step.events}
    )
    if not process_names:
        return _empty_figure("No committed events were recorded.")

    counts_by_process: dict[str, dict[int, int]] = defaultdict(dict)
    for step in steps:
        counts = Counter(event.process_name for event in step.events)
        for process_name in process_names:
            counts_by_process[process_name][step.completed_step_index] = counts[
                process_name
            ]

    figure = go.Figure()
    completed_steps = [step.completed_step_index for step in steps]
    for process_name in process_names:
        figure.add_trace(
            go.Scatter(
                x=completed_steps,
                y=[counts_by_process[process_name][step] for step in completed_steps],
                mode="lines",
                name=process_name,
            )
        )
    return _finish_timeseries(
        figure,
        title="Committed event activity",
        y_title="events",
    )


def mortality_figure(histories: tuple[IndividualLifeHistory, ...]) -> go.Figure:
    """Plot recorded biological deaths by cause."""
    counts = Counter(
        history.death_cause for history in histories if history.death_cause is not None
    )
    if not counts:
        return _empty_figure("No biological deaths were recorded.")
    names = sorted(counts)
    figure = go.Figure(data=[go.Bar(x=names, y=[counts[name] for name in names])])
    figure.update_layout(
        title="Mortality causes",
        xaxis_title="process",
        yaxis_title="deaths",
        margin={"l": 45, "r": 20, "t": 55, "b": 65},
    )
    return figure


def reproductive_success_figure(
    histories: tuple[IndividualLifeHistory, ...],
) -> go.Figure:
    """Plot realized direct reproductive success across observed organisms."""
    counts = Counter(history.realized_reproductive_success for history in histories)
    if not counts:
        return _empty_figure("No life histories were recorded.")
    offspring_counts = sorted(counts)
    figure = go.Figure(
        data=[
            go.Bar(
                x=offspring_counts,
                y=[counts[value] for value in offspring_counts],
            )
        ]
    )
    figure.update_layout(
        title="Realized reproductive success",
        xaxis_title="observed offspring",
        yaxis_title="organisms",
        margin={"l": 45, "r": 20, "t": 55, "b": 45},
    )
    return figure


def experiment_population_figure(result: ReferenceExperimentResult) -> go.Figure:
    """Compare population trajectories across reference experiment seeds."""
    figure = go.Figure()
    for replicate in result.replicates:
        figure.add_trace(
            go.Scatter(
                x=[item.step_index for item in replicate.population_history],
                y=[item.population_size for item in replicate.population_history],
                mode="lines",
                name=f"seed {replicate.seed}",
            )
        )
    return _finish_timeseries(
        figure,
        title="Replicate population trajectories",
        y_title="organisms",
    )


def experiment_outcomes_figure(result: ReferenceExperimentResult) -> go.Figure:
    """Compare final population and resource outcomes across seeds."""
    labels = [str(replicate.seed) for replicate in result.replicates]
    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=labels,
            y=[replicate.final_population_size for replicate in result.replicates],
            name="Final population",
        )
    )
    figure.add_trace(
        go.Bar(
            x=labels,
            y=[replicate.final_total_resources for replicate in result.replicates],
            name="Final resources",
        )
    )
    figure.update_layout(
        barmode="group",
        title="Final replicate outcomes",
        xaxis_title="seed",
        yaxis_title="count / resource units",
        margin={"l": 45, "r": 20, "t": 55, "b": 45},
    )
    return figure


def experiment_summary_rows(
    result: ReferenceExperimentResult,
) -> tuple[dict[str, int], ...]:
    """Return compact table rows for experiment replicate outcomes."""
    return tuple(
        {
            "seed": replicate.seed,
            "steps": replicate.metadata.completed_steps,
            "final_population": replicate.final_population_size,
            "final_resources": replicate.final_total_resources,
            "carcasses": replicate.final_carcass_count,
            "births": replicate.total_births,
            "deaths": replicate.total_deaths,
        }
        for replicate in result.replicates
    )


def top_reproductive_success_rows(
    histories: tuple[IndividualLifeHistory, ...],
    *,
    limit: int = 10,
) -> tuple[dict[str, object], ...]:
    """Return the highest observed reproductive-success life histories."""
    ranked = sorted(
        histories,
        key=lambda history: (
            -history.realized_reproductive_success,
            history.organism_id,
        ),
    )
    return tuple(
        {
            "organism_id": history.organism_id,
            "founder": history.is_founder,
            "offspring": history.realized_reproductive_success,
            "alive": history.is_alive,
            "death_cause": history.death_cause,
            "lifespan_steps": history.lifespan_steps,
        }
        for history in ranked[:limit]
    )


def _spatial_traces(
    frame: SpatialObservation,
) -> tuple[go.Scatter, go.Scatter, go.Scatter]:
    organisms = go.Scatter(
        x=[item.x for item in frame.organisms],
        y=[item.y for item in frame.organisms],
        mode="markers",
        name="Organisms",
        marker={
            "size": [max(10, min(26, 8 + item.body_mass)) for item in frame.organisms],
            "symbol": "circle",
            "line": {"width": 1},
        },
        customdata=[
            [item.organism_id, item.age, item.energy, item.body_mass, item.mating_type]
            for item in frame.organisms
        ],
        hovertemplate=(
            "Organism %{customdata[0]}<br>"
            "position=(%{x}, %{y})<br>"
            "age=%{customdata[1]}<br>"
            "energy=%{customdata[2]}<br>"
            "body mass=%{customdata[3]}<br>"
            "mating type=%{customdata[4]}<extra></extra>"
        ),
    )
    resources = go.Scatter(
        x=[item.x for item in frame.resources],
        y=[item.y for item in frame.resources],
        mode="markers",
        name="Resources",
        marker={
            "size": [max(8, min(30, 6 + item.amount)) for item in frame.resources],
            "symbol": "square",
        },
        customdata=[[item.amount] for item in frame.resources],
        hovertemplate=(
            "Resource deposit<br>position=(%{x}, %{y})<br>"
            "units=%{customdata[0]}<extra></extra>"
        ),
    )
    carcasses = go.Scatter(
        x=[item.x for item in frame.carcasses],
        y=[item.y for item in frame.carcasses],
        mode="markers",
        name="Carcasses",
        marker={"size": 12, "symbol": "x"},
        customdata=[[item.carcass_id, item.resource_units] for item in frame.carcasses],
        hovertemplate=(
            "Carcass %{customdata[0]}<br>position=(%{x}, %{y})<br>"
            "resource units=%{customdata[1]}<extra></extra>"
        ),
    )
    return organisms, resources, carcasses


def _allele_values(
    history: Iterable[GeneticCompositionObservation],
    *,
    locus_name: str,
) -> tuple[object, ...]:
    values: list[object] = []
    for observation in history:
        for allele in observation.locus(locus_name).alleles:
            if not any(allele.value == existing for existing in values):
                values.append(allele.value)
    return tuple(sorted(values, key=repr))


def _finish_timeseries(
    figure: go.Figure,
    *,
    title: str,
    y_title: str,
) -> go.Figure:
    figure.update_layout(
        title=title,
        xaxis_title="committed step",
        yaxis_title=y_title,
        hovermode="x unified",
        margin={"l": 45, "r": 20, "t": 55, "b": 45},
    )
    return figure


def _empty_figure(message: str) -> go.Figure:
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    figure.update_layout(margin={"l": 20, "r": 20, "t": 20, "b": 20})
    return figure
