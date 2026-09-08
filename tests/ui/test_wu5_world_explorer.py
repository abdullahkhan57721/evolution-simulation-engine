"""Focused WU5 tests for presentation-only world explorer state."""

from __future__ import annotations

from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast

import pytest

import evo_engine.ui.world_explorer as world_explorer
from evo_engine.observation import SpatialObservation


class _Context:
    def __enter__(self) -> _Context:
        return self

    def __exit__(self, *_: object) -> None:
        return None


class _FakeStreamlit(_Context):
    def __init__(self) -> None:
        self.session_state: dict[str, Any] = {}
        self.buttons: dict[str, bool] = {}
        self.selections: dict[str, Any] = {}
        self.checkboxes: dict[str, bool] = {}
        self.sliders: dict[str, Any] = {}
        self.reruns = 0

    def columns(self, spec: int | Sequence[Any]) -> tuple[_FakeStreamlit, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        return tuple(self for _ in range(count))

    def button(self, label: str, *, key: str | None = None, **_: Any) -> bool:
        return self.buttons.get(key or label, False)

    def selectbox(
        self,
        label: str,
        options: Sequence[Any],
        *,
        key: str | None = None,
        **_: Any,
    ) -> Any:
        if key is not None and key in self.selections:
            return self.selections[key]
        if key is not None and key in self.session_state:
            return self.session_state[key]
        return options[0]

    def select_slider(
        self,
        label: str,
        *,
        options: Sequence[Any],
        value: Any,
        key: str | None = None,
        **_: Any,
    ) -> Any:
        if key is not None and key in self.selections:
            return self.selections[key]
        return value

    def checkbox(self, label: str, *, key: str, **_: Any) -> bool:
        if key in self.checkboxes:
            value = self.checkboxes[key]
            self.session_state[key] = value
            return value
        return bool(self.session_state[key])

    def slider(self, label: str, *, key: str, **_: Any) -> Any:
        if key in self.sliders:
            value = self.sliders[key]
            self.session_state[key] = value
            return value
        return self.session_state[key]

    def expander(self, *_: Any, **__: Any) -> _Context:
        return self

    def rerun(self, **_: Any) -> None:
        self.reruns += 1


def _patch_streamlit(
    monkeypatch: pytest.MonkeyPatch,
) -> _FakeStreamlit:
    fake = _FakeStreamlit()
    monkeypatch.setattr(world_explorer, "st", fake)
    return fake


def test_owner_and_experience_state_are_namespaced_and_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    fake.session_state["unrelated"] = "keep"
    fake.session_state["wu5_presentation_old"] = "discard"

    world_explorer.ensure_presentation_owner("revision:digest:run-1")
    assert fake.session_state["unrelated"] == "keep"
    assert fake.session_state["wu5_presentation_owner"] == "revision:digest:run-1"
    assert "wu5_presentation_old" not in fake.session_state

    world_explorer.open_world_explorer()
    world_explorer.set_presentation_focus_mode(True)
    assert world_explorer.presentation_experience() == "world"
    assert world_explorer.presentation_focus_mode() is True

    fake.session_state["wu5_presentation_world_playing"] = True
    fake.session_state["wu5_presentation_world_next_advance"] = 5.0
    world_explorer.show_presentation_landing()
    assert world_explorer.presentation_experience() == "landing"
    assert world_explorer.presentation_focus_mode() is False
    assert fake.session_state["wu5_presentation_world_playing"] is False
    assert "wu5_presentation_world_next_advance" not in fake.session_state

    before = dict(fake.session_state)
    world_explorer.ensure_presentation_owner("revision:digest:run-1")
    assert fake.session_state == before

    world_explorer.ensure_presentation_owner("revision:digest:run-2")
    assert fake.session_state["unrelated"] == "keep"
    assert fake.session_state["wu5_presentation_owner"] == "revision:digest:run-2"
    assert world_explorer.presentation_experience() == "landing"

    fake.session_state["wu5_presentation_experience"] = "invalid"
    assert world_explorer.presentation_experience() == "landing"
    world_explorer.clear_presentation_state()
    assert fake.session_state == {"unrelated": "keep"}


def test_state_validation_and_initialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)

    with pytest.raises(TypeError, match="owner_token"):
        world_explorer.ensure_presentation_owner("")
    with pytest.raises(TypeError, match="bool"):
        world_explorer.set_presentation_focus_mode(cast(Any, 1))
    with pytest.raises(ValueError, match="at least one"):
        world_explorer.initialize_world_state(())
    with pytest.raises(ValueError, match="integer"):
        world_explorer.initialize_world_state(cast(Any, (0, "1")))
    with pytest.raises(ValueError, match="duplicates"):
        world_explorer.initialize_world_state((0, 0))

    fake.session_state["wu5_presentation_world_step"] = 99
    fake.session_state["wu5_presentation_world_playing"] = True
    world_explorer.initialize_world_state((0, 2, 4))

    assert fake.session_state["wu5_presentation_world_step"] == 0
    assert fake.session_state["wu5_presentation_world_playing"] is False
    assert fake.session_state["wu5_presentation_world_speed"] == 1.0
    assert fake.session_state["wu5_presentation_show_resources"] is True
    assert fake.session_state["wu5_presentation_show_carcasses"] is True
    assert fake.session_state["wu5_presentation_show_trails"] is True
    assert fake.session_state["wu5_presentation_trail_length"] == 5
    assert fake.session_state["wu5_presentation_show_labels"] is False
    assert world_explorer.playback_interval() is None


