"""Streamlit entry point for the Evolution Experiment Workbench."""

from __future__ import annotations

import uuid

import streamlit as st

from evo_engine.ui.evidence_authoring import evidence_advisories_for_artifact
from evo_engine.ui.evidence_page import (
    clear_evidence_authoring_state,
    pending_evidence_plan,
    render_evidence_page,
)
from evo_engine.ui.experiment_page import (
    clear_experiment_authoring_state,
    pending_experiment_error,
    render_experiment_page,
)
from evo_engine.ui.results_page import render_results_page
from evo_engine.ui.run_binding import bind_pending_scientific_state, effective_readiness
from evo_engine.ui.run_execution import execute_artifact
from evo_engine.ui.run_page import render_run_plan
from evo_engine.ui.simulation_page import (
    clear_simulation_authoring_state,
    render_simulation_page,
)
from evo_engine.ui.study_shell import (
    ConcreteWorkbenchArtifact,
    artifact_download_name,
    artifact_revision_id,
    artifact_title,
    artifact_type_label,
    is_concrete_artifact,
    load_concrete_artifact,
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
    serialize_concrete_artifact,
)
from evo_engine.workbench import (
    EnvironmentSelectionComparisonDefinition,
    EvidenceAdvisory,
    IncompatibleManifestError,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    WorkbenchNotReadyError,
)

_ROUTE_KEY = "wu1_route"
_ACTIVE_ARTIFACT_KEY = "wu1_active_artifact"
_SECTION_KEY = "wu1_study_section"
_RESULT_KEY = "wu1_current_result"
_DIFF_PARENT_KEY = "wu2_diff_parent_artifact"
_RUN_PLAN_KEY = "wu3_run_plan_open"
_RUN_BINDING_NOTICE_KEY = "wu3_run_binding_notice"
_RUN_FAILURE_KEY = "wu3_run_failure"

_HOME = "home"
_NEW = "new"
_OPEN = "open"
_STUDY = "study"
_ROUTES = {_HOME, _NEW, _OPEN, _STUDY}

_STUDY_SECTIONS = (
    "Simulation",
    "Evidence",
    "Experiment",
    "Results",
    "Presentation",
)

_LEGACY_KEYS = (
    "portfolio_dashboard_run",
    "portfolio_experiment_result",
    "v2_application_mode",
)


def main() -> None:
    """Render the Home → Study Workbench application shell."""
    st.set_page_config(
        page_title="Evolution Experiment Workbench",
        page_icon="🧬",
        layout="wide",
    )
    _initialize_router()

    route = st.session_state[_ROUTE_KEY]
    if route == _HOME:
        _render_home()
    elif route == _NEW:
        _render_new_study()
    elif route == _OPEN:
        _render_open_study()
    else:
        _render_study_shell()


def _initialize_router() -> None:
    route = st.session_state.get(_ROUTE_KEY)
    if route not in _ROUTES:
        st.session_state[_ROUTE_KEY] = _HOME
        _clear_active_context()
        return
    if route == _STUDY and not _has_active_artifact():
        st.session_state[_ROUTE_KEY] = _HOME
        _clear_active_context()


def _render_home() -> None:
    st.title("Evolution Experiment Workbench")
    st.write(
        "Build reproducible evolutionary simulations, choose evidence, design "
        "controlled experiments, inspect results, and configure presentation."
    )

    new_column, open_column = st.columns(2)
    with new_column:
        if st.button("New Study", type="primary", use_container_width=True):
            _clear_active_context()
            st.session_state[_ROUTE_KEY] = _NEW
            st.rerun()
    with open_column:
        if st.button("Open Study", use_container_width=True):
            _clear_active_context()
            st.session_state[_ROUTE_KEY] = _OPEN
            st.rerun()

    st.divider()
    st.subheader("Supported Study families")
    curated, controlled, custom = st.columns(3)
    with curated:
        st.markdown("### Curated")
        st.write("B3 Flagship")
    with controlled:
        st.markdown("### Controlled")
        st.write("Controlled Locomotion")
        st.caption("Single run · Max-speed sweep · Environment comparison")
    with custom:
        st.markdown("### Custom")
        st.write("Reference Ecology")
        st.caption("Bounded Workbench-supported composition")


