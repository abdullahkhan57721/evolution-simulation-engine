"""WU3 Run Plan rendering derived from exact concrete scientific artifacts."""

from __future__ import annotations

from typing import Literal, TypeAlias

import streamlit as st

from evo_engine.ui.evidence_authoring import (
    EvidenceBearingArtifact,
    evidence_advisories_for_artifact,
    evidence_options,
    requested_evidence_ids,
)
from evo_engine.ui.experiment_authoring import (
    b3_case_counts,
    environment_run_rows,
    max_speed_run_rows,
)
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench import (
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)
from evo_engine.workbench.controlled_locomotion import SEED_SLOT
from evo_engine.workbench.reference_ecology import (
    HORIZON_SLOT as REFERENCE_HORIZON_SLOT,
)
from evo_engine.workbench.reference_ecology import SEED_SLOT as REFERENCE_SEED_SLOT

RunPlanAction: TypeAlias = Literal["cancel", "run"]


def render_run_plan(
    artifact: ConcreteWorkbenchArtifact,
    *,
    binding_notice: str | None = None,
) -> RunPlanAction | None:
    """Render the exact current scientific definition before execution."""
    st.divider()
    if binding_notice is not None:
        st.info(binding_notice)
    if isinstance(artifact, StudyRevision):
        run_label = _render_controlled_plan(artifact)
    elif isinstance(artifact, ReferenceStudyRevision):
        run_label = _render_reference_plan(artifact)
    elif isinstance(artifact, B3StudyRevision):
        run_label = _render_b3_plan(artifact)
    elif isinstance(artifact, MaxSpeedSweepDefinition):
        run_label = _render_e3_plan(artifact)
    elif isinstance(artifact, EnvironmentSelectionComparisonDefinition):
        run_label = _render_e4_plan(artifact)
    else:
        raise TypeError("Unsupported Workbench artifact for Run Plan.")

    cancel, execute = st.columns(2)
    with cancel:
        if st.button("Cancel Run Plan", use_container_width=True):
            return "cancel"
    with execute:
        if st.button(run_label, type="primary", use_container_width=True):
            return "run"
    return None


def _render_controlled_plan(revision: StudyRevision) -> str:
    st.subheader("RUN STUDY")
    st.write(f"Study revision: `{revision.revision_id}`")
    st.write(f"Seed: **{revision.manifest.explicit_value(SEED_SLOT)}**")
    st.write(
        "Horizon: **"
        f"{revision.manifest.derived_value('controlled-locomotion.horizon-step-index')}"
        "**"
    )
    _render_manifest_digest(revision.manifest.digest)
    _render_evidence(revision)
    return "Run Study"


def _render_reference_plan(revision: ReferenceStudyRevision) -> str:
    st.subheader("RUN STUDY")
    st.write(f"Study revision: `{revision.revision_id}`")
    st.write(f"Seed: **{revision.manifest.explicit_value(REFERENCE_SEED_SLOT)}**")
    st.write(f"Horizon: **{revision.manifest.explicit_value(REFERENCE_HORIZON_SLOT)}**")
    _render_manifest_digest(revision.manifest.digest)
    _render_evidence(revision)
    advisories = evidence_advisories_for_artifact(revision)
    if advisories:
        st.markdown("**Advisories**")
        for advisory in advisories:
            st.warning(advisory.message)
    return "Run Study"


def _render_b3_plan(revision: B3StudyRevision) -> str:
    counts = b3_case_counts(revision)
    st.subheader("RUN CURATED B3 STUDY")
    st.write(f"Study revision: `{revision.revision_id}`")
    st.write(f"Scenario origin: `{revision.scenario_origin}`")
    if revision.scenario_identity is not None:
        st.write(f"Validated scenario: `{revision.scenario_identity}`")
    else:
        st.write("Validated scenario: **none — B3-derived sensitivity Study**")
    _render_manifest_digest(revision.manifest.digest)
    st.markdown("**Compiled scientific cases**")
    st.write(f"Primary confirmation pairs: **{counts.confirmation_pairs}**")
    st.write(f"Radius-sensitivity runs: **{counts.radius_sensitivity_runs}**")
    st.write(f"Counterbalanced pairs: **{counts.counterbalanced_pairs}**")
    st.write(f"Total simulations: **{counts.total_simulations}**")
    st.caption(
        "Same-seed control/treatment cases are matched blocks, not guaranteed "
        "lockstep trajectories after the treatment changes their dynamics."
    )
    _render_evidence(revision)
    return f"Run {counts.total_simulations} simulations"


def _render_e3_plan(definition: MaxSpeedSweepDefinition) -> str:
    rows = max_speed_run_rows(definition)
    st.subheader("RUN EXPERIMENT")
    st.write("Factor: **Maximum speed**")
    st.write("Levels: **" + _integer_text(definition.levels) + "**")
    st.write("Replicate seeds: **" + _integer_text(definition.seeds) + "**")
    st.write(f"Total simulations: **{len(rows)}**")
    _render_evidence(definition)
    with st.expander("View expanded design"):
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
    return f"Run {len(rows)} simulations"


def _render_e4_plan(definition: EnvironmentSelectionComparisonDefinition) -> str:
    rows = environment_run_rows(definition)
    st.subheader("RUN EXPERIMENT")
    st.write("Primary factor: **Resource geography**")
    st.write(f"Control: **{_humanize(definition.control_environment)}**")
    st.write(f"Treatment: **{_humanize(definition.treatment_environment)}**")
    st.write(
        "Standing focal composition: **" + _integer_text(definition.focal_speeds) + "**"
    )
    st.write("Replicate seeds: **" + _integer_text(definition.seeds) + "**")
    st.write(f"Total simulations: **{len(rows)}**")
    _render_evidence(definition)
    with st.expander("View expanded matched design"):
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
    return f"Run {len(rows)} simulations"


def _render_evidence(artifact: EvidenceBearingArtifact) -> None:
    labels = {option.evidence_id: option.label for option in evidence_options(artifact)}
    st.markdown("**Evidence**")
    for evidence_id in requested_evidence_ids(artifact):
        st.write(f"✓ {labels.get(evidence_id, evidence_id)}")


def _render_manifest_digest(digest: str) -> None:
    st.caption("Exact manifest digest")
    st.code(digest, language=None)


def _integer_text(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = ["RunPlanAction", "render_run_plan"]
