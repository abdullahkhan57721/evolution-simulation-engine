"""Full-window configuration experience for the interactive simulator."""

from __future__ import annotations

from typing import Any

import attrs
import streamlit as st

from evo_engine.ui.models import (
    DashboardRun,
    build_curated_config,
    run_dashboard_flagship_max_intake,
    run_dashboard_reference,
)

_CURATED_PATH = "Curated scenario"
_CUSTOM_PATH = "Custom experiment"
_CONFIGURATION_PATH_KEY = "v2_configuration_path"
_EXPLORATION_MOVEMENT_OPTIONS = {
    "Adjacent random (Moore)": "moore",
    "Orthogonal random (Von Neumann)": "von_neumann",
    "Uniform random within speed limit": "uniform",
    "Gaussian random within speed limit": "gaussian",
}


@attrs.frozen(slots=True, kw_only=True)
class ConfigurationOutcome:
    """Describe one configuration-mode interaction result."""

    completed_run: DashboardRun | None = None
    return_to_run: bool = False


def render_configuration_mode(
    *,
    current_run: DashboardRun | None,
) -> ConfigurationOutcome:
    """Render configuration without displaying the simulation workspace."""
    st.title("Evolution Simulation Engine")
    st.caption(
        "Construct a reproducible biological simulation first. The world workspace "
        "appears only after an explicit run completes successfully."
    )

    if current_run is not None:
        st.info(
            "You are editing configuration. The last completed run remains unchanged "
            "until a new Run action succeeds."
        )
        if st.button("Back to current run"):
            return ConfigurationOutcome(return_to_run=True)

    st.markdown("### Scenario")
    path = st.radio(
        "Configuration path",
        (_CURATED_PATH, _CUSTOM_PATH),
        horizontal=True,
        key=_CONFIGURATION_PATH_KEY,
        help=(
            "Curated scenarios are fixed scientific demonstrations. Custom experiments "
            "expose a restrained set of validated reference-ecology controls."
        ),
    )
    if path == _CURATED_PATH:
        return _render_curated_scenario()
    return _render_custom_experiment()


def _render_curated_scenario() -> ConfigurationOutcome:
    st.subheader("v0.1 flagship evolutionary demonstration")
    st.caption(
        "A fixed-seed illustrative scenario with balanced standing variation in "
        "maximum intake rate, mutation disabled, predation isolated, and renewable "
        "resources."
    )
    st.markdown(
        "**Use this path for the current reproducible portfolio story rather than a "
        "custom parameter study.**"
    )
    if not st.button(
        "Run flagship evolution demo",
        type="primary",
        use_container_width=True,
    ):
        return ConfigurationOutcome()

    try:
        with st.spinner("Running flagship evolutionary demonstration…"):
            candidate = run_dashboard_flagship_max_intake()
    except (TypeError, ValueError) as exc:
        st.error(f"Flagship demonstration could not be run: {exc}")
        return ConfigurationOutcome()
    return ConfigurationOutcome(completed_run=candidate)


def _render_custom_experiment() -> ConfigurationOutcome:
    st.subheader("Custom reference experiment")
    st.caption(
        "Only high-leverage validated controls are exposed on the primary path. "
        "Lower-frequency controls remain progressively disclosed."
    )
    values = _custom_controls()
    if not st.button(
        "Run simulation",
        type="primary",
        use_container_width=True,
    ):
        return ConfigurationOutcome()

    try:
        config = build_curated_config(**values)
        with st.spinner("Running reference ecology…"):
            candidate = run_dashboard_reference(config)
    except (TypeError, ValueError) as exc:
        st.error(f"Simulation configuration could not be run: {exc}")
        return ConfigurationOutcome()
    return ConfigurationOutcome(completed_run=candidate)


def _custom_controls() -> dict[str, Any]:
    values: dict[str, Any] = {}
    with st.expander("Simulation & reproducibility", expanded=True):
        values["seed"] = int(st.number_input("Seed", value=42, step=1))
        values["max_steps"] = int(
            st.number_input("Steps", min_value=1, max_value=500, value=30, step=1)
        )

    with st.expander("Environment", expanded=True):
        width_col, height_col = st.columns(2)
        values["width"] = int(
            width_col.number_input(
                "World width", min_value=1, max_value=50, value=12, step=1
            )
        )
        values["height"] = int(
            height_col.number_input(
                "World height", min_value=1, max_value=50, value=12, step=1
            )
        )
        resource_col, deposit_col = st.columns(2)
        values["resource_generation_amount"] = int(
            resource_col.number_input(
                "Resource units per deposit",
                min_value=1,
                max_value=100,
                value=6,
                step=1,
            )
        )
        values["resource_deposits_per_step"] = int(
            deposit_col.number_input(
                "Resource deposits per step",
                min_value=1,
                max_value=100,
                value=8,
                step=1,
            )
        )

    with st.expander("Founder population", expanded=True):
        population_col, energy_col = st.columns(2)
        values["initial_population"] = int(
            population_col.number_input(
                "Founder population", min_value=1, max_value=500, value=20, step=1
            )
        )
        values["initial_energy"] = int(
            energy_col.number_input(
                "Founder energy", min_value=0, max_value=500, value=30, step=1
            )
        )

    with st.expander("Biological performance", expanded=True):
        movement_label = st.selectbox(
            "Exploration movement pattern",
            tuple(_EXPLORATION_MOVEMENT_OPTIONS),
            index=0,
        )
        movement_kind = _EXPLORATION_MOVEMENT_OPTIONS[movement_label]
        values["exploration_movement_kind"] = movement_kind
        values["gaussian_standard_deviation"] = None
        if movement_kind == "gaussian":
            values["gaussian_standard_deviation"] = int(
                st.number_input(
                    "Gaussian movement standard deviation",
                    min_value=0,
                    max_value=20,
                    value=1,
                    step=1,
                )
            )
        values["growth_rate"] = st.slider(
            "Founder growth rate", min_value=0, max_value=4, value=1, step=1
        )

    _genetics_controls(values)
    with st.expander("Reproduction", expanded=False):
        st.caption(
            "The primary path uses the reference ecology's validated mating, "
            "investment, inheritance, newborn-mass, and placement policies."
        )
    with st.expander("Advanced", expanded=False):
        st.caption(
            "Advanced controls are added only when a concrete scientific use case "
            "justifies exposing another validated model parameter."
        )
    return values


def _genetics_controls(values: dict[str, Any]) -> None:
    with st.expander("Genetics", expanded=True):
        mutation_enabled = st.checkbox("Enable mutation", value=True)
        values["mutation_enabled"] = mutation_enabled
        values["mutation_percent"] = None
        values["mutation_max_change"] = None
        if mutation_enabled:
            values["mutation_percent"] = st.slider(
                "Mutation probability (%)", min_value=0, max_value=100, value=1
            )
            values["mutation_max_change"] = int(
                st.number_input(
                    "Maximum mutation step",
                    min_value=0,
                    max_value=20,
                    value=1,
                    step=1,
                )
            )

        recombination_enabled = st.checkbox("Enable recombination", value=True)
        values["recombination_enabled"] = recombination_enabled
        values["recombination_percent"] = None
        if recombination_enabled:
            values["recombination_percent"] = st.slider(
                "Recombination probability (%)",
                min_value=0,
                max_value=100,
                value=50,
            )
