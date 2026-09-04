"""Tests for the concrete Plotly consumer of interactive world primitives."""

from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.ui.world_presentation import (
    CarcassPrimitive,
    MovementTrail,
    OrganismPrimitive,
    ResourcePrimitive,
    WorldPresentationFrame,
)
from evo_engine.ui.world_renderer import world_presentation_figure


def test_world_figure_renders_selected_outline_layers_and_fixed_bounds() -> None:
    """Test Plotly consumes prepared primitives without deciding scientific state."""
    frame = WorldPresentationFrame(
        committed_step_index=4,
        world_width=8,
        world_height=6,
        organisms=(
            OrganismPrimitive(
                organism_id=1,
                x=2.0,
                y=3.0,
                age=5,
                energy=17,
                body_mass=4,
                mating_type="type_a",
                marker_size=12,
                selected=False,
            ),
            OrganismPrimitive(
                organism_id=2,
                x=4.0,
                y=1.0,
                age=3,
                energy=22,
                body_mass=6,
                mating_type="type_b",
                marker_size=14,
                selected=True,
            ),
        ),
        resources=(ResourcePrimitive(x=1, y=1, amount=8),),
        carcasses=(CarcassPrimitive(carcass_id=9, x=5, y=2, resource_units=3),),
        trails=(MovementTrail(organism_id=2, points=((2, 2), (3, 2), (4, 1))),),
        selected_organism_id=2,
    )

    rendered = world_presentation_figure(frame).to_plotly_json()

    assert rendered["layout"]["title"]["text"] == "Committed world · step 4"
    assert tuple(rendered["layout"]["xaxis"]["range"]) == (-0.5, 7.5)
    assert tuple(rendered["layout"]["yaxis"]["range"]) == (5.5, -0.5)
    names = [trace["name"] for trace in rendered["data"]]
    assert names == ["Recent movement", "Resources", "Carcasses", "Organisms"]

    trail_trace, resource_trace, carcass_trace, organism_trace = rendered["data"]
    assert trail_trace["line"]["color"] == "rgba(100, 116, 139, 0.55)"
    assert resource_trace["marker"]["color"] == "#2E8B57"
    assert carcass_trace["marker"]["color"] == "#8C564B"
    assert organism_trace["marker"]["color"] == "#64748B"
    assert organism_trace["marker"]["size"] == [12, 14]
    assert organism_trace["marker"]["line"]["width"] == [1, 4]
    assert organism_trace["marker"]["line"]["color"] == ["#475569", "#111827"]
    assert organism_trace["customdata"][1][0] == 2
    assert organism_trace["customdata"][1][5] is True


def test_science_aware_figure_uses_fixed_scale_legend_and_text_value() -> None:
    """Test focal fill has one fixed scientific meaning independent of selection."""
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=4,
    )
    frame = WorldPresentationFrame(
        committed_step_index=3,
        world_width=5,
        world_height=5,
        organisms=(
            OrganismPrimitive(
                organism_id=1,
                x=1.0,
                y=1.0,
                age=2,
                energy=15,
                body_mass=3,
                mating_type="type_a",
                marker_size=11,
                focal_trait_value=1,
                focal_trait_normalized=0.0,
            ),
            OrganismPrimitive(
                organism_id=2,
                x=3.0,
                y=3.0,
                age=2,
                energy=15,
                body_mass=3,
                mating_type="type_b",
                marker_size=11,
                selected=True,
                focal_trait_value=4,
                focal_trait_normalized=1.0,
            ),
        ),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=2,
        focal_encoding=encoding,
    )

    rendered = world_presentation_figure(frame).to_plotly_json()
    organism_trace = rendered["data"][0]
    marker = organism_trace["marker"]

    assert marker["color"] == [0.0, 1.0]
    assert marker["colorscale"]
    assert marker["cmin"] == 0.0
    assert marker["cmax"] == 1.0
    assert marker["showscale"] is True
    assert marker["colorbar"]["title"]["text"] == "Maximum speed"
    assert marker["colorbar"]["tickvals"] == [0.0, 1.0]
    assert marker["colorbar"]["ticktext"] == ["1", "4"]
    assert marker["line"]["width"] == [1, 4]
    assert marker["line"]["color"] == ["#475569", "#111827"]
    assert organism_trace["customdata"][0][6] == 1
    assert organism_trace["customdata"][1][6] == 4
    assert "Maximum speed=%{customdata[6]}" in organism_trace["hovertemplate"]


def test_focal_colors_are_stable_when_optional_layers_are_absent() -> None:
    """Test environmental layer toggles cannot alter focal scientific mapping."""
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=4,
    )
    frame = WorldPresentationFrame(
        committed_step_index=2,
        world_width=4,
        world_height=4,
        organisms=(
            OrganismPrimitive(
                organism_id=3,
                x=1.0,
                y=2.0,
                age=2,
                energy=10,
                body_mass=3,
                mating_type="type_a",
                marker_size=11,
                selected=True,
                focal_trait_value=2,
                focal_trait_normalized=1 / 3,
            ),
        ),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=3,
        focal_encoding=encoding,
    )

    rendered = world_presentation_figure(frame).to_plotly_json()
    organism_trace = rendered["data"][0]

    assert organism_trace["name"] == "Organisms"
    assert organism_trace["marker"]["color"] == [1 / 3]
    assert organism_trace["marker"]["cmin"] == 0.0
    assert organism_trace["marker"]["cmax"] == 1.0
    assert organism_trace["marker"]["line"]["width"] == [4]
    assert organism_trace["marker"]["line"]["color"] == ["#111827"]


def test_organism_color_is_stable_when_optional_layers_are_absent() -> None:
    """Test view-layer toggles cannot change generic organism color meaning."""
    frame = WorldPresentationFrame(
        committed_step_index=2,
        world_width=4,
        world_height=4,
        organisms=(
            OrganismPrimitive(
                organism_id=3,
                x=1.0,
                y=2.0,
                age=2,
                energy=10,
                body_mass=3,
                mating_type="type_a",
                marker_size=11,
                selected=True,
            ),
        ),
        resources=(),
        carcasses=(),
        trails=(),
        selected_organism_id=3,
    )

    rendered = world_presentation_figure(frame).to_plotly_json()
    organism_trace = rendered["data"][0]

    assert organism_trace["name"] == "Organisms"
    assert organism_trace["marker"]["color"] == "#64748B"
    assert organism_trace["marker"]["line"]["width"] == [4]
    assert organism_trace["marker"]["line"]["color"] == ["#111827"]


def test_world_figure_handles_extinct_frame_with_environment() -> None:
    """Test an empty active population does not erase authoritative environment."""
    frame = WorldPresentationFrame(
        committed_step_index=7,
        world_width=5,
        world_height=5,
        organisms=(),
        resources=(ResourcePrimitive(x=2, y=2, amount=11),),
        carcasses=(),
        trails=(),
    )

    rendered = world_presentation_figure(frame).to_plotly_json()

    assert [trace["name"] for trace in rendered["data"]] == [
        "Resources",
        "Organisms",
    ]
    assert rendered["data"][0]["marker"]["color"] == "#2E8B57"
    assert rendered["data"][-1]["marker"]["color"] == "#64748B"
    assert len(rendered["data"][-1]["x"]) == 0
