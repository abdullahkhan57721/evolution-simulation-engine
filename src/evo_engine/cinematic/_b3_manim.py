# pyright: reportMissingImports=false
"""Manim choreography for the concrete confirmed B3 flagship cinematic."""

from __future__ import annotations

import math
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from manim import (
    BLUE_C,
    DOWN,
    GREY_B,
    LEFT,
    ORANGE,
    ORIGIN,
    RED_C,
    RIGHT,
    TEAL_C,
    UP,
    WHITE,
    YELLOW_C,
    Axes,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MovingCameraScene,
    RoundedRectangle,
    Square,
    Text,
    Transform,
    VGroup,
    interpolate_color,
    tempconfig,
)

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_director import (
    B3_CONTROL_LABEL,
    B3_REPRESENTATIVE_SEED,
    B3_TREATMENT_LABEL,
    B3DirectorAct,
    B3FlagshipDirectorPlan,
    B3PreparedArm,
    B3RepresentativeFocus,
)
from evo_engine.cinematic.primitives import CinematicOrganismPrimitive
from evo_engine.cinematic.timeline import PortfolioAnimationFrame
from evo_engine.observation import SpatialCarcassSnapshot, SpatialResourceSnapshot
from evo_engine.presets.reference_ecology.b3_flagship import B3_PRIMARY_STEP

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
    center_x: float
    center_y: float

    @classmethod
    def from_bounds(
        cls,
        width: int,
        height: int,
        *,
        center_x: float,
        center_y: float,
        max_width: float,
        max_height: float,
    ) -> _WorldLayout:
        scale = min(max_width / width, max_height / height)
        return cls(
            width=width,
            height=height,
            display_width=width * scale,
            display_height=height * scale,
            center_x=center_x,
            center_y=center_y,
        )

    def point(self, x: int, y: int) -> list[float]:
        left = self.center_x - self.display_width / 2
        bottom = self.center_y - self.display_height / 2
        return [
            left + (x + 0.5) * self.display_width / self.width,
            bottom + (y + 0.5) * self.display_height / self.height,
            0.0,
        ]


