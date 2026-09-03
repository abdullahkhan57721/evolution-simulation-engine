"""Tests for Plotly figures built from committed dashboard records."""

from __future__ import annotations

from evo_engine.observation import (
    SpatialObservation,
    SpatialOrganismSnapshot,
    SpatialResourceSnapshot,
)
from evo_engine.ui.charts import (
    allele_frequency_figure,
    environment_figure,
    event_activity_figure,
    genotype_frequency_figure,
    population_size_figure,
    spatial_world_figure,
    trait_mean_figure,
)
from evo_engine.ui.models import build_curated_config, run_dashboard_reference


def test_spatial_world_figure_uses_fixed_bounds_frames_and_hover_state() -> None:
    """Test the spatial animation is driven only by immutable spatial frames."""
    history = (
        SpatialObservation(
            step_index=0,
            world_width=4,
            world_height=3,
            organisms=(
                SpatialOrganismSnapshot(
                    organism_id=0,
                    x=1,
                    y=2,
                    age=0,
                    energy=30,
                    body_mass=2,
                    mating_type="type_a",
                ),
            ),
            resources=(SpatialResourceSnapshot(x=2, y=1, amount=5),),
        ),
        SpatialObservation(step_index=1, world_width=4, world_height=3),
    )

    figure = spatial_world_figure(history)
    figure_json = figure.to_plotly_json()
    frames = figure_json["frames"]

    assert len(frames) == 2
    assert frames[0]["name"] == "0"
    assert frames[1]["name"] == "1"
    assert tuple(figure.layout.xaxis.range) == (-0.5, 3.5)
    assert tuple(figure.layout.yaxis.range) == (2.5, -0.5)
    assert "energy=%{customdata[2]}" in figure.data[0].hovertemplate
    assert len(figure.data) == 3
    assert len(frames[1]["data"][0]["x"]) == 0


def test_empty_spatial_history_builds_a_valid_placeholder_figure() -> None:
    """Test an absent spatial history does not make Plotly rendering fail."""
    figure = spatial_world_figure(())

    assert len(figure.data) == 0
    assert len(figure.layout.annotations) == 1
    assert "No spatial observations" in figure.layout.annotations[0].text


def test_dashboard_figures_consume_real_small_reference_result() -> None:
    """Test core analytics figures accept a completed reference run."""
    result = run_dashboard_reference(
        build_curated_config(
            seed=31,
            max_steps=2,
            initial_population=4,
            width=4,
            height=4,
            resource_deposits_per_step=2,
        )
    )
    trait_name = result.population_history[0].traits[0].trait_name
    locus_name = result.genetic_history[0].loci[0].locus_name

    population = population_size_figure(result.population_history)
    environment = environment_figure(result.population_history)
    trait = trait_mean_figure(result.population_history, trait_name=trait_name)
    allele = allele_frequency_figure(result.genetic_history, locus_name=locus_name)
    genotype = genotype_frequency_figure(result.genetic_history, locus_name=locus_name)
    events = event_activity_figure(result.telemetry_steps)

    assert len(population.data[0].x) == 3
    assert len(environment.data) == 2
    assert len(trait.data[0].x) == 3
    assert len(allele.data) >= 1
    assert genotype.layout.title.text.startswith("Final genotype frequencies")
    assert events.layout.title.text in {
        "Committed event activity",
        None,
    }
