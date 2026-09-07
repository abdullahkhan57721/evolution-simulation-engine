"""Headless Streamlit coverage for WU2 Simulation authoring flows."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from evo_engine.workbench import B3StudyRevision, ReferenceStudyRevision, StudyRevision

_APP_PATH = Path(__file__).parents[2] / "src" / "evo_engine" / "ui" / "app.py"


def _launch() -> AppTest:
    return AppTest.from_file(str(_APP_PATH)).run(timeout=30)


def _open_new_study(app: AppTest) -> AppTest:
    next(button for button in app.button if button.label == "New Study").click()
    return app.run(timeout=30)


def _start(app: AppTest, label: str) -> AppTest:
    next(button for button in app.button if button.label == label).click()
    return app.run(timeout=30)


def test_controlled_simulation_edit_saves_new_child_revision() -> None:
    app = _start(_open_new_study(_launch()), "Start controlled run")
    parent = app.session_state["wu1_active_artifact"]
    assert isinstance(parent, StudyRevision)

    speed = next(item for item in app.number_input if item.label == "Maximum speed")
    speed.set_value(4 if speed.value != 4 else 3)
    app.run(timeout=30)

    save = next(button for button in app.button if button.label == "Save new revision")
    assert save.disabled is False
    save.click()
    app.run(timeout=30)

    child = app.session_state["wu1_active_artifact"]
    assert isinstance(child, StudyRevision)
    assert child.revision_id != parent.revision_id
    assert child.parent_revision_id == parent.revision_id
    assert app.session_state["wu2_diff_parent_artifact"] == parent
    assert any(
        "Changes from parent" in item.value
        for item in (*app.header, *app.subheader, *app.markdown)
    )


def test_reference_guided_and_advanced_are_disclosure_levels_of_same_study() -> None:
    app = _start(_open_new_study(_launch()), "Start Reference Ecology")
    parent = app.session_state["wu1_active_artifact"]
    assert isinstance(parent, ReferenceStudyRevision)

    disclosure = next(radio for radio in app.radio if radio.label == "Disclosure")
    assert disclosure.value == "Guided"
    assert "Renewable resource amount" not in {item.label for item in app.number_input}

    disclosure.set_value("Advanced")
    app.run(timeout=30)

    current = app.session_state["wu1_active_artifact"]
    assert current == parent
    assert "Renewable resource amount" in {item.label for item in app.number_input}
    assert "Recombination probability (ppm)" in {
        item.label for item in app.number_input
    }
    assert not any(
        item.label == "Expert" for item in (*app.radio, *app.selectbox, *app.button)
    )


def test_reference_hidden_gaussian_value_does_not_survive_saved_science() -> None:
    app = _start(_open_new_study(_launch()), "Start Reference Ecology")
    disclosure = next(radio for radio in app.radio if radio.label == "Disclosure")
    disclosure.set_value("Advanced")
    app.run(timeout=30)

    movement = next(
        item for item in app.selectbox if item.label == "Exploration movement"
    )
    movement.set_value("gaussian")
    app.run(timeout=30)

    gaussian = next(
        item for item in app.number_input if item.label == "Gaussian standard deviation"
    )
    gaussian.set_value(3)
    app.run(timeout=30)

    movement = next(
        item for item in app.selectbox if item.label == "Exploration movement"
    )
    movement.set_value("moore")
    app.run(timeout=30)
    assert "Gaussian standard deviation" not in {
        item.label for item in app.number_input
    }

    speed = next(
        item for item in app.number_input if item.label == "Founder maximum speed"
    )
    speed.set_value(4 if speed.value != 4 else 3)
    app.run(timeout=30)
    save = next(button for button in app.button if button.label == "Save new revision")
    assert save.disabled is False
    save.click()
    app.run(timeout=30)

    child = app.session_state["wu1_active_artifact"]
    assert isinstance(child, ReferenceStudyRevision)
    assert child.intent.gaussian_standard_deviation is None


def test_b3_radius_sensitivity_is_explicit_fork_with_identity_loss() -> None:
    app = _start(_open_new_study(_launch()), "Start B3 Flagship")
    parent = app.session_state["wu1_active_artifact"]
    assert isinstance(parent, B3StudyRevision)
    assert parent.scenario_identity is not None

    fork = next(
        button
        for button in app.button
        if button.label == "Fork radius-sensitivity Study"
    )
    fork.click()
    app.run(timeout=30)

    child = app.session_state["wu1_active_artifact"]
    assert isinstance(child, B3StudyRevision)
    assert child.parent_revision_id == parent.revision_id
    assert child.scenario_origin == parent.scenario_origin
    assert child.scenario_identity is None
    assert not any(
        button.label == "Fork radius-sensitivity Study" for button in app.button
    )
    assert any("not the validated radius-1" in warning.value for warning in app.warning)