def test_b3_seed_selection_accepts_only_authoritative_confirmation_seeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)

    with pytest.raises(ValueError, match="confirmation seed"):
        world_explorer.selected_b3_seed(())
    with pytest.raises(ValueError, match="confirmation seed"):
        world_explorer.selected_b3_seed(cast(Any, (1, "2")))

    fake.session_state["wu5_presentation_selected_organism_b3_control"] = 7
    assert world_explorer.selected_b3_seed((11, 13)) == 11
    assert "wu5_presentation_selected_organism_b3_control" not in fake.session_state

    fake.selections["wu5_presentation_b3_seed_widget"] = 13
    fake.session_state["wu5_presentation_world_step"] = 4
    fake.session_state["wu5_presentation_selected_organism_b3_treatment"] = 8
    assert world_explorer.selected_b3_seed((11, 13)) == 13
    assert fake.reruns == 1
    assert "wu5_presentation_world_step" not in fake.session_state
    assert "wu5_presentation_selected_organism_b3_treatment" not in fake.session_state


def test_committed_step_controls_keep_playback_presentation_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    steps = (0, 2, 4)
    world_explorer.initialize_world_state(steps)

    fake.buttons["wu5_presentation_next"] = True
    assert world_explorer.render_committed_step_controls(steps) == 2
    fake.buttons.clear()

    fake.buttons["wu5_presentation_previous"] = True
    assert world_explorer.render_committed_step_controls(steps) == 0
    fake.buttons.clear()

    fake.selections["wu5_presentation_world_step_widget"] = 4
    assert world_explorer.render_committed_step_controls(steps) == 4
    assert fake.reruns == 1
    assert fake.session_state["wu5_presentation_world_playing"] is False


