"""Reusable Streamlit controls for committed-evidence world exploration.

The retained V2 workspace established the interaction behavior reused here:
committed-step navigation, playback, presentation toggles, and organism focus.
This module owns only UI/session state. It does not own Workbench science, result
association, or world-frame construction.
"""

from __future__ import annotations

import time
from typing import Literal

import attrs
import streamlit as st

from evo_engine.observation import SpatialObservation

PresentationExperience = Literal["landing", "world"]

_PREFIX = "wu5_presentation_"
_OWNER_KEY = f"{_PREFIX}owner"
_EXPERIENCE_KEY = f"{_PREFIX}experience"
_FOCUS_KEY = f"{_PREFIX}focus_mode"
_STEP_KEY = f"{_PREFIX}world_step"
_STEP_WIDGET_KEY = f"{_STEP_KEY}_widget"
_PLAYING_KEY = f"{_PREFIX}world_playing"
_SPEED_KEY = f"{_PREFIX}world_speed"
_NEXT_ADVANCE_KEY = f"{_PREFIX}world_next_advance"
_RESOURCES_KEY = f"{_PREFIX}show_resources"
_CARCASSES_KEY = f"{_PREFIX}show_carcasses"
_TRAILS_KEY = f"{_PREFIX}show_trails"
_TRAIL_LENGTH_KEY = f"{_PREFIX}trail_length"
_LABELS_KEY = f"{_PREFIX}show_labels"
_B3_SEED_KEY = f"{_PREFIX}b3_seed"

_PLAYBACK_SPEEDS = (0.5, 1.0, 2.0)
_BASE_PLAYBACK_INTERVAL_SECONDS = 0.6


@attrs.frozen(slots=True, kw_only=True)
class WorldViewOptions:
    """Describe renderer-only options selected in the interactive world."""

    show_resources: bool
    show_carcasses: bool
    show_trails: bool
    trail_length: int
    show_labels: bool


def clear_presentation_state() -> None:
    """Clear all WU5 renderer/view state from the current Streamlit session."""
    for key in tuple(st.session_state):
        if str(key).startswith(_PREFIX):
            st.session_state.pop(key, None)


def ensure_presentation_owner(owner_token: str) -> None:
    """Reset view state when the exact active scientific result owner changes."""
    if type(owner_token) is not str or not owner_token.strip():
        raise TypeError("owner_token must be a non-empty string.")
    if st.session_state.get(_OWNER_KEY) == owner_token:
        return
    clear_presentation_state()
    st.session_state[_OWNER_KEY] = owner_token


def presentation_experience() -> PresentationExperience:
    """Return the current Presentation subexperience."""
    value = st.session_state.get(_EXPERIENCE_KEY, "landing")
    return value if value in ("landing", "world") else "landing"


def open_world_explorer() -> None:
    """Enter the interactive-world subexperience."""
    st.session_state[_EXPERIENCE_KEY] = "world"


def show_presentation_landing() -> None:
    """Return to the Presentation landing page without changing science."""
    st.session_state[_EXPERIENCE_KEY] = "landing"
    st.session_state[_FOCUS_KEY] = False
    _stop_playback()


def presentation_focus_mode() -> bool:
    """Return whether the world explorer is using the shell's focus layout."""
    return st.session_state.get(_FOCUS_KEY) is True


def set_presentation_focus_mode(enabled: bool) -> None:
    """Enable or disable full-window Presentation focus mode."""
    if type(enabled) is not bool:
        raise TypeError("enabled must be a bool.")
    st.session_state[_FOCUS_KEY] = enabled


def initialize_world_state(steps: tuple[int, ...]) -> None:
    """Initialize or reconcile common world controls for recorded committed steps."""
    _validate_steps(steps)
    if st.session_state.get(_STEP_KEY) not in steps:
        _set_step(steps[0])
        _stop_playback()
    st.session_state.setdefault(_PLAYING_KEY, False)
    st.session_state.setdefault(_SPEED_KEY, 1.0)
    st.session_state.setdefault(_RESOURCES_KEY, True)
    st.session_state.setdefault(_CARCASSES_KEY, True)
    st.session_state.setdefault(_TRAILS_KEY, True)
    st.session_state.setdefault(_TRAIL_LENGTH_KEY, 5)
    st.session_state.setdefault(_LABELS_KEY, False)


