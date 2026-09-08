"""WU3 Experiment-page rendering for the concrete Workbench experiment patterns."""

from __future__ import annotations

import streamlit as st

from evo_engine.ui.experiment_authoring import (
    b3_case_counts,
    e4_counterbalance_label,
    environment_run_rows,
    max_speed_run_rows,
    parse_integer_sequence,
    update_environment_selection_comparison,
    update_max_speed_sweep,
)
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench import (
    SUPPORTED_MAX_SPEED_MAXIMUM,
    SUPPORTED_MAX_SPEED_MINIMUM,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)

_DRAFT_OWNER_KEY = "wu3_experiment_draft_owner"
_DRAFT_DEFINITION_KEY = "wu3_experiment_draft_definition"
_DRAFT_ERROR_KEY = "wu3_experiment_draft_error"


def clear_experiment_authoring_state() -> None:
    """Clear transient WU3 Experiment controls when Study context changes."""
    for key in tuple(st.session_state):
        if str(key).startswith("wu3_experiment_"):
            st.session_state.pop(key, None)


def pending_experiment_definition(
    artifact: ConcreteWorkbenchArtifact,
) -> MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition | None:
    """Return a valid pending concrete definition belonging to the active artifact."""
    if not isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        return None
    if st.session_state.get(_DRAFT_OWNER_KEY) != artifact.to_json():
        return None
    candidate = st.session_state.get(_DRAFT_DEFINITION_KEY)
    if isinstance(artifact, MaxSpeedSweepDefinition) and isinstance(
        candidate, MaxSpeedSweepDefinition
    ):
        return candidate
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition) and isinstance(
        candidate, EnvironmentSelectionComparisonDefinition
    ):
        return candidate
    return None


def pending_experiment_error(artifact: ConcreteWorkbenchArtifact) -> str | None:
    """Return the current concrete-definition validation error, if any."""
    if st.session_state.get(_DRAFT_OWNER_KEY) != _owner_value(artifact):
        return None
    value = st.session_state.get(_DRAFT_ERROR_KEY)
    return value if type(value) is str and value else None


def render_experiment_page(
    artifact: ConcreteWorkbenchArtifact,
) -> MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition | None:
    """Render the concrete Experiment surface and return an applied definition."""
    st.header("Experiment")
    if isinstance(artifact, StudyRevision):
        st.info(
            "No multi-treatment experiment configured. This Study represents one "
            "controlled simulation."
        )
        return None
    if isinstance(artifact, ReferenceStudyRevision):
        st.info(
            "Reference Ecology currently has no generic controlled-experiment "
            "definition in the Workbench. WU3 does not invent one."
        )
        return None
    if isinstance(artifact, MaxSpeedSweepDefinition):
        return _render_max_speed_sweep(artifact)
    if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
        return _render_environment_selection(artifact)
    if isinstance(artifact, B3StudyRevision):
        _render_b3_design(artifact)
        return None
    raise TypeError("Unsupported Workbench artifact for Experiment rendering.")