class _B3FlagshipScene(MovingCameraScene):
    """Direct the confirmed B3 evidence into one explanatory flagship film."""

    def __init__(self, plan: B3FlagshipDirectorPlan, **kwargs: object) -> None:
        self._plan = plan
        super().__init__(**kwargs)

    def construct(self) -> None:
        """Render the fixed B3 explanatory arc from committed evidence."""
        self.camera.background_color = _BACKGROUND
        self._question_act()
        self._environment_act()
        self._individual_act()
        self._repetition_act()
        if self._plan.is_full_flagship:
            self._reproduction_act()
            self._population_act()
            self._robustness_act()
        self._conclusion_act()

    def _act(self, key: str) -> B3DirectorAct:
        for act in self._plan.acts:
            if act.key == key:
                return act
        raise KeyError(f"No B3 director act {key!r}.")

    def _question_act(self) -> None:
        act = self._act("question")
        title = _centered_multiline_text(
            ("How can resource geography", "change evolution?"),
            font_size=34,
            color=_TEXT,
            weight="BOLD",
        )
        design = _multiline_text(
            (
                "20 matched founders · inherited max_speed capacity 1 to 4",
                "Initial high-speed allele frequency = 0.50",
                "Same renewable-resource amount · only spatial placement differs",
            ),
            font_size=22,
            color=WHITE,
        ).next_to(title, DOWN, buff=0.42)
        question = Text(
            "Does compact geography change which standing variants reproduce?",
            font_size=22,
            color=YELLOW_C,
        ).next_to(design, DOWN, buff=0.42)
        subtitle = _wrapped_text(
            act.headline,
            width=78,
            font_size=14,
            color=_MUTED,
        ).to_edge(DOWN, buff=0.18)
        group = VGroup(title, design, question).move_to(ORIGIN)
        self.play(FadeIn(title, shift=UP * 0.15), FadeIn(design), run_time=0.65)
        self.play(FadeIn(question), FadeIn(subtitle), run_time=0.35)
        self.wait(1.0)
        self.play(FadeOut(group), FadeOut(subtitle), run_time=0.4)

    def _environment_act(self) -> None:
        act = self._act("environment")
        heading = _act_heading(
            act.title,
            "Representative seed 5 · actual committed resource state at step 10",
        )
        control = _frame_for_step(self._plan.control, 10)
        treatment = _frame_for_step(self._plan.treatment, 10)
        left_layout = _WorldLayout.from_bounds(
            control.spatial.world_width,
            control.spatial.world_height,
            center_x=-3.45,
            center_y=-0.15,
            max_width=5.65,
            max_height=4.65,
        )
        right_layout = _WorldLayout.from_bounds(
            treatment.spatial.world_width,
            treatment.spatial.world_height,
            center_x=3.45,
            center_y=-0.15,
            max_width=5.65,
            max_height=4.65,
        )
        control_world = _world_snapshot(control, left_layout, label=B3_CONTROL_LABEL)
        treatment_world = _world_snapshot(
            treatment,
            right_layout,
            label=B3_TREATMENT_LABEL,
        )
        note = Text(
            "Same world scale · same focal color scale · different resource geography",
            font_size=17,
            color=_MUTED,
        ).to_edge(DOWN, buff=0.2)
        self.play(FadeIn(heading), run_time=0.35)
        self.play(FadeIn(control_world), FadeIn(treatment_world), run_time=0.65)
        self.play(FadeIn(note), run_time=0.3)
        self.wait(1.2)
        self.play(
            FadeOut(heading),
            FadeOut(control_world),
            FadeOut(treatment_world),
            FadeOut(note),
            run_time=0.4,
        )

    def _individual_act(self) -> None:
        act = self._act("individual")
        heading = _act_heading(
            act.title,
            "Separate authoritative examples from the same compact-treatment run",
        )
        self.add_fixed_in_frame_mobjects(heading)
        self.play(FadeIn(heading), run_time=0.35)
        for focus in self._plan.representative_focus:
            self._show_focus_episode(focus)
        self.play(FadeOut(heading), run_time=0.3)
        self.remove_fixed_in_frame_mobjects(heading)

    def _show_focus_episode(self, focus: B3RepresentativeFocus) -> None:
        start = _frame_for_step(self._plan.treatment, focus.first_step)
        end = _frame_for_step(self._plan.treatment, focus.last_step)
        layout = _WorldLayout.from_bounds(
            start.spatial.world_width,
            start.spatial.world_height,
            center_x=-2.05,
            center_y=-0.35,
            max_width=7.1,
            max_height=5.0,
        )
        shell = _world_shell(layout, label="Compact patch · committed world")
        start_resources = _resource_layer(start, layout)
        start_carcasses = _carcass_layer(start, layout)
        start_others = _organism_layer(
            start,
            layout,
            excluded_id=focus.episode.organism_id,
            opacity=0.28,
        )
        start_primitive = start.organism(focus.episode.organism_id)
        focus_marker = _organism_marker(start_primitive, layout, opacity=1.0)
        focus_halo = _focus_halo(start_primitive, layout)
        annotation = _episode_annotation(focus)
        annotation.to_edge(RIGHT, buff=0.28).shift(DOWN * 0.2)
        self.add_fixed_in_frame_mobjects(annotation)

        world_group = VGroup(shell, start_resources, start_carcasses, start_others)
        self.play(
            FadeIn(world_group),
            FadeIn(focus_marker),
            FadeIn(focus_halo),
            FadeIn(annotation),
            run_time=0.5,
        )

        self.camera.frame.save_state()
        start_point = layout.point(start_primitive.x, start_primitive.y)
        self.play(
            self.camera.frame.animate.scale(0.72).move_to(start_point),
            run_time=0.55,
        )

        end_primitive = end.organism(focus.episode.organism_id)
        end_point = layout.point(end_primitive.x, end_primitive.y)
        moving_marker = focus_marker.copy().move_to(end_point)
        moving_halo = focus_halo.copy().move_to(end_point)
        end_marker = _organism_marker(end_primitive, layout, opacity=1.0)
        end_halo = _focus_halo(end_primitive, layout)
        end_resources = _resource_layer(end, layout)
        end_carcasses = _carcass_layer(end, layout)
        end_others = _organism_layer(
            end,
            layout,
            excluded_id=focus.episode.organism_id,
            opacity=0.28,
        )
        self.play(
            Transform(focus_marker, moving_marker),
            Transform(focus_halo, moving_halo),
            FadeOut(start_resources),
            FadeIn(end_resources),
            FadeOut(start_carcasses),
            FadeIn(end_carcasses),
            FadeOut(start_others),
            FadeIn(end_others),
            self.camera.frame.animate.move_to(end_point),
            run_time=0.9,
        )
        # Presentation interpolation moves position only. Any body-mass size change
        # appears discretely once the authoritative committed endpoint is reached.
        focus_marker.become(end_marker)
        focus_halo.become(end_halo)
        self.wait(0.45)
        self.play(Restore(self.camera.frame), run_time=0.5)
        self.play(
            FadeOut(shell),
            FadeOut(end_resources),
            FadeOut(end_carcasses),
            FadeOut(end_others),
            FadeOut(focus_marker),
            FadeOut(focus_halo),
            FadeOut(annotation),
            run_time=0.35,
        )
        self.remove_fixed_in_frame_mobjects(annotation)

    def _repetition_act(self) -> None:
        act = self._act("repetition")
        heading = _act_heading(
            "One event is not selection",
            "Committed snapshots · intervening timesteps omitted, not interpolated",
        )
        layout = _WorldLayout.from_bounds(
            12,
            12,
            center_x=-1.7,
            center_y=-0.3,
            max_width=7.5,
            max_height=5.1,
        )
        steps = (5, 10, 15, 20, 25, 30)
        self.play(FadeIn(heading), run_time=0.35)
        current: object | None = None
        current_label: object | None = None
        for step in steps:
            frame = _frame_for_step(self._plan.treatment, step)
            snapshot = _world_snapshot(
                frame,
                layout,
                label=f"Compact patch · committed step {step}",
                include_legend=False,
            )
            counts = _event_counts_through(self._plan.treatment, step)
            label = _multiline_text(
                (
                    f"Resource-consumption events through step {step}: "
                    f"{counts['ResourceConsumption']}",
                    f"Reproduction events through step {step}: "
                    f"{counts['Reproduction']}",
                ),
                font_size=17,
                color=_MUTED,
            )
            label.to_edge(RIGHT, buff=0.28).shift(DOWN * 0.15)
            if current is not None and current_label is not None:
                self.play(
                    FadeOut(current),
                    FadeOut(current_label),
                    run_time=0.10,
                )
            self.play(FadeIn(snapshot), FadeIn(label), run_time=0.20)
            current = snapshot
            current_label = label
            self.wait(0.12)
        footer = _wrapped_text(
            act.headline,
            width=80,
            font_size=16,
            color=YELLOW_C,
        ).to_edge(DOWN, buff=0.16)
        self.play(FadeIn(footer), run_time=0.25)
        self.wait(0.65)
        animations = [FadeOut(heading), FadeOut(footer)]
        if current is not None:
            animations.append(FadeOut(current))
        if current_label is not None:
            animations.append(FadeOut(current_label))
        self.play(*animations, run_time=0.35)

    def _reproduction_act(self) -> None:
        act = self._act("reproduction")
        heading = _act_heading(
            act.title,
            "Founder realized reproductive success · each point is one simulation seed",
        )
        uniform, compact = _founder_differences(self._plan)
        bound = _symmetric_bound((*uniform, *compact))
        left = _difference_plot(
            B3_CONTROL_LABEL,
            uniform,
            center_x=-3.4,
            bound=bound,
            point_color=BLUE_C,
        )
        right = _difference_plot(
            B3_TREATMENT_LABEL,
            compact,
            center_x=3.4,
            bound=bound,
            point_color=RED_C,
        )
        uniform_low_count = sum(value < 0 for value in uniform)
        uniform_ties = sum(abs(value) < 1e-12 for value in uniform)
        compact_high_count = sum(value > 0 for value in compact)
        summary_text = (
            f"Uniform: lower-speed founders higher in {uniform_low_count}/8"
            + (f" · {uniform_ties} ties" if uniform_ties else "")
            + f"     Compact: higher-speed founders higher in {compact_high_count}/8"
        )
        summary = Text(summary_text, font_size=18, color=YELLOW_C).to_edge(
            DOWN,
            buff=0.18,
        )
        self.play(FadeIn(heading), FadeIn(left), FadeIn(right), run_time=0.6)
        self.play(FadeIn(summary), run_time=0.3)
        self.wait(1.1)
        self.play(
            FadeOut(heading),
            FadeOut(left),
            FadeOut(right),
            FadeOut(summary),
            run_time=0.4,
        )

    def _population_act(self) -> None:
        act = self._act("population")
        heading = _act_heading(
            act.title,
            "Representative seed 5 · high-speed allele frequency · fixed 0 to 1 scale",
        )
        axes = Axes(
            x_range=[0, 50, 10],
            y_range=[0, 1.0, 0.25],
            x_length=10.0,
            y_length=4.2,
            axis_config={"color": GREY_B, "stroke_width": 1.2},
            tips=False,
        ).shift(DOWN * 0.25)
        steps = [
            point.step_index
            for point in self._plan.representative_genetic_trajectory
        ]
        control = [
            point.control_high_speed_frequency
            for point in self._plan.representative_genetic_trajectory
        ]
        treatment = [
            point.treatment_high_speed_frequency
            for point in self._plan.representative_genetic_trajectory
        ]
        control_graph = axes.plot_line_graph(
            x_values=steps,
            y_values=control,
            line_color=BLUE_C,
            add_vertex_dots=False,
        )
        treatment_graph = axes.plot_line_graph(
            x_values=steps,
            y_values=treatment,
            line_color=RED_C,
            add_vertex_dots=False,
        )
        baseline = DashedLine(
            axes.c2p(0, 0.5),
            axes.c2p(50, 0.5),
            color=_MUTED,
            stroke_opacity=0.5,
        )
        primary = DashedLine(
            axes.c2p(B3_PRIMARY_STEP, 0),
            axes.c2p(B3_PRIMARY_STEP, 1),
            color=YELLOW_C,
            stroke_opacity=0.65,
        )
        labels = _multiline_text(
            (
                "Blue = Uniform",
                "Red = Compact radius-1",
                "Horizontal dash = founder baseline 0.50",
                "Yellow dash = predeclared step 30",
            ),
            font_size=16,
            color=_MUTED,
        ).to_edge(RIGHT, buff=0.25).shift(UP * 1.15)
        primary_point = next(
            point
            for point in self._plan.representative_genetic_trajectory
            if point.step_index == B3_PRIMARY_STEP
        )
        primary_text = Text(
            "Step 30: "
            f"Uniform {primary_point.control_high_speed_frequency:.3f} · "
            f"Compact {primary_point.treatment_high_speed_frequency:.3f}",
            font_size=19,
            color=YELLOW_C,
        ).to_edge(DOWN, buff=0.18)
        self.play(FadeIn(heading), FadeIn(axes), FadeIn(baseline), run_time=0.45)
        self.play(Create(control_graph), Create(treatment_graph), run_time=1.0)
        self.play(FadeIn(primary), FadeIn(labels), FadeIn(primary_text), run_time=0.4)
        self.wait(1.15)
        self.play(
            FadeOut(heading),
            FadeOut(axes),
            FadeOut(control_graph),
            FadeOut(treatment_graph),
            FadeOut(baseline),
            FadeOut(primary),
            FadeOut(labels),
            FadeOut(primary_text),
            run_time=0.4,
        )

    def _robustness_act(self) -> None:
        act = self._act("robustness")
        heading = _act_heading(
            act.title,
            "Independent confirmation at step 30 · replicate = simulation run",
        )
        plot = _confirmation_plot(self._plan)
        self.play(FadeIn(heading), FadeIn(plot), run_time=0.6)
        self.wait(1.05)
        self.play(FadeOut(plot), run_time=0.3)

        sensitivity = _sensitivity_plot(self._plan)
        sensitivity_title = _centered_multiline_text(
            (
                "Geometry sensitivity",
                "Broader radius-2 patches weaken the compact advantage in aggregate.",
            ),
            font_size=21,
            color=WHITE,
        ).shift(UP * 2.25)
        self.play(FadeIn(sensitivity), FadeIn(sensitivity_title), run_time=0.5)
        self.wait(1.05)
        self.play(
            FadeOut(heading),
            FadeOut(sensitivity),
            FadeOut(sensitivity_title),
            run_time=0.4,
        )

    def _conclusion_act(self) -> None:
        title = Text(
            "What this experiment supports",
            font_size=36,
            weight="BOLD",
            color=_TEXT,
        )
        claim = _wrapped_text(
            self._plan.conclusion,
            width=72,
            font_size=20,
            color=WHITE,
        ).next_to(title, DOWN, buff=0.42)
        scope = _wrapped_text(
            self._plan.scope_qualifier,
            width=82,
            font_size=16,
            color=_MUTED,
        ).next_to(claim, DOWN, buff=0.4)
        footer = Text(
            "Evidence → mechanism → reproduction → population change",
            font_size=18,
            color=YELLOW_C,
        ).next_to(scope, DOWN, buff=0.4)
        group = VGroup(title, claim, scope, footer).move_to(ORIGIN)
        self.play(FadeIn(title), FadeIn(claim, shift=UP * 0.1), run_time=0.6)
        self.play(FadeIn(scope), FadeIn(footer), run_time=0.35)
        self.wait(1.4)
        self.play(FadeOut(group), run_time=0.4)


