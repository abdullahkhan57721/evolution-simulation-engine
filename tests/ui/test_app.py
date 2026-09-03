"""Headless Streamlit interaction tests for the portfolio dashboard."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path("src/evo_engine/ui/app.py")


def test_dashboard_launches_without_running_a_simulation() -> None:
    """Test the dashboard loads its initial portfolio/configuration state."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Simulation Engine"
    assert any("Run simulation" in button.label for button in app.button)
    assert app.info


def test_dashboard_can_run_a_small_valid_reference_ecology() -> None:
    """Test one meaningful form interaction produces committed result metrics."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    app.number_input[1].set_value(1)
    app.number_input[2].set_value(4)
    app.number_input[3].set_value(4)
    app.number_input[4].set_value(4)
    run_button = next(button for button in app.button if button.label == "Run simulation")
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
    completed = next(metric for metric in app.metric if metric.label == "Completed steps")
    assert completed.value == "1"


def test_dashboard_surfaces_cross_field_configuration_errors() -> None:
    """Test expected reference validation errors are presented to the user."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    app.number_input[2].set_value(5)
    app.number_input[3].set_value(2)
    app.number_input[4].set_value(2)
    run_button = next(button for button in app.button if button.label == "Run simulation")
    run_button.click()
    app.run(timeout=30)

    assert not app.exception
    assert any("must not exceed" in error.value for error in app.error)
