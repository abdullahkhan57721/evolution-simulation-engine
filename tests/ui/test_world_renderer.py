"""Tests for the concrete Plotly consumer of interactive world primitives."""

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
