"""Headless Streamlit tests for the WU1 Workbench application shell."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from evo_engine.workbench import (
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"
_STUDY_SECTIONS = [
    "Simulation",
    "Evidence",
    "Experiment",
    "Results",
    "Presentation",
]


def _launch() -> AppTest:
    return AppTest.from_file(str(_APP_PATH)).run(timeout=30)


def _open_new_study(app: AppTest) -> AppTest:
    next(button for button in app.button if button.label == "New Study").click()
    return app.run(timeout=30)


def _start(app: AppTest, label: str) -> AppTest:
    next(button for button in app.button if button.label == label).click()
    return app.run(timeout=30)


def test_app_launches_at_workbench_home() -> None:
    app = _launch()

    assert not app.exception
    assert app.title[0].value == "Evolution Experiment Workbench"
    assert {"New Study", "Open Study"} <= {button.label for button in app.button}
    assert "Configuration path" not in {radio.label for radio in app.radio}
    assert not app.metric
    assert "wu1_active_artifact" not in app.session_state


def test_home_exposes_curated_controlled_and_custom_families() -> None:
    app = _launch()
    markdown = {item.value for item in app.markdown}

    assert "### Curated" in markdown
    assert "### Controlled" in markdown
    assert "### Custom" in markdown
    assert any("B3 Flagship" in item.value for item in app.markdown)
    assert any("Controlled Locomotion" in item.value for item in app.markdown)
    assert any("Reference Ecology" in item.value for item in app.markdown)


def test_new_study_exposes_only_supported_wu1_entry_paths() -> None:
    app = _open_new_study(_launch())
    labels = {button.label for button in app.button}

    assert not app.exception
    assert {
        "Start B3 Flagship",
        "Start controlled run",
        "Start max-speed sweep",
        "Start environment comparison",
        "Start Reference Ecology",
    } <= labels
    assert not any("radius 2" in label.lower() for label in labels)
    assert not any("extension" in label.lower() for label in labels)


def test_b3_entry_opens_common_study_shell_with_run_as_action() -> None:
    app = _start(_open_new_study(_launch()), "Start B3 Flagship")

    assert not app.exception
    assert app.title[0].value == "B3 Flagship"
    assert isinstance(app.session_state["wu1_active_artifact"], B3StudyRevision)
    navigation = next(radio for radio in app.radio if radio.label == "Study section")
    assert navigation.options == _STUDY_SECTIONS
    assert navigation.value == "Simulation"
    assert {"← Home", "Run", "More"} <= {button.label for button in app.button}
    run = next(button for button in app.button if button.label == "Run")
    assert run.disabled is True


def test_all_new_study_families_enter_the_same_shell() -> None:
    cases = (
        ("Start controlled run", StudyRevision),
        ("Start max-speed sweep", MaxSpeedSweepDefinition),
        ("Start environment comparison", EnvironmentSelectionComparisonDefinition),
        ("Start Reference Ecology", ReferenceStudyRevision),
    )

    for label, artifact_type in cases:
        app = _start(_open_new_study(_launch()), label)

        assert not app.exception
        assert isinstance(app.session_state["wu1_active_artifact"], artifact_type)
        navigation = next(radio for radio in app.radio if radio.label == "Study section")
        assert navigation.options == _STUDY_SECTIONS
        assert "Run" in {button.label for button in app.button}
        assert "Configuration path" not in {radio.label for radio in app.radio}


def test_study_navigation_switches_sections_without_replacing_artifact() -> None:
    app = _start(_open_new_study(_launch()), "Start controlled run")
    artifact = app.session_state["wu1_active_artifact"]
    navigation = next(radio for radio in app.radio if radio.label == "Study section")

    navigation.set_value("Results")
    app.run(timeout=30)

    assert not app.exception
    assert app.session_state["wu1_active_artifact"] == artifact
    assert any(header.value == "Results" for header in app.header)
    assert any("No completed run payload" in info.value for info in app.info)


def test_returning_home_clears_active_study_and_stale_result_state() -> None:
    app = _start(_open_new_study(_launch()), "Start B3 Flagship")
    app.session_state["wu1_current_result"] = "stale-result"
    app.session_state["portfolio_dashboard_run"] = "legacy-run"

    next(button for button in app.button if button.label == "← Home").click()
    app.run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Evolution Experiment Workbench"
    assert "wu1_active_artifact" not in app.session_state
    assert "wu1_current_result" not in app.session_state
    assert "portfolio_dashboard_run" not in app.session_state


def test_starting_new_study_does_not_leak_prior_artifact_state() -> None:
    app = _start(_open_new_study(_launch()), "Start B3 Flagship")
    old_artifact = app.session_state["wu1_active_artifact"]

    next(button for button in app.button if button.label == "← Home").click()
    app.run(timeout=30)
    app = _open_new_study(app)
    app = _start(app, "Start controlled run")

    new_artifact = app.session_state["wu1_active_artifact"]
    assert not app.exception
    assert isinstance(new_artifact, StudyRevision)
    assert new_artifact != old_artifact
    assert "wu1_current_result" not in app.session_state
