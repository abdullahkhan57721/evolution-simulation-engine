"""Headless Streamlit interaction tests for the portfolio dashboard."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"


def test_dashboard_launches_without_running_a_simulation() -> None:
    """Test the dashboard loads its initial portfolio/configuration state."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Simulation Engine"
    assert any("Run simulation" in button.label for button in app.button)
    assert app.info


def test_adaptive_controls_hide_inactive_mutation_and_recombination_fields() -> None:
    """Test high-level choices immediately control dependent field visibility."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

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
    assert "Recombination probability (%)" in {slider.label for slider in app.slider}
    assert app.info
    assert not app.metric

    recombination = next(
        checkbox
        for checkbox in app.checkbox
        if checkbox.label == "Enable recombination"
    )
    recombination.set_value(False)
    app.run(timeout=30)

    assert not app.exception
    assert "Recombination probability (%)" not in {
        slider.label for slider in app.slider
    }
    assert app.info
    assert not app.metric


def test_dashboard_configuration_changes_do_not_run_automatically() -> None:
    """Test editing configuration still requires the explicit run action."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    steps = next(
        number_input for number_input in app.number_input if number_input.label == "Steps"
    )
    steps.set_value(1)
    app.run(timeout=30)

    assert not app.exception
    assert app.info
    assert not app.metric


def test_dashboard_can_run_a_small_valid_reference_ecology() -> None:
    """Test one meaningful interaction produces committed result metrics."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

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

    run_button = next(
        button for button in app.button if button.label == "Run simulation"
    )
    run_button.click()
    app.run(timeout=60)

    assert not app.exception
    labels = {metric.label for metric in app.metric}
    assert {
        "Completed steps",
        "Final population",
        "Births",
        "Deaths",
        "Final resources",
    } <= labels
    completed = next(
        metric for metric in app.metric if metric.label == "Completed steps"
    )
    assert completed.value == "1"


def test_dashboard_runs_after_disabling_adaptive_branches() -> None:
    """Test inactive variation branches still produce a valid real simulation."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    for label in ("Enable mutation", "Enable recombination"):
        next(checkbox for checkbox in app.checkbox if checkbox.label == label).set_value(
            False
        )
        app.run(timeout=30)

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

    next(button for button in app.button if button.label == "Run simulation").click()
    app.run(timeout=60)

    assert not app.exception
    completed = next(
        metric for metric in app.metric if metric.label == "Completed steps"
    )
    assert completed.value == "1"


def test_dashboard_surfaces_cross_field_configuration_errors() -> None:
    """Test expected reference validation errors are presented to the user."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

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

    run_button = next(
        button for button in app.button if button.label == "Run simulation"
    )
    run_button.click()
    app.run(timeout=30)

    assert not app.exception
    assert any("must not exceed" in error.value for error in app.error)