def _render_max_speed_sweep(
    definition: MaxSpeedSweepDefinition,
) -> MaxSpeedSweepDefinition | None:
    st.subheader("Maximum-speed sweep")
    st.markdown("**Primary factor · Maximum speed**")
    st.caption(
        "Maximum speed is supplied by the Experiment. Replicate seed is assigned by "
        "the replicate design; neither is an ordinary base-Simulation control."
    )
    st.write(
        f"Base resource geography: **{_humanize(definition.base_intent.resource_geography)}**"
    )

    current = pending_experiment_definition(definition)
    if not isinstance(current, MaxSpeedSweepDefinition):
        current = definition
    supported_levels = tuple(
        range(SUPPORTED_MAX_SPEED_MINIMUM, SUPPORTED_MAX_SPEED_MAXIMUM + 1)
    )
    levels = tuple(
        st.multiselect(
            "Maximum-speed levels",
            supported_levels,
            default=list(current.levels),
            key="wu3_experiment_e3_levels",
        )
    )
    seed_text = st.text_input(
        "Replicate seeds",
        value=_integer_text(current.seeds),
        key="wu3_experiment_e3_seeds",
        help="Comma-separated integer seeds. Seed is a replicate identity, not a factor.",
    )
    try:
        seeds = parse_integer_sequence(seed_text, name="Replicate seeds")
        candidate = update_max_speed_sweep(definition, levels=levels, seeds=seeds)
        rows = max_speed_run_rows(candidate)
    except (TypeError, ValueError) as exc:
        _store_invalid(definition, str(exc))
        st.error(str(exc))
        return None

    _store_candidate(definition, candidate)
    st.markdown(f"**Total simulations · {len(rows)}**")
    st.dataframe(
        [
            {
                "Maximum speed": row.maximum_speed,
                "Seed": row.seed,
                "Resource geography": _humanize(row.resource_geography),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    if candidate == definition:
        st.caption("Experiment design matches the current immutable definition.")
        return None
    if st.button("Apply experiment design", type="primary"):
        return candidate
    return None


def _render_environment_selection(
    definition: EnvironmentSelectionComparisonDefinition,
) -> EnvironmentSelectionComparisonDefinition | None:
    st.subheader("Environment-selection comparison")
    st.markdown("**Primary factor · Resource geography**")
    control, treatment = st.columns(2)
    with control:
        st.markdown("**Control**")
        st.write(_humanize(definition.control_environment))
    with treatment:
        st.markdown("**Treatment**")
        st.write(_humanize(definition.treatment_environment))
    st.write(
        "Standing focal composition: **"
        + ", ".join(str(value) for value in definition.focal_speeds)
        + "**"
    )
    st.caption(e4_counterbalance_label())
    st.caption(
        "Primary factor, factor level, control/treatment role, replicate seed, and "
        "founder-order counterbalance are distinct parts of the design."
    )

    current = pending_experiment_definition(definition)
    if not isinstance(current, EnvironmentSelectionComparisonDefinition):
        current = definition
    seed_text = st.text_input(
        "Replicate seeds",
        value=_integer_text(current.seeds),
        key="wu3_experiment_e4_seeds",
        help="Comma-separated integer seeds shared across matched control/treatment pairs.",
    )
    try:
        seeds = parse_integer_sequence(seed_text, name="Replicate seeds")
        candidate = update_environment_selection_comparison(definition, seeds=seeds)
        rows = environment_run_rows(candidate)
    except (TypeError, ValueError) as exc:
        _store_invalid(definition, str(exc))
        st.error(str(exc))
        return None

    _store_candidate(definition, candidate)
    st.markdown(f"**Total simulations · {len(rows)}**")
    st.caption("Rows sharing a seed form the matched control/treatment block.")
    st.dataframe(
        [
            {
                "Seed": row.seed,
                "Role": row.role.title(),
                "Environment": _humanize(row.environment),
                "Standing focal composition": _integer_text(
                    row.standing_focal_composition
                ),
                "Founder order": _integer_text(row.founder_speed_order),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    if candidate == definition:
        st.caption("Experiment design matches the current immutable definition.")
        return None
    if st.button("Apply experiment design", type="primary"):
        return candidate
    return None


def _render_b3_design(revision: B3StudyRevision) -> None:
    counts = b3_case_counts(revision)
    st.subheader("Curated B3 experimental design")
    st.info("The B3 experimental design is frozen and read-only.")
    st.markdown("**Primary confirmation**")
    st.write(
        f"{counts.confirmation_pairs} matched same-seed control/treatment pair(s)."
    )
    st.markdown("**Radius sensitivity**")
    if counts.radius_sensitivity_runs:
        st.write(f"{counts.radius_sensitivity_runs} broader-patch sensitivity run(s).")
    else:
        st.write("No separate radius-sensitivity runs in this B3-derived revision.")
    st.markdown("**Counterbalance**")
    st.write(
        f"{counts.counterbalanced_pairs} matched founder-assignment counterbalance pair(s)."
    )
    st.markdown(f"**Total simulations · {counts.total_simulations}**")
    st.warning(
        "Same-seed B3 control/treatment pairs are blocked or matched by seed. They "
        "are not guaranteed to remain lockstep-identical after treatment divergence."
    )


def _store_candidate(
    owner: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
    candidate: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
) -> None:
    st.session_state[_DRAFT_OWNER_KEY] = owner.to_json()
    st.session_state[_DRAFT_DEFINITION_KEY] = candidate
    st.session_state.pop(_DRAFT_ERROR_KEY, None)


def _store_invalid(
    owner: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
    message: str,
) -> None:
    st.session_state[_DRAFT_OWNER_KEY] = owner.to_json()
    st.session_state.pop(_DRAFT_DEFINITION_KEY, None)
    st.session_state[_DRAFT_ERROR_KEY] = message


def _owner_value(artifact: ConcreteWorkbenchArtifact) -> str | None:
    if isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        return artifact.to_json()
    return None


def _integer_text(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = [
    "clear_experiment_authoring_state",
    "pending_experiment_definition",
    "pending_experiment_error",
    "render_experiment_page",
]