def selected_b3_seed(seeds: tuple[int, ...]) -> int:
    """Render authoritative B3 confirmation-seed selection and reconcile state."""
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must contain at least one integer confirmation seed.")
    current = st.session_state.get(_B3_SEED_KEY)
    if current not in seeds:
        current = seeds[0]
        st.session_state[_B3_SEED_KEY] = current
        _reset_timeline_and_selection()
    selected = st.selectbox(
        "Confirmation seed",
        seeds,
        index=seeds.index(current),
        key=f"{_B3_SEED_KEY}_widget",
        help="Only confirmation replicate seeds recorded by the authoritative B3 result.",
    )
    if selected != st.session_state[_B3_SEED_KEY]:
        st.session_state[_B3_SEED_KEY] = selected
        _reset_timeline_and_selection()
        st.rerun(scope="app")
    return int(st.session_state[_B3_SEED_KEY])


def render_committed_step_controls(steps: tuple[int, ...]) -> int:
    """Render exact committed-step navigation and return the selected step."""
    initialize_world_state(steps)
    selected = _selected_step(steps)
    previous_col, step_col, next_col = st.columns((1, 4, 1))
    if previous_col.button(
        "Previous",
        disabled=selected == steps[0],
        use_container_width=True,
        key=f"{_PREFIX}previous",
    ):
        _set_step(_previous_step(steps, selected))
        _stop_playback()

    selected = _selected_step(steps)
    if next_col.button(
        "Next",
        disabled=selected == steps[-1],
        use_container_width=True,
        key=f"{_PREFIX}next",
    ):
        _set_step(_next_step(steps, selected))
        _stop_playback()

    selected = _selected_step(steps)
    slider_value = step_col.select_slider(
        "Committed step",
        options=steps,
        value=selected,
        key=_STEP_WIDGET_KEY,
    )
    if slider_value != st.session_state[_STEP_KEY]:
        st.session_state[_STEP_KEY] = slider_value
        _stop_playback()
        st.rerun(scope="app")
    return _selected_step(steps)


def render_view_controls(steps: tuple[int, ...]) -> WorldViewOptions:
    """Render playback and renderer-only world controls."""
    initialize_world_state(steps)
    selected = _selected_step(steps)
    play_col, speed_col, focus_col = st.columns((1, 1.5, 1.5))
    if st.session_state[_PLAYING_KEY]:
        if play_col.button("Pause", use_container_width=True, key=f"{_PREFIX}pause"):
            _stop_playback()
            st.rerun(scope="app")
    elif play_col.button(
        "Play",
        disabled=selected == steps[-1],
        use_container_width=True,
        key=f"{_PREFIX}play",
    ):
        st.session_state[_PLAYING_KEY] = True
        _schedule_next_advance()
        st.rerun(scope="app")

    speed = speed_col.selectbox(
        "Playback speed",
        _PLAYBACK_SPEEDS,
        index=_PLAYBACK_SPEEDS.index(float(st.session_state[_SPEED_KEY])),
        format_func=lambda value: f"{value:g}×",
        key=f"{_SPEED_KEY}_widget",
    )
    if speed != st.session_state[_SPEED_KEY]:
        st.session_state[_SPEED_KEY] = speed
        if st.session_state[_PLAYING_KEY]:
            _schedule_next_advance()
            st.rerun(scope="app")

    focus_label = "Exit Focus Mode" if presentation_focus_mode() else "Focus Mode"
    if focus_col.button(
        focus_label,
        use_container_width=True,
        key=f"{_PREFIX}focus_toggle",
    ):
        set_presentation_focus_mode(not presentation_focus_mode())
        st.rerun(scope="app")

    with st.expander("View", expanded=False):
        columns = st.columns(4)
        show_resources = columns[0].checkbox("Resources", key=_RESOURCES_KEY)
        show_carcasses = columns[1].checkbox("Carcasses", key=_CARCASSES_KEY)
        show_trails = columns[2].checkbox("Movement trails", key=_TRAILS_KEY)
        show_labels = columns[3].checkbox("Organism labels", key=_LABELS_KEY)
        trail_length = st.slider(
            "Trail length (committed frames)",
            min_value=2,
            max_value=12,
            key=_TRAIL_LENGTH_KEY,
            disabled=not show_trails,
        )
    return WorldViewOptions(
        show_resources=show_resources,
        show_carcasses=show_carcasses,
        show_trails=show_trails,
        trail_length=trail_length,
        show_labels=show_labels,
    )


