"""Headless Streamlit tests for adaptive exploration-movement controls."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from evo_engine.presets import ReferenceGaussianMovement, ReferenceUniformMovement
from evo_engine.ui.models import DashboardRun

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"


def _enter_custom_configuration(app: AppTest) -> AppTest:
    path = next(radio for radio in app.radio if radio.label == "Configuration path")
    path.set_value("Custom experiment")
    return app.run(timeout=30)


def _movement_selectbox(app: AppTest):  # type: ignore[no-untyped-def]
    return next(
        selectbox
        for selectbox in app.selectbox
        if selectbox.label == "Exploration movement pattern"
    )


def _set_small_world(app: AppTest) -> None:
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


def test_gaussian_only_control_progressively_reveals_and_hides() -> None:
    """Test the strategy selector controls Gaussian-only field visibility."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
    app = _enter_custom_configuration(app)

    assert not app.exception
    assert _movement_selectbox(app).value == "Adjacent random (Moore)"
    assert "Gaussian movement standard deviation" not in {
        number_input.label for number_input in app.number_input
    }

    _movement_selectbox(app).set_value("Gaussian random within speed limit")
    app.run(timeout=30)

    assert not app.exception
    assert "Gaussian movement standard deviation" in {
        number_input.label for number_input in app.number_input
    }
    assert not app.metric

    next(
        number_input
        for number_input in app.number_input
        if number_input.label == "Gaussian movement standard deviation"
    ).set_value(7)
    app.run(timeout=30)

    _movement_selectbox(app).set_value("Uniform random within speed limit")
    app.run(timeout=30)

    assert not app.exception
    assert "Gaussian movement standard deviation" not in {
        number_input.label for number_input in app.number_input
    }
    assert not app.metric


def test_switching_from_gaussian_runs_non_gaussian_typed_config() -> None:
    """Test a hidden Gaussian value cannot affect the explicit run config."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
    app = _enter_custom_configuration(app)

    _movement_selectbox(app).set_value("Gaussian random within speed limit")
    app.run(timeout=30)
    next(
        number_input
        for number_input in app.number_input
        if number_input.label == "Gaussian movement standard deviation"
    ).set_value(7)
    app.run(timeout=30)

    _movement_selectbox(app).set_value("Uniform random within speed limit")
    app.run(timeout=30)
    _set_small_world(app)

    next(button for button in app.button if button.label == "Run simulation").click()
    app.run(timeout=60)

    assert not app.exception
    run = app.session_state["portfolio_dashboard_run"]
    assert isinstance(run, DashboardRun)
    assert isinstance(run.config.exploration_movement, ReferenceUniformMovement)
    assert not hasattr(run.config.exploration_movement, "standard_deviation")


def test_gaussian_run_commits_selected_typed_variant() -> None:
    """Test an active Gaussian value reaches the committed DashboardRun config."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)
    app = _enter_custom_configuration(app)

    _movement_selectbox(app).set_value("Gaussian random within speed limit")
    app.run(timeout=30)
    next(
        number_input
        for number_input in app.number_input
        if number_input.label == "Gaussian movement standard deviation"
    ).set_value(3)
    app.run(timeout=30)
    _set_small_world(app)

    next(button for button in app.button if button.label == "Run simulation").click()
    app.run(timeout=60)

    assert not app.exception
    run = app.session_state["portfolio_dashboard_run"]
    assert isinstance(run, DashboardRun)
    assert run.config.exploration_movement == ReferenceGaussianMovement(
        standard_deviation=3
    )