def render_b3_flagship_with_manim(
    plan: B3FlagshipDirectorPlan,
    output_path: Path,
    *,
    quality: AnimationQuality,
) -> Path:
    """Render the concrete B3 director and copy finished media to destination."""
    width, height, frame_rate = _QUALITY_SETTINGS[quality]
    output_format = output_path.suffix.lower().removeprefix(".")
    with TemporaryDirectory(prefix="evo-engine-b3-manim-") as temporary_directory:
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
            scene = _B3FlagshipScene(plan)
            scene.render()
            rendered_path = _rendered_media_path(scene, output_format)
            if not rendered_path.exists():
                raise RuntimeError(
                    f"Manim did not produce expected B3 media: {rendered_path}"
                )
            shutil.copy2(rendered_path, output_path)
    return output_path


def _rendered_media_path(scene: Any, output_format: str) -> Path:
    writer = scene.renderer.file_writer
    if output_format == "gif":
        return Path(writer.gif_file_path)
    return Path(writer.movie_file_path)


def _act_heading(title: str, subtitle: str) -> object:
    title_text = Text(title, font_size=31, weight="BOLD", color=_TEXT)
    subtitle_text = Text(subtitle, font_size=16, color=_MUTED)
    return VGroup(title_text, subtitle_text).arrange(DOWN, buff=0.1).to_edge(
        UP,
        buff=0.18,
    )