def test_view_controls_update_only_renderer_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    monkeypatch.setattr(world_explorer.time, "monotonic", lambda: 10.0)
    steps = (0, 1, 2)
    world_explorer.initialize_world_state(steps)

    fake.buttons["wu5_presentation_play"] = True
    fake.selections["wu5_presentation_world_speed_widget"] = 2.0
    fake.checkboxes["wu5_presentation_show_resources"] = False
    fake.checkboxes["wu5_presentation_show_carcasses"] = False
    fake.checkboxes["wu5_presentation_show_trails"] = True
    fake.checkboxes["wu5_presentation_show_labels"] = True
    fake.sliders["wu5_presentation_trail_length"] = 8
    options = world_explorer.render_view_controls(steps)

    assert fake.session_state["wu5_presentation_world_playing"] is True
    assert fake.session_state["wu5_presentation_world_speed"] == 2.0
    assert fake.session_state["wu5_presentation_world_next_advance"] == pytest.approx(10.3)
    assert options == world_explorer.WorldViewOptions(
        show_resources=False,
        show_carcasses=False,
        show_trails=True,
        trail_length=8,
        show_labels=True,
    )
    assert fake.reruns >= 1

    fake.buttons.clear()
    fake.buttons["wu5_presentation_pause"] = True
    world_explorer.render_view_controls(steps)
    assert fake.session_state["wu5_presentation_world_playing"] is False
    assert "wu5_presentation_world_next_advance" not in fake.session_state

    fake.buttons.clear()
    fake.buttons["wu5_presentation_focus_toggle"] = True
    world_explorer.render_view_controls(steps)
    assert world_explorer.presentation_focus_mode() is True
    fake.buttons.clear()
    fake.buttons["wu5_presentation_focus_toggle"] = True
    world_explorer.render_view_controls(steps)
    assert world_explorer.presentation_focus_mode() is False


def test_organism_selection_and_recorded_history_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)

    with pytest.raises(TypeError, match="key_suffix"):
        world_explorer.render_organism_selector((1,), key_suffix="")
    with pytest.raises(TypeError, match="integers"):
        world_explorer.render_organism_selector(cast(Any, (1, "2")), key_suffix="x")

    key = "wu5_presentation_selected_organism_reference"
    fake.session_state[key] = 99
    fake.selections[key] = 2
    assert world_explorer.render_organism_selector((1, 2), key_suffix="reference") == 2
    assert fake.session_state[key] is None

    left = cast(
        tuple[SpatialObservation, ...],
        (
            SimpleNamespace(
                step_index=0,
                organisms=(SimpleNamespace(organism_id=3), SimpleNamespace(organism_id=1)),
            ),
            SimpleNamespace(
                step_index=2,
                organisms=(SimpleNamespace(organism_id=2), SimpleNamespace(organism_id=3)),
            ),
            SimpleNamespace(step_index=4, organisms=()),
        ),
    )
    right = cast(
        tuple[SpatialObservation, ...],
        (SimpleNamespace(step_index=2, organisms=()), SimpleNamespace(step_index=4, organisms=())),
    )
    assert world_explorer.observed_organism_ids(left) == (1, 2, 3)
    assert world_explorer.common_step_indices(left, right) == (2, 4)


def test_playback_advances_only_across_recorded_committed_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _patch_streamlit(monkeypatch)
    clock = {"now": 10.0}
    monkeypatch.setattr(world_explorer.time, "monotonic", lambda: clock["now"])
    steps = (0, 3, 8)
    world_explorer.initialize_world_state(steps)

    world_explorer.advance_playback_if_due(steps)
    assert fake.session_state["wu5_presentation_world_step"] == 0

    fake.session_state["wu5_presentation_world_playing"] = True
    world_explorer.advance_playback_if_due(steps)
    deadline = fake.session_state["wu5_presentation_world_next_advance"]
    assert isinstance(deadline, float)
    assert world_explorer.playback_interval() == pytest.approx(0.6)

    clock["now"] = deadline - 0.1
    world_explorer.advance_playback_if_due(steps)
    assert fake.session_state["wu5_presentation_world_step"] == 0

    clock["now"] = deadline + 0.1
    world_explorer.advance_playback_if_due(steps)
    assert fake.session_state["wu5_presentation_world_step"] == 3

    clock["now"] = cast(float, fake.session_state["wu5_presentation_world_next_advance"]) + 0.1
    world_explorer.advance_playback_if_due(steps)
    assert fake.session_state["wu5_presentation_world_step"] == 8
    assert fake.session_state["wu5_presentation_world_playing"] is False
    assert "wu5_presentation_world_next_advance" not in fake.session_state

    fake.session_state["wu5_presentation_world_playing"] = True
    world_explorer.advance_playback_if_due(steps)
    assert fake.session_state["wu5_presentation_world_playing"] is False
