"""Regression tests for the retired V2 top-level configuration shell."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"


def test_workbench_shell_does_not_leak_legacy_movement_configuration() -> None:
    """WU1 replaces the old Configuration path; movement authoring returns in WU2."""
    app = AppTest.from_file(str(_APP_PATH)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Experiment Workbench"
    assert "Configuration path" not in {radio.label for radio in app.radio}
    assert "Exploration movement pattern" not in {
        selectbox.label for selectbox in app.selectbox
    }
    assert "Run simulation" not in {button.label for button in app.button}