def _multiline_text(
    lines: tuple[str, ...],
    *,
    font_size: int,
    color: object,
) -> object:
    return VGroup(
        *(Text(line, font_size=font_size, color=color) for line in lines)
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.14)


def _centered_multiline_text(
    lines: tuple[str, ...],
    *,
    font_size: int,
    color: object,
    weight: str | None = None,
) -> object:
    return VGroup(
        *(
            Text(line, font_size=font_size, color=color, weight=weight)
            for line in lines
        )
    ).arrange(DOWN, buff=0.08)


def _wrapped_text(
    value: str,
    *,
    width: int,
    font_size: int,
    color: object,
) -> object:
    lines = tuple(textwrap.wrap(value, width=width))
    return _multiline_text(lines, font_size=font_size, color=color)


def _frame_for_step(arm: B3PreparedArm, step: int) -> PortfolioAnimationFrame:
    for frame in arm.timeline.frames:
        if frame.step_index == step:
            return frame
    raise KeyError(f"No committed {arm.label} cinematic frame for step {step}.")


def _world_snapshot(
    frame: PortfolioAnimationFrame,
    layout: _WorldLayout,
    *,
    label: str,
    include_legend: bool = True,
) -> object:
    shell = _world_shell(layout, label=label)
    resources = _resource_layer(frame, layout)
    carcasses = _carcass_layer(frame, layout)
    organisms = _organism_layer(frame, layout)
    items: list[object] = [shell, resources, carcasses, organisms]
    if include_legend:
        legend = _speed_legend()
        legend.next_to(shell, DOWN, buff=0.12)
        items.append(legend)
    return VGroup(*items)