def _render_new_study() -> None:
    _render_page_back("Home")
    st.title("New Study")
    st.caption(
        "Open one supported concrete Study family, then author its scientific "
        "meaning inside the persistent Study shell."
    )

    st.subheader("Curated")
    st.write("**B3 Flagship** — canonical validated radius-1 starting Study.")
    if st.button("Start B3 Flagship", type="primary"):
        _activate_artifact(new_b3_flagship(revision_id=_new_revision_id("b3")))
        st.rerun()

    st.divider()
    st.subheader("Controlled")
    controlled_run, speed_sweep, environment = st.columns(3)
    with controlled_run:
        st.write("**Single controlled run**")
        if st.button("Start controlled run", use_container_width=True):
            _activate_artifact(
                new_controlled_run(revision_id=_new_revision_id("controlled"))
            )
            st.rerun()
    with speed_sweep:
        st.write("**Max-speed sweep**")
        if st.button("Start max-speed sweep", use_container_width=True):
            _activate_artifact(new_max_speed_sweep())
            st.rerun()
    with environment:
        st.write("**Environment-selection comparison**")
        if st.button("Start environment comparison", use_container_width=True):
            _activate_artifact(new_environment_selection_comparison())
            st.rerun()

    st.divider()
    st.subheader("Custom")
    st.write("**Reference Ecology** — bounded WB4 recipe; Extension stays internal.")
    if st.button("Start Reference Ecology"):
        _activate_artifact(
            new_reference_ecology(revision_id=_new_revision_id("reference"))
        )
        st.rerun()


def _render_open_study() -> None:
    _render_page_back("Home")
    st.title("Open Study")
    st.write(
        "Open a supported Workbench JSON artifact. The saved scientific manifest "
        "is loaded exactly; current defaults are not applied."
    )
    uploaded = st.file_uploader("Workbench Study JSON", type=("json",))
    if uploaded is None:
        return
    if not st.button("Open uploaded Study", type="primary"):
        return

    try:
        value = uploaded.getvalue().decode("utf-8")
        artifact = load_concrete_artifact(value)
    except UnicodeDecodeError:
        st.error("Study file must be UTF-8 JSON.")
        return
    except IncompatibleManifestError as exc:
        _render_exact_reproduction_failure(exc)
        return
    except (TypeError, ValueError) as exc:
        st.error(f"Study could not be opened: {exc}")
        return

    _activate_artifact(artifact)
    st.rerun()


def _render_study_shell() -> None:
    artifact = st.session_state.get(_ACTIVE_ARTIFACT_KEY)
    if not is_concrete_artifact(artifact):
        _go_home()
        st.rerun()

    home, heading, actions = st.columns((1, 5, 4))
    with home:
        if st.button("← Home"):
            _go_home()
            st.rerun()
    with heading:
        st.title(artifact_title(artifact))
        st.caption(artifact_type_label(artifact))
    with actions:
        _render_study_actions(artifact)

    _render_artifact_identity(artifact)
    st.divider()
    section = st.radio(
        "Study section",
        _STUDY_SECTIONS,
        horizontal=True,
        key=_SECTION_KEY,
        label_visibility="collapsed",
    )
    _render_study_section(artifact, section)

    active = st.session_state.get(_ACTIVE_ARTIFACT_KEY)
    if st.session_state.get(_RUN_PLAN_KEY) and is_concrete_artifact(active):
        _render_active_run_plan(active)


def _render_study_actions(artifact: ConcreteWorkbenchArtifact) -> None:
    readiness = effective_readiness(artifact)
    experiment_error = pending_experiment_error(artifact)
    run_disabled = readiness.state != "ready" or experiment_error is not None
    run_column, save_column, more_column = st.columns(3)
    with run_column:
        if st.button(
            "Run",
            disabled=run_disabled,
            use_container_width=True,
            help="Review the exact scientific Run Plan before execution.",
        ):
            _open_run_plan(artifact)
            st.rerun()
    with save_column:
        st.download_button(
            "Save Study",
            data=serialize_concrete_artifact(artifact),
            file_name=artifact_download_name(artifact),
            mime="application/json",
            use_container_width=True,
            help="Download the current immutable concrete Workbench artifact.",
        )
    with more_column:
        st.button(
            "More",
            disabled=True,
            use_container_width=True,
            help="Additional Study-level actions remain reserved for later milestones.",
        )


