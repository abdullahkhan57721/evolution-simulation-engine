"""Regression tests for V2 components retained behind the WU1 product shell."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from evo_engine.genetics import MAX_SPEED
from evo_engine.ui.models import SCIENCE_AWARE_MAX_SPEED_SCENARIO

_HARNESS_PATH = Path(__file__).with_name("v2_component_harness.py")
_MAX_SPEED_PREVIEW = "B1/B2 mechanism preview · maximum speed"


def _custom_configuration(app: AppTest) -> AppTest:
    path = next(radio for radio in app.radio if radio.label == "Configuration path")
    path.set_value("Custom experiment")
    return app.run(timeout=30)


def _set_small_valid_configuration(app: AppTest) -> None:
    for label, value in (
        ("Steps", 1),
        ("Founder population", 4),
        ("World width", 4),
        ("World height", 4),
    ):
        next(
            number_input
            for number_input in app.number_input
            if number_input.label == label
        ).set_value(value)


def _run_small_custom_simulation() -> AppTest:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)
    app = _custom_configuration(app)
    _set_small_valid_configuration(app)
    next(button for button in app.button if button.label == "Run simulation").click()
    return app.run(timeout=60)


def _run_max_speed_preview() -> AppTest:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)
    scenario = next(radio for radio in app.radio if radio.label == "Curated scenario")
    scenario.set_value(_MAX_SPEED_PREVIEW)
    app.run(timeout=30)
    next(
        button
        for button in app.button
        if button.label == "Run max-speed mechanism preview"
    ).click()
    return app.run(timeout=60)


def _committed_step_metric(app: AppTest):  # type: ignore[no-untyped-def]
    return next(metric for metric in app.metric if metric.label == "Committed step")


def test_retained_configuration_component_launches() -> None:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Simulation Engine"
    path = next(radio for radio in app.radio if radio.label == "Configuration path")
    assert path.value == "Curated scenario"
    assert "Run flagship evolution demo" in {button.label for button in app.button}
    assert not app.metric
    assert "Edit configuration" not in {button.label for button in app.button}


def test_retained_custom_configuration_preserves_adaptive_visibility() -> None:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)
    app = _custom_configuration(app)

    assert "Mutation probability (%)" in {slider.label for slider in app.slider}
    assert "Maximum mutation step" in {
        number_input.label for number_input in app.number_input
    }
    assert "Recombination probability (%)" in {slider.label for slider in app.slider}

    mutation = next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Enable mutation"
    )
    mutation.set_value(False)
    app.run(timeout=30)

    assert not app.exception
    assert "Mutation probability (%)" not in {slider.label for slider in app.slider}
    assert "Maximum mutation step" not in {
        number_input.label for number_input in app.number_input
    }


def test_retained_configuration_edits_do_not_run_implicitly() -> None:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)
    app = _custom_configuration(app)

    steps = next(
        number_input for number_input in app.number_input if number_input.label == "Steps"
    )
    steps.set_value(1)
    app.run(timeout=30)

    assert not app.exception
    assert not app.metric
    assert "Run simulation" in {button.label for button in app.button}


def test_retained_valid_custom_run_opens_world_workspace() -> None:
    app = _run_small_custom_simulation()

    assert not app.exception
    labels = {metric.label for metric in app.metric}
    assert {
        "Committed step",
        "Population",
        "Resources",
        "Mean energy",
        "Mean body mass",
        "Carcasses",
    } <= labels
    assert _committed_step_metric(app).value == "0"
    assert "Steps" not in {item.label for item in app.number_input}
    assert {
        "Edit configuration",
        "Rerun",
        "New simulation",
        "Next",
        "Play",
    } <= {button.label for button in app.button}
    assert "Committed step" in {slider.label for slider in app.select_slider}
    assert "Selected organism" in {selectbox.label for selectbox in app.selectbox}


def test_retained_next_step_does_not_replace_completed_run() -> None:
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    next(button for button in app.button if button.label == "Next").click()
    app.run(timeout=30)

    assert not app.exception
    assert _committed_step_metric(app).value == "1"
    assert app.session_state["portfolio_dashboard_run"] == completed_run


def test_retained_scrubber_previous_and_selection_share_committed_step() -> None:
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    scrubber = next(
        slider for slider in app.select_slider if slider.label == "Committed step"
    )
    scrubber.set_value(1)
    app.run(timeout=30)
    assert _committed_step_metric(app).value == "1"

    next(button for button in app.button if button.label == "Previous").click()
    app.run(timeout=30)
    assert _committed_step_metric(app).value == "0"

    organism = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Selected organism"
    )
    organism.set_value(0)
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["v2_world_selected_organism"] == 0
    assert app.session_state["portfolio_dashboard_run"] == completed_run
    assert any(markdown.value == "**ID:** 0" for markdown in app.markdown)


def test_retained_playback_never_reruns_simulation() -> None:
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    next(button for button in app.button if button.label == "Play").click()
    app.run(timeout=30)
    assert app.session_state["v2_world_playing"] is True

    speed = next(
        selectbox for selectbox in app.selectbox if selectbox.label == "Playback speed"
    )
    speed.set_value(2.0)
    app.run(timeout=30)
    assert app.session_state["v2_world_speed"] == 2.0
    assert app.session_state["v2_world_playing"] is True

    next(button for button in app.button if button.label == "Pause").click()
    app.run(timeout=30)
    assert app.session_state["v2_world_playing"] is False

    next(button for button in app.button if button.label == "Play").click()
    app.run(timeout=30)
    app.session_state["v2_world_next_advance"] = 0.0
    app.run(timeout=30)

    assert not app.exception
    assert _committed_step_metric(app).value == "1"
    assert app.session_state["v2_world_playing"] is False
    assert app.session_state["portfolio_dashboard_run"] == completed_run


def test_retained_invalid_world_view_state_recovers() -> None:
    app = _run_small_custom_simulation()

    app.session_state["v2_world_step"] = 999
    app.session_state["v2_world_selected_organism"] = 999
    app.run(timeout=30)

    assert not app.exception
    assert _committed_step_metric(app).value == "0"
    assert app.session_state["v2_world_step"] == 0
    assert app.session_state["v2_world_selected_organism"] is None


def test_retained_view_controls_are_presentation_only() -> None:
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    trail_length = next(
        slider
        for slider in app.slider
        if slider.label == "Trail length (committed frames)"
    )
    trail_length.set_value(7)
    app.run(timeout=30)
    assert app.session_state["v2_world_trail_length"] == 7

    next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Resources"
    ).set_value(False)
    next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Carcasses"
    ).set_value(False)
    next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Movement trails"
    ).set_value(False)
    next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Organism labels"
    ).set_value(True)
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["portfolio_dashboard_run"] == completed_run
    assert app.session_state["v2_world_show_resources"] is False
    assert app.session_state["v2_world_show_carcasses"] is False
    assert app.session_state["v2_world_show_trails"] is False
    assert app.session_state["v2_world_show_labels"] is True
    assert app.session_state["v2_world_trail_length"] == 7


def test_retained_featured_scenario_uses_world_workspace() -> None:
    app = AppTest.from_file(str(_HARNESS_PATH)).run(timeout=30)
    next(
        button for button in app.button if button.label == "Run flagship evolution demo"
    ).click()
    app.run(timeout=60)

    assert not app.exception
    assert _committed_step_metric(app).value == "0"
    assert "Edit configuration" in {button.label for button in app.button}
    assert any(
        selectbox.label == "Inspect heritable trait"
        and selectbox.value == "max_intake_rate"
        for selectbox in app.selectbox
    )
    assert any(
        selectbox.label == "Inspect locus" and selectbox.value == "max_intake_rate"
        for selectbox in app.selectbox
    )


def test_retained_max_speed_preview_uses_committed_focal_science() -> None:
    app = _run_max_speed_preview()
    run = app.session_state["portfolio_dashboard_run"]

    assert not app.exception
    assert run.scenario == SCIENCE_AWARE_MAX_SPEED_SCENARIO
    assert run.individual_trait_history
    assert _committed_step_metric(app).value == "0"
    assert any(
        selectbox.label == "Inspect heritable trait" and selectbox.value == MAX_SPEED
        for selectbox in app.selectbox
    )
    assert any(
        selectbox.label == "Inspect locus" and selectbox.value == MAX_SPEED
        for selectbox in app.selectbox
    )
    assert "Run experiment" not in {button.label for button in app.button}
    assert any("B3 owns" in info.value for info in app.info)

    organism = next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Selected organism"
    )
    organism.set_value(0)
    app.run(timeout=30)

    expected = run.individual_trait_history[0].trait_value(0, MAX_SPEED)
    assert not app.exception
    assert any(
        markdown.value == f"**Maximum speed:** {expected}" for markdown in app.markdown
    )


def test_retained_invalid_edit_keeps_last_valid_run() -> None:
    app = _run_small_custom_simulation()

    next(
        button for button in app.button if button.label == "Edit configuration"
    ).click()
    app.run(timeout=30)
    app = _custom_configuration(app)

    for label, value in (
        ("Founder population", 5),
        ("World width", 2),
        ("World height", 2),
    ):
        next(
            number_input
            for number_input in app.number_input
            if number_input.label == label
        ).set_value(value)

    next(button for button in app.button if button.label == "Run simulation").click()
    app.run(timeout=30)

    assert not app.exception
    assert any("must not exceed" in error.value for error in app.error)
    assert "Back to current run" in {button.label for button in app.button}

    next(
        button for button in app.button if button.label == "Back to current run"
    ).click()
    app.run(timeout=30)
    assert _committed_step_metric(app).value == "0"


def test_retained_rerun_resets_view_and_new_clears_run() -> None:
    app = _run_small_custom_simulation()
    next(button for button in app.button if button.label == "Next").click()
    app.run(timeout=30)
    assert _committed_step_metric(app).value == "1"

    next(button for button in app.button if button.label == "Rerun").click()
    app.run(timeout=60)
    assert _committed_step_metric(app).value == "0"

    next(button for button in app.button if button.label == "New simulation").click()
    app.run(timeout=30)
    assert not app.metric
    assert "Configuration path" in {radio.label for radio in app.radio}
    assert "Back to current run" not in {button.label for button in app.button}
    assert "v2_world_step" not in app.session_state