def _world_shell(layout: _WorldLayout, *, label: str) -> object:
    border = RoundedRectangle(
        width=layout.display_width + 0.16,
        height=layout.display_height + 0.16,
        corner_radius=0.10,
        stroke_color=GREY_B,
        stroke_width=1.5,
        fill_color=_PANEL,
        fill_opacity=0.55,
    ).move_to([layout.center_x, layout.center_y, 0])
    grid = VGroup(*_grid_lines(layout))
    title = Text(label, font_size=18, color=_TEXT).next_to(border, UP, buff=0.11)
    return VGroup(border, grid, title)


def _grid_lines(layout: _WorldLayout) -> tuple[object, ...]:
    left = layout.center_x - layout.display_width / 2
    right = layout.center_x + layout.display_width / 2
    bottom = layout.center_y - layout.display_height / 2
    top = layout.center_y + layout.display_height / 2
    lines: list[object] = []
    for x in range(1, layout.width):
        scene_x = left + x * layout.display_width / layout.width
        lines.append(
            Line(
                [scene_x, bottom, 0],
                [scene_x, top, 0],
                stroke_color=GREY_B,
                stroke_opacity=0.10,
                stroke_width=0.6,
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
                stroke_width=0.6,
            )
        )
    return tuple(lines)


def _resource_layer(frame: PortfolioAnimationFrame, layout: _WorldLayout) -> object:
    return VGroup(
        *(_resource_marker(resource, layout) for resource in frame.spatial.resources)
    )


