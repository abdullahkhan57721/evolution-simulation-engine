"""Streamlit entry point for the interactive evolution simulator."""

from __future__ import annotations

import streamlit as st

from evo_engine.ui.configuration import render_configuration_mode
from evo_engine.ui.models import (
    FLAGSHIP_MAX_INTAKE_SCENARIO,
    DashboardRun,
    run_dashboard_flagship_max_intake,
    run_dashboard_reference,
)
from evo_engine.ui.workspace import render_simulation_workspace

_RUN_KEY = "portfolio_dashboard_run"
_EXPERIMENT_KEY = "portfolio_experiment_result"
_MODE_KEY = "v2_application_mode"
_CONFIGURATION_MODE = "configuration"
_WORKSPACE_MODE = "workspace"


def main() -> None:
    """Render the two-mode interactive evolution-simulator experience."""
    st.set_page_config(
        page_title="Evolution Simulation Engine",
        page_icon="🧬",
        layout="wide",
    )
    _initialize_mode()

    if st.session_state[_MODE_KEY] == _CONFIGURATION_MODE:
        _configuration_mode()
        return

    run = st.session_state.get(_RUN_KEY)
    if not isinstance(run, DashboardRun):
        st.session_state[_MODE_KEY] = _CONFIGURATION_MODE
        _configuration_mode()
        return

    _workspace_mode(run)


def _initialize_mode() -> None:
    mode = st.session_state.get(_MODE_KEY)
    if mode in {_CONFIGURATION_MODE, _WORKSPACE_MODE}:
        return
    run = st.session_state.get(_RUN_KEY)
    st.session_state[_MODE_KEY] = (
        _WORKSPACE_MODE if isinstance(run, DashboardRun) else _CONFIGURATION_MODE
    )


def _configuration_mode() -> None:
    current_run = st.session_state.get(_RUN_KEY)
    current = current_run if isinstance(current_run, DashboardRun) else None
    outcome = render_configuration_mode(current_run=current)

    if outcome.return_to_run:
        st.session_state[_MODE_KEY] = _WORKSPACE_MODE
        st.rerun()
    if outcome.completed_run is not None:
        _store_completed_run(outcome.completed_run)
        st.rerun()


def _workspace_mode(run: DashboardRun) -> None:
    action = render_simulation_workspace(run, experiment_key=_EXPERIMENT_KEY)
    if action == "edit":
        st.session_state[_MODE_KEY] = _CONFIGURATION_MODE
        st.rerun()
    if action == "rerun":
        _rerun(run)
    if action == "new":
        st.session_state.pop(_RUN_KEY, None)
        st.session_state.pop(_EXPERIMENT_KEY, None)
        st.session_state[_MODE_KEY] = _CONFIGURATION_MODE
        st.rerun()


def _rerun(run: DashboardRun) -> None:
    try:
        with st.spinner("Rerunning completed configuration…"):
            if run.scenario == FLAGSHIP_MAX_INTAKE_SCENARIO:
                candidate = run_dashboard_flagship_max_intake()
            else:
                candidate = run_dashboard_reference(run.config)
    except (TypeError, ValueError) as exc:
        st.error(f"Simulation could not be rerun: {exc}")
        return

    _store_completed_run(candidate)
    st.rerun()


def _store_completed_run(run: DashboardRun) -> None:
    st.session_state[_RUN_KEY] = run
    st.session_state.pop(_EXPERIMENT_KEY, None)
    st.session_state[_MODE_KEY] = _WORKSPACE_MODE


if __name__ == "__main__":
    main()
