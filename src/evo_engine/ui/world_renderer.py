"""Render interactive world primitives from UI-only presentation values."""

from __future__ import annotations

import plotly.graph_objects as go

from evo_engine.ui.world_presentation import WorldPresentationFrame

_NEUTRAL_ORGANISM_COLOR = "#64748B"
_RESOURCE_COLOR = "#2E8B57"
_CARCASS_COLOR = "#8C564B"
_TRAIL_COLOR = "rgba(100, 116, 139, 0.55)"
_DEFAULT_OUTLINE_COLOR = "#475569"
_SELECTED_OUTLINE_COLOR = "#111827"
_FOCAL_COLOR_SCALE = "Cividis"


def world_presentation_figure(
    frame: WorldPresentationFrame,
    *,
    show_labels: bool = False,
) -> go.Figure:
    """Render one selected committed world presentation frame."""
    figure = go.Figure()
    _add_trails(figure, frame)
    _add_resources(figure, frame)
    _add_carcasses(figure, frame)
    _add_organisms(figure, frame, show_labels=show_labels)
    figure.update_layout(
        title=f"Committed world · step {frame.committed_step_index}",
        xaxis={
            "title": "x",
            "range": [-0.5, frame.world_width - 0.5],
            "dtick": 1,
            "fixedrange": True,
        },
        yaxis={
            "title": "y",
            "range": [frame.world_height - 0.5, -0.5],
            "dtick": 1,
            "fixedrange": True,
            "scaleanchor": "x",
            "scaleratio": 1,
        },
        height=max(500, min(760, frame.world_height * 42)),
        margin={"l": 35, "r": 20, "t": 55, "b": 35},
        legend={"orientation": "h", "y": 1.08},
        hovermode="closest",
    )
    return figure


def _add_trails(figure: go.Figure, frame: WorldPresentationFrame) -> None:
    first = True
    for trail in frame.trails:
        figure.add_trace(
            go.Scatter(
                x=[point[0] for point in trail.points],
                y=[point[1] for point in trail.points],
                mode="lines",
                name="Recent movement",
                legendgroup="movement-trails",
                showlegend=first,
                hoverinfo="skip",
                line={"width": 2, "dash": "dot", "color": _TRAIL_COLOR},
            )
        )
        first = False


def _add_resources(figure: go.Figure, frame: WorldPresentationFrame) -> None:
    if not frame.resources:
        return
    figure.add_trace(
        go.Scatter(
            x=[item.x for item in frame.resources],
            y=[item.y for item in frame.resources],
            mode="markers",
            name="Resources",
            marker={
                "size": [max(8, min(30, 6 + item.amount)) for item in frame.resources],
                "symbol": "square",
                "color": _RESOURCE_COLOR,
            },
            customdata=[[item.amount] for item in frame.resources],
            hovertemplate=(
                "Resource deposit<br>position=(%{x}, %{y})<br>"
                "units=%{customdata[0]}<extra></extra>"
            ),
        )
    )


def _add_carcasses(figure: go.Figure, frame: WorldPresentationFrame) -> None:
    if not frame.carcasses:
        return
    figure.add_trace(
        go.Scatter(
            x=[item.x for item in frame.carcasses],
            y=[item.y for item in frame.carcasses],
            mode="markers",
            name="Carcasses",
            marker={"size": 12, "symbol": "x", "color": _CARCASS_COLOR},
            customdata=[
                [item.carcass_id, item.resource_units] for item in frame.carcasses
            ],
            hovertemplate=(
                "Carcass %{customdata[0]}<br>position=(%{x}, %{y})<br>"
                "resource units=%{customdata[1]}<extra></extra>"
            ),
        )
    )


def _add_organisms(
    figure: go.Figure,
    frame: WorldPresentationFrame,
    *,
    show_labels: bool,
) -> None:
    mode = "markers+text" if show_labels else "markers"
    marker = _organism_marker(frame)
    figure.add_trace(
        go.Scatter(
            x=[item.x for item in frame.organisms],
            y=[item.y for item in frame.organisms],
            mode=mode,
            name="Organisms",
            text=[str(item.organism_id) for item in frame.organisms]
            if show_labels
            else None,
            textposition="top center",
            marker=marker,
            customdata=[
                [
                    item.organism_id,
                    item.age,
                    item.energy,
                    item.body_mass,
                    item.mating_type,
                    item.selected,
                    item.focal_trait_value,
                ]
                for item in frame.organisms
            ],
            hovertemplate=_organism_hover_template(frame),
        )
    )


def _organism_marker(frame: WorldPresentationFrame) -> dict[str, object]:
    marker: dict[str, object] = {
        "size": [item.marker_size for item in frame.organisms],
        "symbol": "circle",
        "line": {
            "width": [4 if item.selected else 1 for item in frame.organisms],
            "color": [
                _SELECTED_OUTLINE_COLOR if item.selected else _DEFAULT_OUTLINE_COLOR
                for item in frame.organisms
            ],
        },
    }
    if frame.focal_encoding is None:
        marker["color"] = _NEUTRAL_ORGANISM_COLOR
        return marker

    normalized = tuple(item.focal_trait_normalized for item in frame.organisms)
    if any(value is None for value in normalized):
        raise ValueError(
            "science-aware organism rendering requires a normalized focal value "
            "for every displayed organism."
        )
    encoding = frame.focal_encoding
    marker.update(
        {
            "color": normalized,
            "colorscale": _FOCAL_COLOR_SCALE,
            "cmin": 0.0,
            "cmax": 1.0,
            "showscale": True,
            "colorbar": {
                "title": {"text": encoding.label},
                "tickmode": "array",
                "tickvals": [0.0, 1.0],
                "ticktext": [
                    str(encoding.lower_bound),
                    str(encoding.upper_bound),
                ],
            },
        }
    )
    return marker


def _organism_hover_template(frame: WorldPresentationFrame) -> str:
    base = (
        "Organism %{customdata[0]}<br>position=(%{x}, %{y})<br>"
        "age=%{customdata[1]}<br>energy=%{customdata[2]}<br>"
        "body mass=%{customdata[3]}<br>mating type=%{customdata[4]}"
    )
    if frame.focal_encoding is None:
        return base + "<extra></extra>"
    return (
        base
        + f"<br>{frame.focal_encoding.label}=%{{customdata[6]}}"
        + "<extra></extra>"
    )