def _resource_marker(resource: SpatialResourceSnapshot, layout: _WorldLayout) -> object:
    side = 0.065 + min(resource.amount, 14) * 0.005
    return Square(
        side_length=side,
        stroke_width=0,
        fill_color=_RESOURCE,
        fill_opacity=0.78,
    ).move_to(layout.point(resource.x, resource.y))


def _carcass_layer(frame: PortfolioAnimationFrame, layout: _WorldLayout) -> object:
    return VGroup(
        *(_carcass_marker(carcass, layout) for carcass in frame.spatial.carcasses)
    )


def _carcass_marker(carcass: SpatialCarcassSnapshot, layout: _WorldLayout) -> object:
    side = 0.08 + min(carcass.resource_units, 12) * 0.0035
    return (
        Square(
            side_length=side,
            color=GREY_B,
            fill_opacity=0.28,
            stroke_width=0.8,
        )
        .rotate(math.pi / 4)
        .move_to(layout.point(carcass.x, carcass.y))
    )


def _organism_layer(
    frame: PortfolioAnimationFrame,
    layout: _WorldLayout,
    *,
    excluded_id: int | None = None,
    opacity: float = 0.95,
) -> object:
    return VGroup(
        *(
            _organism_marker(organism, layout, opacity=opacity)
            for organism in frame.organisms
            if organism.organism_id != excluded_id
        )
    )


