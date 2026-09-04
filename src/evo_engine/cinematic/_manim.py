# pyright: reportMissingImports=false
"""Manim implementation for the optional science-aware cinematic renderer."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from manim import (
    BLUE_C,
    DOWN,
    GREY_B,
    LEFT,
    RED_C,
    RIGHT,
    TEAL_C,
    UP,
    WHITE,
    Axes,
    Circle,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    Rectangle,
    RoundedRectangle,
    Scene,
    Square,
    Text,
    Transform,
    VGroup,
    interpolate_color,
    linear,
    tempconfig,
)

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.primitives import CinematicOrganismPrimitive
from evo_engine.cinematic.timeline import (
    PortfolioAnimationFrame,
    PortfolioAnimationTimeline,
)
from evo_engine.observation import (
    SpatialCarcassSnapshot,
    SpatialResourceSnapshot,
)

_BACKGROUND = "#0B1020"
_PANEL = "#151D2E"
_MUTED = "#93A4BC"
_RESOURCE = "#F0C75E"
_TEXT = "#EEF4FF"
_QUALITY_SETTINGS: dict[AnimationQuality, tuple[int, int, int]] = {
    "low": (854, 480, 15),
    "medium": (1280, 720, 30),
    "high": (1920, 1080, 60),
}


@dataclass(frozen=True, slots=True)
class _WorldLayout:
    width: int
    height: int
    display_width: float
    display_height: float
    center_x: float = -3.25
    center_y: float = -0.20

    @classmethod
    def from_bounds(cls, width: int, height: int) -> _WorldLayout:
        """Return a stable world layout for authoritative world dimensions."""
        scale = min(6.1 / width, 5.45 / height)
        return cls(
            width=width,
            height=height,
            display_width=width * scale,
            display_height=height * scale,
        )

    def point(self, x: int, y: int) -> list[float]:
        """Map one committed grid coordinate onto the cinematic world surface."""
        left = self.center_x - self.display_width / 2
        bottom = self.center_y - self.display_height / 2
        return [
            left + (x + 0.5) * self.display_width / self.width,
            bottom + (y + 0.5) * self.display_height / self.height,
            0.0,
        ]


@dataclass(slots=True)
class _WorldSceneState:
    layout: _WorldLayout
    shell: object
    resources: object
    carcasses: object
    organisms: dict[int, object]
    status_group: object
    step_text: object
    population_text: object
    trait_text: object
    evidence_text: object


class _PortfolioScene(Scene):
    """Render committed evidence without retaining or driving a simulation."""

    def __init__(self, timeline: PortfolioAnimationTimeline, **kwargs: object) -> None:
        self._timeline = timeline
        super().__init__(**kwargs)

    def construct(self) -> None:
        """Build the generic cinematic sequence from immutable committed values."""
        self.camera.background_color = _BACKGROUND
        self._show_intro()
        if not self._timeline.frames:
            self._show_empty_timeline()
            return
        state = self._show_initial_world()
        self._animate_remaining_world(state)
        self._show_evidence(state)
        self._show_outcome()

    def _show_intro(self) -> None:
        title = Text(
            "Evolution Simulation Engine",
            font_size=48,
            weight="BOLD",
            color=_TEXT,
        )
        subtitle = Text(
            "Cinematic replay from committed scientific evidence",
            font_size=23,
            color=_MUTED,
        ).next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(title, shift=UP * 0.2), FadeIn(subtitle), run_time=0.6)
        self.wait(0.35)
        self.play(FadeOut(title), FadeOut(subtitle), run_time=0.35)

    def _show_empty_timeline(self) -> None:
        message = Text(
            "No committed frames were recorded.",
            font_size=34,
            color=_TEXT,
        )
        self.play(FadeIn(message), run_time=0.4)
        self.wait(0.6)

    def _show_initial_world(self) -> _WorldSceneState:
        frame = self._timeline.frames[0]
        layout = _WorldLayout.from_bounds(
            frame.spatial.world_width,
            frame.spatial.world_height,
        )
        shell = _world_shell(layout)
        resources = _resource_layer(frame, layout)
        carcasses = _carcass_layer(frame, layout)
        organisms = _organism_layer(frame, layout)
        status = _status_group(self._timeline, frame)
        state = _WorldSceneState(
            layout=layout,
            shell=shell,
            resources=resources,
            carcasses=carcasses,
            organisms=organisms,
            status_group=status[0],
            step_text=status[1],
            population_text=status[2],
            trait_text=status[3],
            evidence_text=status[4],
        )
        self.play(
            FadeIn(shell),
            FadeIn(resources),
            FadeIn(carcasses),
            *[FadeIn(item, scale=0.7) for item in organisms.values()],
            FadeIn(state.status_group),
            run_time=0.6,
        )
        return state

    def _animate_remaining_world(self, state: _WorldSceneState) -> None:
        for frame in self._timeline.frames[1:]:
            self.play(
                *_frame_animations(state, frame, self._timeline),
                run_time=0.22,
                rate_func=linear,
            )
        self.wait(0.25)

    def _show_evidence(self, state: _WorldSceneState) -> None:
        world_mobjects = [
            state.shell,
            state.resources,
            state.carcasses,
            *state.organisms.values(),
            state.status_group,
        ]
        self.play(*[FadeOut(item) for item in world_mobjects], run_time=0.4)
        heading = Text(
            "Population-level evidence",
            font_size=36,
            weight="BOLD",
            color=_TEXT,
        )
        heading.to_edge(UP, buff=0.35)
        population_chart = _population_chart(self._timeline)
        trait_chart = _trait_chart(self._timeline)
        charts = VGroup(population_chart, trait_chart).arrange(RIGHT, buff=0.7)
        charts.shift(DOWN * 0.25)
        self.play(FadeIn(heading), FadeIn(charts, shift=UP * 0.15), run_time=0.6)
        self.wait(0.75)
        self.play(FadeOut(heading), FadeOut(charts), run_time=0.35)

    def _show_outcome(self) -> None:
        initial = self._timeline.frames[0]
        final = self._timeline.frames[-1]
        heading = Text("Committed outcome", font_size=38, weight="BOLD", color=_TEXT)
        population = Text(
            f"Population: {initial.population.population_size} → "
            f"{final.population.population_size}",
            font_size=30,
            color=WHITE,
        )
        trait = Text(
            _trait_outcome_text(self._timeline, initial, final),
            font_size=26,
            color=_MUTED,
        )
        steps = Text(
            f"Completed step: {final.step_index}",
            font_size=23,
            color=_MUTED,
        )
        summary = VGroup(heading, population, trait, steps).arrange(DOWN, buff=0.34)
        self.play(FadeIn(summary, shift=UP * 0.15), run_time=0.55)
        self.wait(1.0)


def render_timeline_with_manim(
    timeline: PortfolioAnimationTimeline,
    output_path: Path,
    *,
    quality: AnimationQuality,
) -> Path:
    """Render ``timeline`` through Manim and copy finished media to destination."""
    width, height, frame_rate = _QUALITY_SETTINGS[quality]
    output_format = output_path.suffix.lower().removeprefix(".")
    with TemporaryDirectory(prefix="evo-engine-manim-") as temporary_directory:
        settings = {
            "media_dir": temporary_directory,
            "output_file": output_path.stem,
            "format": output_format,
            "pixel_width": width,
            "pixel_height": height,
            "frame_rate": frame_rate,
            "write_to_movie": True,
            "preview": False,
            "disable_caching": True,
            "verbosity": "WARNING",
        }
        with tempconfig(settings):
            scene = _PortfolioScene(timeline)
            scene.render()
            rendered_path = _rendered_media_path(scene, output_format)
            if not rendered_path.exists():
                raise RuntimeError(
                    f"Manim did not produce expected media: {rendered_path}"
                )
            shutil.copy2(rendered_path, output_path)
    return output_path


def _rendered_media_path(scene: Any, output_format: str) -> Path:
    writer = scene.renderer.file_writer
    if output_format == "gif":
        return Path(writer.gif_file_path)
    return Path(writer.movie_file_path)


def _world_shell(layout: _WorldLayout) -> object:
    border = RoundedRectangle(
        width=layout.display_width + 0.18,
        height=layout.display_height + 0.18,
        corner_radius=0.12,
        stroke_color=GREY_B,
        stroke_width=1.6,
        fill_color=_PANEL,
        fill_opacity=0.55,
    ).move_to([layout.center_x, layout.center_y, 0])
    grid = VGroup(*_grid_lines(layout))
    label = Text("Recorded ecological world", font_size=20, color=_MUTED)
    label.next_to(border, UP, buff=0.18)
    return VGroup(border, grid, label)


def _grid_lines(layout: _WorldLayout) -> list[object]:
    lines: list[object] = []
    left = layout.center_x - layout.display_width / 2
    right = layout.center_x + layout.display_width / 2
    bottom = layout.center_y - layout.display_height / 2
    top = layout.center_y + layout.display_height / 2
    for x in range(1, layout.width):
        scene_x = left + x * layout.display_width / layout.width
        lines.append(
            Line(
                [scene_x, bottom, 0],
                [scene_x, top, 0],
                stroke_color=GREY_B,
                stroke_opacity=0.10,
                stroke_width=0.7,
            )
        )
    for y in range(1, layout.height):
        scene_y = bottom + y * layout.display_height / layout.height
        lines.append(
            Line(
                [left, scene_y, 0],
                [right, scene_y, 0],
                stroke_color=GREY_B,
                stroke_opacity=0.10,
                stroke_width=0.7,
            )
        )
    return lines


def _resource_layer(frame: PortfolioAnimationFrame, layout: _WorldLayout) -> object:
    return VGroup(
        *[_resource_marker(resource, layout) for resource in frame.spatial.resources]
    )


def _resource_marker(resource: SpatialResourceSnapshot, layout: _WorldLayout) -> object:
    side = 0.07 + min(resource.amount, 14) * 0.006
    return Square(
        side_length=side,
        stroke_width=0,
        fill_color=_RESOURCE,
        fill_opacity=0.78,
    ).move_to(layout.point(resource.x, resource.y))


def _carcass_layer(frame: PortfolioAnimationFrame, layout: _WorldLayout) -> object:
    return VGroup(
        *[_carcass_marker(carcass, layout) for carcass in frame.spatial.carcasses]
    )


def _carcass_marker(carcass: SpatialCarcassSnapshot, layout: _WorldLayout) -> object:
    side = 0.09 + min(carcass.resource_units, 12) * 0.004
    return (
        Square(
            side_length=side,
            color=GREY_B,
            fill_opacity=0.32,
            stroke_width=1.0,
        )
        .rotate(0.7853981633974483)
        .move_to(layout.point(carcass.x, carcass.y))
    )


def _organism_layer(
    frame: PortfolioAnimationFrame,
    layout: _WorldLayout,
) -> dict[int, object]:
    return {
        organism.organism_id: _organism_marker(organism, layout)
        for organism in frame.organisms
    }


def _organism_marker(
    organism: CinematicOrganismPrimitive,
    layout: _WorldLayout,
) -> object:
    radius = 0.065 + min(organism.body_mass, 30) * 0.0018
    marker = Circle(
        radius=radius,
        stroke_color=WHITE,
        stroke_width=0.65,
        fill_color=_organism_fill(organism),
        fill_opacity=0.95,
    )
    return marker.move_to(layout.point(organism.x, organism.y))


def _organism_fill(organism: CinematicOrganismPrimitive) -> object:
    if organism.focal_normalized is None:
        return TEAL_C
    return interpolate_color(BLUE_C, RED_C, organism.focal_normalized)


def _status_group(
    timeline: PortfolioAnimationTimeline,
    frame: PortfolioAnimationFrame,
) -> tuple[object, object, object, object, object]:
    title = Text("Committed replay", font_size=30, weight="BOLD", color=_TEXT)
    step = Text(_step_text(frame), font_size=25, color=WHITE)
    population = Text(_population_text(frame), font_size=25, color=WHITE)
    trait = Text(_trait_text(timeline.trait_name, frame), font_size=22, color=_MUTED)
    evidence = Text(_evidence_text(frame), font_size=19, color=_MUTED)
    legend = _focal_legend(timeline)
    group = VGroup(title, step, population, trait, evidence, legend).arrange(
        DOWN,
        aligned_edge=LEFT,
        buff=0.25,
    )
    group.to_edge(RIGHT, buff=0.45).shift(UP * 0.55)
    return group, step, population, trait, evidence


def _focal_legend(timeline: PortfolioAnimationTimeline) -> object:
    encoding = timeline.focal_encoding
    if encoding is None:
        return Text("Organism fill: neutral", font_size=18, color=_MUTED)

    label = Text(
        f"Fill: {encoding.label}",
        font_size=18,
        color=_TEXT,
    )
    low_dot = Dot(radius=0.055, color=BLUE_C)
    low_text = Text(str(encoding.lower_bound), font_size=16, color=_MUTED)
    high_dot = Dot(radius=0.055, color=RED_C)
    high_text = Text(str(encoding.upper_bound), font_size=16, color=_MUTED)
    scale = VGroup(low_dot, low_text, high_dot, high_text).arrange(RIGHT, buff=0.13)
    return VGroup(label, scale).arrange(DOWN, aligned_edge=LEFT, buff=0.12)


def _frame_animations(
    state: _WorldSceneState,
    frame: PortfolioAnimationFrame,
    timeline: PortfolioAnimationTimeline,
) -> list[object]:
    animations = _organism_animations(state, frame)

    previous_resources = state.resources
    next_resources = _resource_layer(frame, state.layout)
    state.resources = next_resources
    animations.extend((FadeOut(previous_resources), FadeIn(next_resources)))

    previous_carcasses = state.carcasses
    next_carcasses = _carcass_layer(frame, state.layout)
    state.carcasses = next_carcasses
    animations.extend((FadeOut(previous_carcasses), FadeIn(next_carcasses)))

    animations.extend(_status_animations(state, frame, timeline.trait_name))
    return animations


def _organism_animations(
    state: _WorldSceneState,
    frame: PortfolioAnimationFrame,
) -> list[object]:
    animations: list[object] = []
    current = {organism.organism_id: organism for organism in frame.organisms}
    for organism_id in frame.departed_organism_ids:
        marker = state.organisms.pop(organism_id, None)
        if marker is not None:
            animations.append(FadeOut(marker, scale=0.55))
    for organism_id, organism in current.items():
        target = _organism_marker(organism, state.layout)
        if organism_id in state.organisms:
            animations.append(Transform(state.organisms[organism_id], target))
        else:
            state.organisms[organism_id] = target
            animations.append(FadeIn(target, scale=0.55))
    return animations


def _status_animations(
    state: _WorldSceneState,
    frame: PortfolioAnimationFrame,
    trait_name: str,
) -> list[object]:
    return [
        Transform(
            state.step_text,
            _replacement_text(state.step_text, _step_text(frame), 25),
        ),
        Transform(
            state.population_text,
            _replacement_text(state.population_text, _population_text(frame), 25),
        ),
        Transform(
            state.trait_text,
            _replacement_text(
                state.trait_text,
                _trait_text(trait_name, frame),
                22,
                _MUTED,
            ),
        ),
        Transform(
            state.evidence_text,
            _replacement_text(
                state.evidence_text,
                _evidence_text(frame),
                19,
                _MUTED,
            ),
        ),
    ]


def _replacement_text(
    old: Any,
    value: str,
    font_size: int,
    color: object = WHITE,
) -> object:
    replacement = Text(value, font_size=font_size, color=color)
    replacement.move_to(old.get_center())
    replacement.align_to(old, LEFT)
    return replacement


def _step_text(frame: PortfolioAnimationFrame) -> str:
    return f"Step  {frame.step_index}"


def _population_text(frame: PortfolioAnimationFrame) -> str:
    return f"Population  {frame.population.population_size}"


def _trait_text(trait_name: str, frame: PortfolioAnimationFrame) -> str:
    value = "—" if frame.trait_mean is None else f"{frame.trait_mean:.2f}"
    return f"Mean {trait_name.replace('_', ' ')}  {value}"


def _evidence_text(frame: PortfolioAnimationFrame) -> str:
    lines: list[str] = []
    if frame.appeared_organism_ids or frame.departed_organism_ids:
        lines.append(
            f"Appeared +{len(frame.appeared_organism_ids)}  "
            f"Departed −{len(frame.departed_organism_ids)}"
        )
    if not frame.applied_events:
        lines.append("Committed events 0")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for event in frame.applied_events:
        counts[event.process_name] = counts.get(event.process_name, 0) + 1
    process_name, count = min(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    lines.append(
        f"Events {len(frame.applied_events)}  "
        f"{_display_process_name(process_name)} ×{count}"
    )
    return "\n".join(lines)


def _display_process_name(process_name: str) -> str:
    characters: list[str] = []
    for index, character in enumerate(process_name):
        if index > 0 and character.isupper():
            characters.append(" ")
        characters.append(character.lower() if index > 0 else character)
    return "".join(characters)


def _population_chart(timeline: PortfolioAnimationTimeline) -> object:
    steps = [frame.step_index for frame in timeline.frames]
    values = [float(frame.population.population_size) for frame in timeline.frames]
    return _line_chart(
        title="Population",
        steps=steps,
        values=values,
        color=BLUE_C,
    )


def _trait_chart(timeline: PortfolioAnimationTimeline) -> object:
    points = [
        (frame.step_index, frame.trait_mean)
        for frame in timeline.frames
        if frame.trait_mean is not None
    ]
    steps = [step for step, _ in points]
    values = [float(value) for _, value in points if value is not None]
    title = f"Mean {timeline.trait_name.replace('_', ' ')}"
    return _line_chart(title=title, steps=steps, values=values, color=TEAL_C)


def _line_chart(
    *,
    title: str,
    steps: list[int],
    values: list[float],
    color: object,
) -> object:
    if not steps:
        return _empty_chart(title)
    axes = _chart_axes(steps, values)
    graph = _chart_graph(axes, steps, values, color)
    label = Text(title, font_size=22, color=_TEXT).next_to(axes, UP, buff=0.2)
    step_label = Text("step", font_size=16, color=_MUTED).next_to(
        axes,
        DOWN,
        buff=0.12,
    )
    return VGroup(axes, graph, label, step_label)


def _chart_axes(steps: list[int], values: list[float]) -> object:
    x_min = min(steps)
    x_max = max(steps)
    if x_min == x_max:
        x_max = x_min + 1
    y_max = max(max(values) * 1.12, 1.0)
    return Axes(
        x_range=[x_min, x_max, max(1, (x_max - x_min) // 4)],
        y_range=[0, y_max, max(y_max / 4, 0.25)],
        x_length=5.35,
        y_length=3.7,
        tips=False,
        axis_config={"stroke_width": 1.1, "color": GREY_B},
    )


def _chart_graph(
    axes: Any,
    steps: list[int],
    values: list[float],
    color: object,
) -> object:
    if len(steps) == 1:
        return Dot(axes.c2p(steps[0], values[0]), radius=0.06, color=color)
    return axes.plot_line_graph(
        x_values=steps,
        y_values=values,
        line_color=color,
        add_vertex_dots=False,
        stroke_width=3,
    )


def _empty_chart(title: str) -> object:
    panel = Rectangle(
        width=5.35,
        height=3.7,
        stroke_color=GREY_B,
        stroke_width=1.0,
        fill_color=_PANEL,
        fill_opacity=0.25,
    )
    label = Text(title, font_size=22, color=_TEXT).next_to(panel, UP, buff=0.2)
    message = Text("No non-empty population values", font_size=18, color=_MUTED)
    message.move_to(panel.get_center())
    return VGroup(panel, label, message)


def _trait_outcome_text(
    timeline: PortfolioAnimationTimeline,
    initial: PortfolioAnimationFrame,
    final: PortfolioAnimationFrame,
) -> str:
    label = timeline.trait_name.replace("_", " ")
    if initial.trait_mean is None or final.trait_mean is None:
        return f"Mean {label}: unavailable after population extinction"
    return f"Mean {label}: {initial.trait_mean:.2f} → {final.trait_mean:.2f}"