def render_organism_selector(
    organism_ids: tuple[int, ...],
    *,
    key_suffix: str,
    label: str = "Selected organism",
) -> int | None:
    """Render presentation-only organism focus over IDs present in recorded replay."""
    if type(key_suffix) is not str or not key_suffix.strip():
        raise TypeError("key_suffix must be a non-empty string.")
    if any(type(organism_id) is not int for organism_id in organism_ids):
        raise TypeError("organism_ids must contain integers.")
    key = f"{_PREFIX}selected_organism_{key_suffix}"
    current = st.session_state.get(key)
    options = (None, *organism_ids)
    if current not in options:
        st.session_state[key] = None
    return st.selectbox(
        label,
        options,
        key=key,
        format_func=lambda value: "None" if value is None else f"Organism {value}",
        help=(
            "Selection is presentation focus only. It changes the outline and "
            "inspector, never scientific state or focal-trait encoding."
        ),
    )


def observed_organism_ids(
    history: tuple[SpatialObservation, ...],
) -> tuple[int, ...]:
    """Return permanent organism IDs appearing anywhere in recorded spatial evidence."""
    return tuple(
        sorted(
            {organism.organism_id for frame in history for organism in frame.organisms}
        )
    )


def common_step_indices(
    left: tuple[SpatialObservation, ...],
    right: tuple[SpatialObservation, ...],
) -> tuple[int, ...]:
    """Return recorded committed steps shared by two matched replay histories."""
    right_steps = {frame.step_index for frame in right}
    return tuple(frame.step_index for frame in left if frame.step_index in right_steps)


def advance_playback_if_due(steps: tuple[int, ...]) -> None:
    """Advance one recorded committed step when renderer-owned playback is due."""
    initialize_world_state(steps)
    if not st.session_state[_PLAYING_KEY]:
        return
    current = _selected_step(steps)
    if current == steps[-1]:
        _stop_playback()
        return
    deadline = st.session_state.get(_NEXT_ADVANCE_KEY)
    if not isinstance(deadline, float):
        _schedule_next_advance()
        return
    if time.monotonic() < deadline:
        return
    _set_step(_next_step(steps, current))
    if st.session_state[_STEP_KEY] == steps[-1]:
        _stop_playback()
        return
    _schedule_next_advance()


def playback_interval() -> float | None:
    """Return the Streamlit fragment interval while playback is active."""
    if st.session_state.get(_PLAYING_KEY) is not True:
        return None
    speed = float(st.session_state.get(_SPEED_KEY, 1.0))
    return _BASE_PLAYBACK_INTERVAL_SECONDS / speed


def _reset_timeline_and_selection() -> None:
    for key in tuple(st.session_state):
        text = str(key)
        if text in (_STEP_KEY, _PLAYING_KEY, _NEXT_ADVANCE_KEY, _STEP_WIDGET_KEY):
            st.session_state.pop(key, None)
        elif text.startswith(f"{_PREFIX}selected_organism_"):
            st.session_state.pop(key, None)


def _set_step(step: int) -> None:
    st.session_state[_STEP_KEY] = step
    st.session_state.pop(_STEP_WIDGET_KEY, None)


def _stop_playback() -> None:
    st.session_state[_PLAYING_KEY] = False
    st.session_state.pop(_NEXT_ADVANCE_KEY, None)


def _schedule_next_advance() -> None:
    st.session_state[_NEXT_ADVANCE_KEY] = time.monotonic() + (
        _BASE_PLAYBACK_INTERVAL_SECONDS / float(st.session_state[_SPEED_KEY])
    )


def _selected_step(steps: tuple[int, ...]) -> int:
    value = st.session_state.get(_STEP_KEY)
    return value if isinstance(value, int) and value in steps else steps[0]


def _previous_step(steps: tuple[int, ...], current: int) -> int:
    return steps[max(0, steps.index(current) - 1)]


def _next_step(steps: tuple[int, ...], current: int) -> int:
    return steps[min(len(steps) - 1, steps.index(current) + 1)]


def _validate_steps(steps: tuple[int, ...]) -> None:
    if not steps or any(type(step) is not int for step in steps):
        raise ValueError("steps must contain at least one committed integer step.")
    if len(steps) != len(set(steps)):
        raise ValueError("steps must not contain duplicates.")


__all__ = [
    "WorldViewOptions",
    "advance_playback_if_due",
    "clear_presentation_state",
    "common_step_indices",
    "ensure_presentation_owner",
    "initialize_world_state",
    "observed_organism_ids",
    "open_world_explorer",
    "playback_interval",
    "presentation_experience",
    "presentation_focus_mode",
    "render_committed_step_controls",
    "render_organism_selector",
    "render_view_controls",
    "selected_b3_seed",
    "set_presentation_focus_mode",
    "show_presentation_landing",
]