def _organism_marker(
    organism: CinematicOrganismPrimitive,
    layout: _WorldLayout,
    *,
    opacity: float,
) -> object:
    radius = 0.06 + min(organism.body_mass, 30) * 0.0018
    return Circle(
        radius=radius,
        stroke_color=WHITE,
        stroke_width=0.55,
        fill_color=_organism_fill(organism),
        fill_opacity=opacity,
        stroke_opacity=opacity,
    ).move_to(layout.point(organism.x, organism.y))


def _organism_fill(organism: CinematicOrganismPrimitive) -> object:
    if organism.focal_normalized is None:
        return TEAL_C
    return interpolate_color(BLUE_C, RED_C, organism.focal_normalized)


def _focus_halo(organism: CinematicOrganismPrimitive, layout: _WorldLayout) -> object:
    radius = 0.105 + min(organism.body_mass, 30) * 0.0018
    return Circle(
        radius=radius,
        stroke_color=YELLOW_C,
        stroke_width=3.0,
        fill_opacity=0,
    ).move_to(layout.point(organism.x, organism.y))


def _speed_legend() -> object:
    low = Dot(radius=0.045, color=BLUE_C)
    high = Dot(radius=0.045, color=RED_C)
    return VGroup(
        Text("Fill = Maximum speed", font_size=14, color=_MUTED),
        VGroup(
            low,
            Text("1", font_size=13, color=_MUTED),
            high,
            Text("4", font_size=13, color=_MUTED),
        ).arrange(RIGHT, buff=0.08),
    ).arrange(DOWN, buff=0.05)


def _episode_annotation(focus: B3RepresentativeFocus) -> object:
    episode = focus.episode
    text = _multiline_text(
        (
            f"Organism {episode.organism_id} · max_speed {episode.max_speed_capacity}",
            f"Committed step {episode.completed_step_index}",
            f"Resolved move {episode.start} → {episode.end}",
            f"Realized displacement {episode.realized_displacement:.0f}",
            f"Movement energy cost {episode.movement_energy_cost}",
            f"Committed resource consumed {episode.resource_consumed_same_step}",
        ),
        font_size=17,
        color=WHITE,
    )
    panel = RoundedRectangle(
        width=text.width + 0.35,
        height=text.height + 0.28,
        corner_radius=0.10,
        stroke_color=GREY_B,
        stroke_width=1.0,
        fill_color=_PANEL,
        fill_opacity=0.90,
    ).move_to(text)
    return VGroup(panel, text)


def _event_counts_through(arm: B3PreparedArm, step: int) -> dict[str, int]:
    counts = {"ResourceConsumption": 0, "Reproduction": 0}
    for frame in arm.timeline.frames:
        if frame.step_index > step:
            break
        for event in frame.applied_events:
            if event.process_name in counts:
                counts[event.process_name] += 1
    return counts


