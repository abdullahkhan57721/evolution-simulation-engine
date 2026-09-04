"""Headless Streamlit interaction tests for the interactive simulator."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from evo_engine.genetics import MAX_SPEED
from evo_engine.ui.models import SCIENCE_AWARE_MAX_SPEED_SCENARIO

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"
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
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
    app = _custom_configuration(app)
    _set_small_valid_configuration(app)
    next(button for button in app.button if button.label == "Run simulation").click()
    return app.run(timeout=60)


def _run_max_speed_preview() -> AppTest:
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
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


def test_app_launches_in_full_configuration_mode() -> None:
    """Test initial launch shows configuration without result workspace state."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Simulation Engine"
    path = next(radio for radio in app.radio if radio.label == "Configuration path")
    assert path.value == "Curated scenario"
    assert "Run flagship evolution demo" in {button.label for button in app.button}
    assert not app.metric
    assert "Edit configuration" not in {button.label for button in app.button}


def test_custom_path_preserves_adaptive_configuration_visibility() -> None:
    """Test high-level choices control dependent fields before any run."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
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


def test_configuration_edits_do_not_run_implicitly() -> None:
    """Test changing simulation configuration still requires explicit Run."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
    app = _custom_configuration(app)

    steps = next(
        number_input
        for number_input in app.number_input
        if number_input.label == "Steps"
    )
    steps.set_value(1)
    app.run(timeout=30)

    assert not app.exception
    assert not app.metric
    assert "Run simulation" in {button.label for button in app.button}


def test_valid_custom_run_transitions_to_selected_step_world_workspace() -> None:
    """Test a successful run opens the committed founder frame first."""
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


def test_next_step_updates_world_context_without_replacing_completed_run() -> None:
    """Test timeline navigation changes presentation state only."""
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    next(button for button in app.button if button.label == "Next").click()
    app.run(timeout=30)

    assert not app.exception
    assert _committed_step_metric(app).value == "1"
    assert app.session_state["portfolio_dashboard_run"] == completed_run


def test_scrubber_previous_and_selection_share_one_committed_step() -> None:
    """Test timeline and inspector focus stay in application presentation state."""
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


def test_playback_speed_pause_and_due_advance_never_rerun_simulation() -> None:
    """Test fragment playback advances committed presentation frames only."""
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


def test_invalid_world_view_state_recovers_to_recorded_values() -> None:
    """Test stale display state cannot select nonexistent scientific records."""
    app = _run_small_custom_simulation()

    app.session_state["v2_world_step"] = 999
    app.session_state["v2_world_selected_organism"] = 999
    app.run(timeout=30)

    assert not app.exception
    assert _committed_step_metric(app).value == "0"
    assert app.session_state["v2_world_step"] == 0
    assert app.session_state["v2_world_selected_organism"] is None


def test_view_controls_do_not_replace_completed_run() -> None:
    """Test environmental visibility and labels are view-only state."""
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


def test_featured_scenario_transitions_to_same_workspace() -> None:
    """Test the current curated scenario uses the V2 interactive workspace."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
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


def test_max_speed_preview_uses_committed_focal_science_without_b3_experiment() -> None:
    """Test the preview exposes focal evidence but does not fabricate B3 comparison."""
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


def test_edit_configuration_keeps_completed_run_until_new_run_succeeds() -> None:
    """Test an invalid edit cannot destroy the last valid immutable result."""
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


def test_rerun_resets_world_presentation_and_new_simulation_clears_run() -> None:
    """Test completed-run replacement resets timeline while New removes the run."""
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