def _render_artifact_identity(artifact: ConcreteWorkbenchArtifact) -> None:
    revision_id = artifact_revision_id(artifact)
    readiness = effective_readiness(artifact)
    advisories = _current_advisories(artifact)

    details: list[str] = []
    if revision_id is not None:
        details.append(f"Revision · `{revision_id}`")
    details.append(f"Readiness · **{readiness.state.title()}**")
    if advisories:
        details.append(f"{len(advisories)} advisory")
    st.markdown("  |  ".join(details))

    for diagnostic in readiness.diagnostics:
        st.error(diagnostic.message)
        if diagnostic.slot_id is not None:
            st.caption(f"Scientific slot: `{diagnostic.slot_id}`")
        if diagnostic.remediation is not None:
            st.caption(diagnostic.remediation)
    for advisory in advisories:
        st.warning(advisory.message)

    experiment_error = pending_experiment_error(artifact)
    if experiment_error is not None:
        st.error(f"Unsaved Experiment draft is not runnable: {experiment_error}")


def _render_study_section(
    artifact: ConcreteWorkbenchArtifact,
    section: str,
) -> None:
    if section == "Simulation":
        if isinstance(
            artifact,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            _render_experiment_simulation_summary(artifact)
            return
        child = render_simulation_page(
            artifact,
            diff_parent=_diff_parent(),
            new_revision_id=_new_revision_id,
        )
        if child is not None:
            _activate_artifact(child, diff_parent=artifact)
            st.rerun()
        return

    if section == "Evidence":
        child = render_evidence_page(artifact, new_revision_id=_new_revision_id)
        if child is not None:
            _activate_artifact(child, diff_parent=artifact)
            st.rerun()
        return
    if section == "Experiment":
        definition = render_experiment_page(artifact)
        if definition is not None:
            _activate_artifact(definition)
            st.rerun()
        return
    if section == "Results":
        render_results_page(artifact, st.session_state.get(_RESULT_KEY))
        return

    st.header("Presentation")
    st.write(
        "Presentation remains downstream of scientific evidence. Renderer and "
        "world-workspace integration are intentionally deferred."
    )


def _render_experiment_simulation_summary(
    artifact: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
) -> None:
    st.header("Simulation")
    st.info(
        "This Simulation is owned jointly with a concrete controlled Experiment. "
        "Experiment-owned values are not duplicated as ordinary Simulation controls."
    )
    if isinstance(artifact, MaxSpeedSweepDefinition):
        st.write("**Maximum speed:** Varied by Experiment")
        st.write("**Seed:** Assigned by replicate design")
        st.write(
            "**Resource geography:** "
            f"{_humanize(artifact.base_intent.resource_geography)}"
        )
        return
    st.write("**Resource geography:** Varied by Experiment")
    st.write("**Seed:** Assigned by replicate design")
    st.write(
        "**Standing focal composition:** "
        + ", ".join(str(value) for value in artifact.focal_speeds)
        + " (fixed by Experiment)"
    )
    st.write(
        f"**Control / treatment:** {_humanize(artifact.control_environment)} / "
        f"{_humanize(artifact.treatment_environment)}"
    )


def _open_run_plan(artifact: ConcreteWorkbenchArtifact) -> None:
    try:
        bound, notice = bind_pending_scientific_state(
            artifact,
            new_revision_id=_new_revision_id,
        )
    except WorkbenchNotReadyError as exc:
        messages = "; ".join(item.message for item in exc.readiness.diagnostics)
        st.session_state[_RUN_FAILURE_KEY] = messages or str(exc)
        return
    except (TypeError, ValueError) as exc:
        st.session_state[_RUN_FAILURE_KEY] = str(exc)
        return

    if bound != artifact:
        _replace_active_for_run(bound, previous=artifact)
    st.session_state[_RUN_PLAN_KEY] = True
    st.session_state[_RUN_BINDING_NOTICE_KEY] = notice
    st.session_state.pop(_RUN_FAILURE_KEY, None)


def _render_active_run_plan(artifact: ConcreteWorkbenchArtifact) -> None:
    failure = st.session_state.get(_RUN_FAILURE_KEY)
    if type(failure) is str and failure:
        _render_run_failure(failure)
    try:
        action = render_run_plan(
            artifact,
            binding_notice=_binding_notice(),
        )
    except Exception as exc:  # noqa: BLE001 - top-level UI boundary preserves artifact
        _render_run_failure(str(exc))
        return
    if action == "cancel":
        _clear_run_plan_state()
        st.rerun()
    if action == "run":
        _execute_active_artifact(artifact)


def _execute_active_artifact(artifact: ConcreteWorkbenchArtifact) -> None:
    st.session_state.pop(_RESULT_KEY, None)
    st.session_state.pop(_RUN_FAILURE_KEY, None)
    try:
        with st.spinner("Executing the exact scientific definition..."):
            updated_artifact, result = execute_artifact(artifact)
    except Exception as exc:  # noqa: BLE001 - authoritative UI execution boundary
        st.session_state[_RUN_FAILURE_KEY] = str(exc)
        _render_run_failure(str(exc), exc=exc)
        return

    st.session_state[_ACTIVE_ARTIFACT_KEY] = updated_artifact
    st.session_state[_RESULT_KEY] = result
    st.session_state[_SECTION_KEY] = "Results"
    _clear_run_plan_state()
    st.rerun()


def _render_run_failure(message: str, *, exc: Exception | None = None) -> None:
    st.error("SIMULATION COULD NOT BE COMPILED OR RUN")
    st.write(
        "The saved scientific artifact has not been rewritten. Authoritative "
        "compilation, preflight, or execution rejected the exact definition."
    )
    st.code(message, language=None)
    if isinstance(exc, IncompatibleManifestError):
        st.caption(exc.diagnostic.remediation)


def _current_advisories(
    artifact: ConcreteWorkbenchArtifact,
) -> tuple[EvidenceAdvisory, ...]:
    if not isinstance(artifact, ReferenceStudyRevision):
        return ()
    plan = pending_evidence_plan(artifact) or artifact.evidence_plan
    return evidence_advisories_for_artifact(artifact, plan=plan)


def _replace_active_for_run(
    artifact: ConcreteWorkbenchArtifact,
    *,
    previous: ConcreteWorkbenchArtifact,
) -> None:
    clear_simulation_authoring_state()
    clear_evidence_authoring_state()
    clear_experiment_authoring_state()
    st.session_state[_ACTIVE_ARTIFACT_KEY] = artifact
    if artifact_revision_id(artifact) is not None:
        st.session_state[_DIFF_PARENT_KEY] = previous


def _render_exact_reproduction_failure(exc: IncompatibleManifestError) -> None:
    st.error("Exact reproduction unavailable.")
    st.write(exc.diagnostic.message)
    st.info(
        "This saved Study requires assumptions or a software version that the "
        "current implementation cannot reproduce exactly. The saved scientific "
        "manifest has not been re-resolved."
    )
    if exc.diagnostic.remediation is not None:
        st.caption(exc.diagnostic.remediation)


def _render_page_back(label: str) -> None:
    if st.button(f"← {label}"):
        _go_home()
        st.rerun()


def _activate_artifact(
    artifact: ConcreteWorkbenchArtifact,
    *,
    diff_parent: ConcreteWorkbenchArtifact | None = None,
) -> None:
    _clear_active_context()
    st.session_state[_ACTIVE_ARTIFACT_KEY] = artifact
    st.session_state[_SECTION_KEY] = _STUDY_SECTIONS[0]
    st.session_state[_ROUTE_KEY] = _STUDY
    if diff_parent is not None:
        st.session_state[_DIFF_PARENT_KEY] = diff_parent


def _go_home() -> None:
    _clear_active_context()
    st.session_state[_ROUTE_KEY] = _HOME


def _clear_active_context() -> None:
    clear_simulation_authoring_state()
    clear_evidence_authoring_state()
    clear_experiment_authoring_state()
    for key in (
        _ACTIVE_ARTIFACT_KEY,
        _SECTION_KEY,
        _RESULT_KEY,
        _DIFF_PARENT_KEY,
        _RUN_PLAN_KEY,
        _RUN_BINDING_NOTICE_KEY,
        _RUN_FAILURE_KEY,
        *_LEGACY_KEYS,
    ):
        st.session_state.pop(key, None)
    for key in tuple(st.session_state):
        if str(key).startswith("v2_world_"):
            st.session_state.pop(key, None)


def _clear_run_plan_state() -> None:
    for key in (_RUN_PLAN_KEY, _RUN_BINDING_NOTICE_KEY, _RUN_FAILURE_KEY):
        st.session_state.pop(key, None)


def _binding_notice() -> str | None:
    value = st.session_state.get(_RUN_BINDING_NOTICE_KEY)
    return value if type(value) is str and value else None


def _diff_parent() -> ConcreteWorkbenchArtifact | None:
    value = st.session_state.get(_DIFF_PARENT_KEY)
    return value if is_concrete_artifact(value) else None


def _has_active_artifact() -> bool:
    return is_concrete_artifact(st.session_state.get(_ACTIVE_ARTIFACT_KEY))


def _new_revision_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


if __name__ == "__main__":
    main()
