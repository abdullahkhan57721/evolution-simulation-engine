"""Headless Streamlit interaction tests for the interactive simulator."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"


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


def test_view_controls_do_not_replace_completed_run() -> None:
    """Test resource visibility is display state rather than simulation state."""
    app = _run_small_custom_simulation()
    completed_run = app.session_state["portfolio_dashboard_run"]

    resource_toggle = next(
        checkbox for checkbox in app.checkbox if checkbox.label == "Resources"
    )
    resource_toggle.set_value(False)
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["portfolio_dashboard_run"] == completed_run
    assert app.session_state["v2_world_show_resources"] is False


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
