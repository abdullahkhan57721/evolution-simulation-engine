"""Streamlit entry point for the Evolution Experiment Workbench."""

from __future__ import annotations

import uuid

import streamlit as st

from evo_engine.ui.study_shell import (
    ConcreteWorkbenchArtifact,
    artifact_download_name,
    artifact_readiness,
    artifact_revision_id,
    artifact_run_count,
    artifact_title,
    artifact_type_label,
    load_concrete_artifact,
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
    serialize_concrete_artifact,
)
from evo_engine.workbench import IncompatibleManifestError

_ROUTE_KEY = "wu1_route"
_ACTIVE_ARTIFACT_KEY = "wu1_active_artifact"
_SECTION_KEY = "wu1_study_section"
_RESULT_KEY = "wu1_current_result"

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
        "WU1 opens supported concrete starting artifacts. Scientific authoring "
        "controls arrive in later WU milestones."
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
    if not _is_supported_artifact(artifact):
        _go_home()
        st.rerun()

    artifact = artifact
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


def _render_study_actions(artifact: ConcreteWorkbenchArtifact) -> None:
    run_column, save_column, more_column = st.columns(3)
    with run_column:
        st.button(
            "Run",
            disabled=True,
            use_container_width=True,
            help="WU1 reserves the primary Run action; execution integration is later.",
        )
    with save_column:
        st.download_button(
            "Save Study",
            data=serialize_concrete_artifact(artifact),
            file_name=artifact_download_name(artifact),
            mime="application/json",
            use_container_width=True,
        )
    with more_column:
        st.button(
            "More",
            disabled=True,
            use_container_width=True,
            help="Fork and semantic-diff actions arrive in WU2.",
        )


def _render_artifact_identity(artifact: ConcreteWorkbenchArtifact) -> None:
    revision_id = artifact_revision_id(artifact)
    readiness = artifact_readiness(artifact)

    details: list[str] = []
    if revision_id is not None:
        details.append(f"Revision · `{revision_id}`")
    if readiness is not None:
        details.append(f"Readiness · **{readiness.state.title()}**")
    if details:
        st.markdown("  |  ".join(details))

    if readiness is not None and readiness.state != "ready":
        for diagnostic in readiness.diagnostics:
            st.error(diagnostic.message)
            if diagnostic.remediation is not None:
                st.caption(diagnostic.remediation)


def _render_study_section(
    artifact: ConcreteWorkbenchArtifact,
    section: str,
) -> None:
    st.header(section)
    if section == "Simulation":
        st.write(
            "This Study's concrete simulation meaning is loaded and retained. "
            "Simulation authoring is intentionally deferred to WU2."
        )
    elif section == "Evidence":
        st.write(
            "The concrete artifact's existing evidence plan is preserved exactly. "
            "Evidence authoring is intentionally deferred."
        )
    elif section == "Experiment":
        st.write(
            "Experiment structure is shown through the active concrete Workbench "
            "artifact; WU1 does not introduce an experiment DSL or generic builder."
        )
    elif section == "Results":
        _render_results_placeholder(artifact)
    else:
        st.write(
            "Presentation remains downstream of scientific evidence. Renderer and "
            "world-workspace integration are intentionally deferred."
        )


def _render_results_placeholder(artifact: ConcreteWorkbenchArtifact) -> None:
    if st.session_state.get(_RESULT_KEY) is not None:
        st.info("A session-only result is present, but WU1 does not persist it.")
        return

    run_count = artifact_run_count(artifact)
    if run_count:
        st.info(
            f"This saved Study records {run_count} completed run reference(s), but "
            "complete result payloads are not serialized by this Study format. "
            "Reopening does not reconstruct or automatically rerun them."
        )
    elif run_count == 0:
        st.info("No completed run payload is available in this session.")
    else:
        st.info(
            "This concrete experiment definition does not contain durable result "
            "payloads. WU1 does not invent result storage."
        )


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


def _activate_artifact(artifact: ConcreteWorkbenchArtifact) -> None:
    _clear_active_context()
    st.session_state[_ACTIVE_ARTIFACT_KEY] = artifact
    st.session_state[_SECTION_KEY] = _STUDY_SECTIONS[0]
    st.session_state[_ROUTE_KEY] = _STUDY


def _go_home() -> None:
    _clear_active_context()
    st.session_state[_ROUTE_KEY] = _HOME


def _clear_active_context() -> None:
    for key in (_ACTIVE_ARTIFACT_KEY, _SECTION_KEY, _RESULT_KEY, *_LEGACY_KEYS):
        st.session_state.pop(key, None)
    for key in tuple(st.session_state):
        if str(key).startswith("v2_world_"):
            st.session_state.pop(key, None)


def _has_active_artifact() -> bool:
    return _is_supported_artifact(st.session_state.get(_ACTIVE_ARTIFACT_KEY))


def _is_supported_artifact(value: object) -> bool:
    return hasattr(value, "to_json") and type(value).__module__.startswith(
        "evo_engine.workbench"
    )


def _new_revision_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


if __name__ == "__main__":
    main()