def _founder_differences(
    plan: B3FlagshipDirectorPlan,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    uniform: list[float] = []
    compact: list[float] = []
    for point in plan.founder_contribution_points:
        difference = point.high_speed_mean - point.low_speed_mean
        if point.environment == "uniform":
            uniform.append(difference)
        else:
            compact.append(difference)
    return tuple(uniform), tuple(compact)


def _symmetric_bound(values: tuple[float, ...]) -> float:
    maximum = max((abs(value) for value in values), default=1.0)
    return max(1.0, math.ceil(maximum * 2) / 2)


def _difference_plot(
    title: str,
    values: tuple[float, ...],
    *,
    center_x: float,
    bound: float,
    point_color: object,
) -> object:
    axes = Axes(
        x_range=[0, 9, 1],
        y_range=[-bound, bound, bound / 2],
        x_length=5.2,
        y_length=3.4,
        axis_config={"color": GREY_B, "stroke_width": 1.0},
        tips=False,
    ).move_to([center_x, -0.35, 0])
    zero = DashedLine(
        axes.c2p(0, 0),
        axes.c2p(9, 0),
        color=_MUTED,
        stroke_opacity=0.6,
    )
    dots = VGroup(
        *(
            Dot(axes.c2p(index + 1, value), radius=0.055, color=point_color)
            for index, value in enumerate(values)
        )
    )
    label = Text(title, font_size=21, color=_TEXT).next_to(axes, UP, buff=0.16)
    axis_label = Text(
        "high-speed − low-speed founder RRS",
        font_size=14,
        color=_MUTED,
    ).next_to(axes, DOWN, buff=0.12)
    return VGroup(axes, zero, dots, label, axis_label)


def _confirmation_plot(plan: B3FlagshipDirectorPlan) -> object:
    axes = Axes(
        x_range=[0, 9, 1],
        y_range=[0, 1.0, 0.25],
        x_length=10.2,
        y_length=4.3,
        axis_config={"color": GREY_B, "stroke_width": 1.1},
        tips=False,
    ).shift(DOWN * 0.25)
    items: list[object] = [axes]
    for index, point in enumerate(plan.confirmation_points, start=1):
        control = axes.c2p(index, point.control_high_speed_frequency)
        treatment = axes.c2p(index, point.treatment_high_speed_frequency)
        items.extend(
            (
                Line(control, treatment, color=GREY_B, stroke_width=1.2),
                Dot(control, radius=0.05, color=BLUE_C),
                Dot(treatment, radius=0.05, color=RED_C),
                Text(str(point.seed), font_size=12, color=_MUTED).next_to(
                    axes.c2p(index, 0),
                    DOWN,
                    buff=0.08,
                ),
            )
        )
    mean_control = sum(
        point.control_high_speed_frequency for point in plan.confirmation_points
    ) / len(plan.confirmation_points)
    mean_treatment = sum(
        point.treatment_high_speed_frequency for point in plan.confirmation_points
    ) / len(plan.confirmation_points)
    positives = sum(point.paired_effect > 0 for point in plan.confirmation_points)
    legend = _multiline_text(
        (
            "Blue = Uniform · Red = Compact radius-1",
            f"Mean step-30 frequency: Uniform {mean_control:.3f} · "
            f"Compact {mean_treatment:.3f}",
            f"Compact > matched Uniform in {positives}/8 seeds",
        ),
        font_size=17,
        color=_MUTED,
    ).to_edge(DOWN, buff=0.16)
    items.append(legend)
    return VGroup(*items)


def _sensitivity_plot(plan: B3FlagshipDirectorPlan) -> object:
    mean_uniform = sum(
        point.control_high_speed_frequency for point in plan.confirmation_points
    ) / len(plan.confirmation_points)
    mean_compact = sum(
        point.treatment_high_speed_frequency for point in plan.confirmation_points
    ) / len(plan.confirmation_points)
    broad = plan.broad_patch_step30_mean
    if broad is None:
        raise ValueError("Full B3 flagship requires broad-patch sensitivity evidence.")
    axes = Axes(
        x_range=[0, 4, 1],
        y_range=[0, 1.0, 0.25],
        x_length=7.4,
        y_length=3.7,
        axis_config={"color": GREY_B, "stroke_width": 1.0},
        tips=False,
    ).shift(DOWN * 0.4)
    values = (
        (1, mean_uniform, BLUE_C, "Uniform"),
        (2, mean_compact, RED_C, "Compact r=1"),
        (3, broad, ORANGE, "Compact r=2"),
    )
    marks: list[object] = [axes]
    for x, value, color, label in values:
        base = axes.c2p(x, 0)
        point = axes.c2p(x, value)
        marks.extend(
            (
                Line(base, point, color=color, stroke_width=3),
                Dot(point, radius=0.07, color=color),
                Text(label, font_size=16, color=_MUTED).next_to(
                    base,
                    DOWN,
                    buff=0.09,
                ),
                Text(f"{value:.3f}", font_size=16, color=WHITE).next_to(
                    point,
                    UP,
                    buff=0.08,
                ),
            )
        )
    return VGroup(*marks)


__all__ = ["render_b3_flagship_with_manim"]
