"""WU4 scientific Results workspace over authoritative WB5 result views."""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from evo_engine.experiments.b3_flagship import B3RunSummary
from evo_engine.experiments.locomotion import LocomotionReplicateMeasurements
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.observation import (
    GeneticCompositionObservation,
    IndividualLifeHistory,
    PopulationObservation,
    SpatialObservation,
)
from evo_engine.telemetry import AppliedEvent
from evo_engine.ui.evidence_authoring import evidence_options
from evo_engine.ui.results_navigation import inspect_current_results
from evo_engine.ui.results_tables import (
    b3_genetic_rows,
    b3_matched_summary_rows,
    b3_population_rows,
    b3_single_summary_rows,
    e3_energy_rows,
    e3_outcome_rows,
    e3_replicate_identity_rows,
    e3_summary_rows,
    e4_mechanism_rows,
    e4_replicate_identity_rows,
    e4_summary_chart_rows,
    e4_summary_rows,
    e4_trajectory_rows,
    event_rows,
    genetic_allele_rows,
    genetic_genotype_rows,
    historical_run_rows,
    locomotion_rows,
    pedigree_rows,
    population_rows,
    scientific_provenance_rows,
    spatial_carcass_rows,
    spatial_frame_rows,
    spatial_organism_rows,
    spatial_resource_rows,
    workbench_provenance_rows,
)
from evo_engine.ui.run_execution import is_authoritative_run_result
from evo_engine.ui.study_shell import (
    ConcreteWorkbenchArtifact,
    artifact_run_count,
    artifact_title,
)
from evo_engine.workbench.b3_curated import B3MatchedRunArtifacts, B3SingleRunArtifacts
from evo_engine.workbench.results import (
    AnalysisAvailability,
    B3ResultsView,
    ControlledLocomotionResultsView,
    EnvironmentSelectionReplicateView,
    EnvironmentSelectionResultsView,
    MaxSpeedSweepReplicateView,
    MaxSpeedSweepResultsView,
    ReferenceStudyResultsView,
)
from evo_engine.workbench.study import WorkbenchRunProvenance


def render_results_page(
    artifact: ConcreteWorkbenchArtifact,
    result: object,
) -> None:
    """Render current-session Results or honest provenance-only history."""
    st.header("Results")
    if not is_authoritative_run_result(result):
        _render_historical_state(artifact)
        return

    try:
        view = inspect_current_results(artifact, result)
    except (TypeError, ValueError) as exc:
        st.error("Current Results do not belong to this scientific artifact.")
        st.write(
            "The session result is being rejected rather than displayed under the "
            "wrong Study or Experiment identity."
        )
        st.code(str(exc), language=None)
        return

    st.success("Run completed — authoritative scientific Results are available")
    if isinstance(view, ControlledLocomotionResultsView):
        _render_controlled(artifact, view)
    elif isinstance(view, ReferenceStudyResultsView):
        _render_reference(artifact, view)
    elif isinstance(view, MaxSpeedSweepResultsView):
        _render_e3(artifact, view)
    elif isinstance(view, EnvironmentSelectionResultsView):
        _render_e4(artifact, view)
    elif isinstance(view, B3ResultsView):
        _render_b3(artifact, view)
    else:  # pragma: no cover - closed concrete dispatch guard
        raise TypeError("Unsupported inspected Results view.")


def _render_historical_state(artifact: ConcreteWorkbenchArtifact) -> None:
    run_count = artifact_run_count(artifact)
    if run_count:
        st.subheader("Historical run references")
        st.info(
            "This saved revision contains run provenance references, but the full "
            "authoritative scientific result payload is not present in this session. "
            "The application will not regenerate or rerun historical Results."
        )
        _table(historical_run_rows(getattr(artifact, "runs", ())))
        st.caption(
            "A historical run reference identifies what ran; it does not contain the "
            "observations, events, measurements, or experiment payloads themselves."
        )
    elif run_count == 0:
        st.info("No completed run payload is available in this session.")
    else:
        st.info(
            "This immutable Experiment definition does not serialize durable result "
            "payloads. Run it in this session to inspect scientific Results."
        )


def _render_controlled(
    artifact: ConcreteWorkbenchArtifact,
    view: ControlledLocomotionResultsView,
) -> None:
    overview, explore, analysis, provenance = st.tabs(
        ("Overview", "Explore", "Analysis", "Provenance")
    )
    with overview:
        _result_heading(artifact, "Single controlled run")
        _identity_metrics(
            run_id=view.provenance.run_id,
            revision_id=view.provenance.study_revision_id,
            seed=view.scientific_provenance.seed,
        )
        _recorded_evidence(artifact, view.provenance.evidence_ids)
        st.write(f"**Treatment:** `{view.scientific_provenance.treatment_id}`")
        st.write(f"**Manifest digest:** `{view.provenance.manifest_digest}`")

    with explore:
        st.subheader("Population history")
        _render_population(view.population_availability, view.population_observations)

    with analysis:
        st.subheader("Locomotion analysis")
        if _render_availability(view.locomotion_availability):
            if not isinstance(view.locomotion, LocomotionReplicateMeasurements):
                raise TypeError(
                    "Available locomotion analysis must be an E1 measurement."
                )
            _table(locomotion_rows(view.locomotion))
            st.caption(
                "These values are the existing E1 replicate measurement derived from "
                "committed movement evidence; the Results UI does not recalculate it."
            )

    with provenance:
        _render_workbench_provenance(view.provenance)
        _render_scientific_provenance(view.scientific_provenance)


def _render_reference(
    artifact: ConcreteWorkbenchArtifact,
    view: ReferenceStudyResultsView,
) -> None:
    overview, explore, analysis, provenance = st.tabs(
        ("Overview", "Explore", "Analysis", "Provenance")
    )
    with overview:
        _result_heading(artifact, "Reference Ecology run")
        _identity_metrics(
            run_id=view.provenance.run_id,
            revision_id=view.provenance.study_revision_id,
            seed=view.scientific_provenance.seed,
        )
        _recorded_evidence(artifact, view.provenance.evidence_ids)
        st.write(f"**Manifest digest:** `{view.provenance.manifest_digest}`")

    with explore:
        population, events, pedigree, genetics, spatial = st.tabs(
            ("Population", "Events", "Pedigree", "Genetics", "Spatial history")
        )
        with population:
            _render_population(
                view.population_availability,
                view.population_observations,
            )
        with events:
            _render_events(view.event_availability, view.applied_events)
        with pedigree:
            _render_pedigree(view.pedigree_availability, view.pedigree_records)
        with genetics:
            _render_genetics(view.genetic_availability, view.genetic_observations)
        with spatial:
            _render_spatial(view.spatial_availability, view.spatial_observations)

    with analysis:
        st.subheader("Recorded scientific evidence")
        st.write(
            "Reference Ecology currently exposes committed evidence streams rather "
            "than a generic derived-analysis layer. Each stream below is independently "
            "gated by the EvidencePlan used for this exact run."
        )
        for label, availability in (
            ("Population history", view.population_availability),
            ("Committed events", view.event_availability),
            ("Pedigree / life history", view.pedigree_availability),
            ("Genetic composition", view.genetic_availability),
            ("Spatial history", view.spatial_availability),
        ):
            _availability_line(label, availability)

    with provenance:
        _render_workbench_provenance(view.provenance)
        _render_scientific_provenance(view.scientific_provenance)


def _render_e3(
    artifact: ConcreteWorkbenchArtifact,
    view: MaxSpeedSweepResultsView,
) -> None:
    overview, explore, analysis, provenance = st.tabs(
        ("Overview", "Explore", "Analysis", "Provenance")
    )
    with overview:
        _result_heading(artifact, "Ecological-performance sweep")
        left, middle, right = st.columns(3)
        left.metric("Factor", "Maximum speed")
        middle.metric("Factor levels", len(view.definition.levels))
        right.metric("Simulation replicates", len(view.replicates))
        st.write(
            "**Resource geography:** "
            f"{_humanize(view.definition.base_intent.resource_geography)}"
        )
        st.write(
            "**Replicate seeds:** "
            + ", ".join(str(seed) for seed in view.definition.seeds)
        )
        _recorded_evidence(artifact, view.definition.evidence_plan.requested)

    with explore:
        replicate = _select_e3_replicate(view)
        _table(e3_replicate_identity_rows(replicate))
        st.subheader("Replicate outcome")
        _table(e3_outcome_rows(replicate.outcome))
        st.subheader("Committed energy trajectory")
        energy = e3_energy_rows(replicate.outcome)
        _line_chart(energy, x="Step", y="Total population energy")
        _table(energy)
        st.subheader("Existing locomotion measurement")
        _table(locomotion_rows(replicate.outcome.locomotion))

    with analysis:
        st.subheader("Treatment-level performance landscape")
        rows = e3_summary_rows(view.treatment_summaries)
        _line_chart(rows, x="Maximum speed", y="Mean cumulative births")
        _table(rows)
        st.caption(
            "Rows and chart values come directly from existing E3TreatmentSummary "
            "objects. Organisms inside a run are not treated as independent replicates."
        )

    with provenance:
        replicate = _select_e3_replicate(view, key="wu4_e3_provenance")
        _table(e3_replicate_identity_rows(replicate))
        _render_scientific_provenance(replicate.outcome.provenance)
        st.caption(
            "E3 owns immutable Experiment-definition and replicate identity; WU4 does "
            "not invent a Study revision or Study-level run ID."
        )


def _render_e4(
    artifact: ConcreteWorkbenchArtifact,
    view: EnvironmentSelectionResultsView,
) -> None:
    overview, explore, analysis, provenance = st.tabs(
        ("Overview", "Explore", "Analysis", "Provenance")
    )
    with overview:
        _result_heading(artifact, "Selection on standing variation")
        left, middle, right = st.columns(3)
        left.metric("Factor", "Resource geography")
        middle.metric("Arms", 2)
        right.metric("Simulation replicates", len(view.replicates))
        st.write(
            "**Control / treatment:** "
            f"{_humanize(view.definition.control_environment)} / "
            f"{_humanize(view.definition.treatment_environment)}"
        )
        st.write(
            "**Standing focal composition:** "
            + ", ".join(str(speed) for speed in view.definition.focal_speeds)
        )
        st.caption(
            "Founder-speed order is counterbalance metadata, not another experimental "
            "factor."
        )
        _recorded_evidence(artifact, view.definition.evidence_plan.requested)

    with explore:
        replicate = _select_e4_replicate(view)
        _table(e4_replicate_identity_rows(replicate))
        st.subheader("Focal composition trajectory")
        trajectory = e4_trajectory_rows(replicate.outcome)
        frequency_columns = [
            f"Speed {speed} frequency" for speed in replicate.standing_focal_composition
        ]
        _line_chart(trajectory, x="Step", y=frequency_columns)
        _table(trajectory)
        st.subheader("Existing mechanism evidence")
        _table(e4_mechanism_rows(replicate.outcome))

    with analysis:
        st.subheader("Environment-level selection summaries")
        chart_rows = e4_summary_chart_rows(view.environment_summaries)
        _bar_chart(
            chart_rows,
            x="Environment",
            y=[
                f"Speed {speed} frequency change"
                for speed in view.definition.focal_speeds
            ],
        )
        _table(e4_summary_rows(view.environment_summaries))
        st.caption(
            "Frequency endpoints, changes, mechanism means, and extinction counts are "
            "the existing E4EnvironmentSummary values; WU4 does not recompute them."
        )

    with provenance:
        replicate = _select_e4_replicate(view, key="wu4_e4_provenance")
        _table(e4_replicate_identity_rows(replicate))
        _render_scientific_provenance(replicate.outcome.provenance)
        st.caption(
            "Resource geography remains the factor. Control/treatment role, seed, "
            "standing composition, and founder-order counterbalance remain distinct."
        )


def _render_b3(
    artifact: ConcreteWorkbenchArtifact,
    view: B3ResultsView,
) -> None:
    overview, explore, analysis, provenance = st.tabs(
        ("Overview", "Explore", "Analysis", "Provenance")
    )
    with overview:
        _result_heading(artifact, "Curated B3 scientific result")
        _identity_metrics(
            run_id=view.provenance.run_id,
            revision_id=view.provenance.study_revision_id,
            seed=None,
        )
        st.write(f"**Scenario origin:** `{view.scenario_origin}`")
        identity = view.scenario_identity or "No validated canonical identity"
        st.write(f"**Validated scenario identity:** `{identity}`")
        _recorded_evidence(artifact, view.provenance.evidence_ids)
        st.write(f"**Manifest digest:** `{view.provenance.manifest_digest}`")

    with explore:
        role = st.radio(
            "Scientific run role",
            (
                "Primary confirmation",
                "Radius sensitivity",
                "Founder-label counterbalance",
            ),
            horizontal=True,
            key="wu4_b3_role",
        )
        if role == "Primary confirmation":
            _render_b3_matched_explorer(
                view.confirmation,
                key="wu4_b3_confirmation",
            )
        elif role == "Radius sensitivity":
            _render_b3_single_explorer(
                view.radius_sensitivity,
                key="wu4_b3_sensitivity",
            )
        else:
            _render_b3_matched_explorer(
                view.counterbalanced,
                key="wu4_b3_counterbalance",
            )

    with analysis:
        st.subheader("Primary confirmation")
        _table(
            b3_matched_summary_rows(tuple(item.summary for item in view.confirmation))
        )
        st.caption(
            "Control and compact-treatment arms are matched/blocked by seed. Matching "
            "does not imply RNG streams stay lockstep after the treatments diverge."
        )
        st.subheader("Radius sensitivity")
        _table(
            b3_single_summary_rows(
                tuple(item.summary for item in view.radius_sensitivity)
            )
        )
        st.caption(
            "Sensitivity remains secondary to the canonical primary confirmation."
        )
        st.subheader("Founder-label counterbalance")
        _table(
            b3_matched_summary_rows(
                tuple(item.summary for item in view.counterbalanced)
            )
        )
        st.caption(
            "Founder-label assignment is counterbalance evidence, not the biological "
            "resource-geography treatment factor."
        )
        st.subheader("Cinematic scientific handoff")
        if _render_availability(view.cinematic_handoff_availability):
            st.success("Canonical B3 cinematic scientific handoff is available.")
        else:
            st.caption(
                "Results remains scientific analysis only; cinematic execution belongs "
                "to downstream Presentation integration."
            )

    with provenance:
        _render_workbench_provenance(view.provenance)
        st.write(f"**Scenario origin:** `{view.scenario_origin}`")
        st.write(
            "**Validated scenario identity:** "
            + (f"`{view.scenario_identity}`" if view.scenario_identity else "None")
        )
        st.caption(
            "B3 scientific origin and validated canonical identity are intentionally "
            "different provenance concepts."
        )


def _render_population(
    availability: AnalysisAvailability,
    observations: Sequence[PopulationObservation],
) -> None:
    if not _render_availability(availability):
        return
    rows = population_rows(observations)
    if not rows:
        st.info("The evidence stream was requested but contains no population rows.")
        return
    _line_chart(rows, x="Step", y="Population size")
    _table(rows)


def _render_events(
    availability: AnalysisAvailability,
    events: Sequence[AppliedEvent],
) -> None:
    if not _render_availability(availability):
        return
    rows = event_rows(events)
    if not rows:
        st.info("No committed events were recorded in this run.")
        return
    process_names = tuple(dict.fromkeys(item.process_name for item in events))
    selected = st.selectbox(
        "Process filter",
        ("All processes", *process_names),
        key="wu4_reference_event_process",
    )
    if selected != "All processes":
        rows = [row for row in rows if row["Process"] == selected]
    _table(rows)


def _render_pedigree(
    availability: AnalysisAvailability,
    records: Sequence[IndividualLifeHistory],
) -> None:
    if not _render_availability(availability):
        return
    rows = pedigree_rows(records)
    if rows:
        _table(rows)
    else:
        st.info("No individual life-history records are present.")


def _render_genetics(
    availability: AnalysisAvailability,
    observations: Sequence[GeneticCompositionObservation],
) -> None:
    if not _render_availability(availability):
        return
    allele_rows = genetic_allele_rows(observations)
    genotype_rows = genetic_genotype_rows(observations)
    if not allele_rows and not genotype_rows:
        st.info("No genetic-composition observations are present.")
        return
    alleles, genotypes = st.tabs(("Alleles", "Genotypes"))
    with alleles:
        _table(allele_rows)
    with genotypes:
        _table(genotype_rows)


def _render_spatial(
    availability: AnalysisAvailability,
    observations: Sequence[SpatialObservation],
) -> None:
    if not _render_availability(availability):
        return
    rows = spatial_frame_rows(observations)
    if not rows:
        st.info("No spatial observations are present.")
        return
    _table(rows)
    steps = tuple(item.step_index for item in observations)
    selected_step = st.select_slider(
        "Inspect committed spatial frame",
        options=steps,
        value=steps[-1],
        key="wu4_reference_spatial_step",
    )
    frame = next(item for item in observations if item.step_index == selected_step)
    st.caption(
        "This is committed spatial evidence inspection, not interpolated world replay."
    )
    organisms, resources, carcasses = st.tabs(("Organisms", "Resources", "Carcasses"))
    with organisms:
        _table(spatial_organism_rows(frame))
    with resources:
        _table(spatial_resource_rows(frame))
    with carcasses:
        _table(spatial_carcass_rows(frame))


def _render_availability(value: AnalysisAvailability) -> bool:
    if value.available:
        return True
    st.warning("This analysis is unavailable for the completed run.")
    if value.missing_evidence_ids:
        st.write("**Evidence not recorded:** " + ", ".join(value.missing_evidence_ids))
        st.info(
            "Obtaining this analysis requires a new run with an appropriate "
            "EvidencePlan. Evidence cannot be added retroactively to a completed run."
        )
    if value.unavailable_reason is not None:
        st.write(value.unavailable_reason)
    with st.expander("Technical evidence contract"):
        st.write(f"Analysis ID: `{value.analysis_id}`")
        st.write(f"Source contract: `{value.source_contract}`")
        st.write("Required evidence: " + ", ".join(value.required_evidence_ids))
    return False


def _availability_line(label: str, value: AnalysisAvailability) -> None:
    if value.available:
        st.write(f"✓ **{label}** — available")
        return
    detail = (
        "missing " + ", ".join(value.missing_evidence_ids)
        if value.missing_evidence_ids
        else value.unavailable_reason or "unavailable"
    )
    st.write(f"○ **{label}** — {detail}")


def _select_e3_replicate(
    view: MaxSpeedSweepResultsView,
    *,
    key: str = "wu4_e3_explore",
) -> MaxSpeedSweepReplicateView:
    level = st.selectbox(
        "Maximum-speed factor level",
        view.definition.levels,
        key=f"{key}_level",
    )
    replicates = tuple(item for item in view.replicates if item.factor_level == level)
    seed = st.selectbox(
        "Replicate seed",
        tuple(item.seed for item in replicates),
        key=f"{key}_seed",
    )
    return next(item for item in replicates if item.seed == seed)


def _select_e4_replicate(
    view: EnvironmentSelectionResultsView,
    *,
    key: str = "wu4_e4_explore",
) -> EnvironmentSelectionReplicateView:
    role = st.radio(
        "Arm",
        ("control", "treatment"),
        horizontal=True,
        key=f"{key}_role",
    )
    candidates = tuple(item for item in view.replicates if item.role == role)
    seed = st.selectbox(
        "Replicate seed",
        tuple(dict.fromkeys(item.seed for item in candidates)),
        key=f"{key}_seed",
    )
    return next(item for item in candidates if item.seed == seed)


def _render_b3_matched_explorer(
    values: Sequence[B3MatchedRunArtifacts],
    *,
    key: str,
) -> None:
    if not values:
        st.info("No run artifacts are present for this B3 role.")
        return
    labels = tuple(
        f"Seed {item.summary.seed} · {_humanize(item.summary.founder_assignment)}"
        for item in values
    )
    selected = st.selectbox("Matched replicate", labels, key=f"{key}_pair")
    pair = values[labels.index(selected)]
    _table(b3_matched_summary_rows((pair.summary,)))
    arm = st.radio(
        "Arm",
        ("Uniform control", "Compact treatment"),
        horizontal=True,
        key=f"{key}_arm",
    )
    summary = (
        pair.summary.control if arm == "Uniform control" else pair.summary.treatment
    )
    _render_b3_run_summary(summary)


def _render_b3_single_explorer(
    values: Sequence[B3SingleRunArtifacts],
    *,
    key: str,
) -> None:
    if not values:
        st.info("No radius-sensitivity artifacts are present for this revision.")
        return
    labels = tuple(
        f"Seed {item.summary.seed} · {_humanize(item.summary.environment)}"
        for item in values
    )
    selected = st.selectbox("Sensitivity replicate", labels, key=f"{key}_run")
    item = values[labels.index(selected)]
    _table(b3_single_summary_rows((item.summary,)))
    _render_b3_run_summary(item.summary)


def _render_b3_run_summary(summary: B3RunSummary) -> None:
    population = b3_population_rows(summary)
    genetics = b3_genetic_rows(summary)
    st.subheader("Population trajectory")
    _line_chart(population, x="Step", y="Population size")
    _table(population)
    st.subheader("Focal genetic trajectory")
    _line_chart(genetics, x="Step", y="High-speed allele frequency")
    _table(genetics)
    st.subheader("Existing founder reproductive-success summary")
    success = summary.founder_reproductive_success
    _table(
        [
            {
                "Low-speed founders": success.low_speed_count,
                "Low-speed mean direct offspring": success.low_speed_mean,
                "High-speed founders": success.high_speed_count,
                "High-speed mean direct offspring": success.high_speed_mean,
            }
        ]
    )


def _result_heading(artifact: ConcreteWorkbenchArtifact, subtitle: str) -> None:
    st.subheader(artifact_title(artifact))
    st.caption(subtitle)


def _identity_metrics(
    *,
    run_id: str | None,
    revision_id: str | None,
    seed: int | None,
) -> None:
    columns = st.columns(3)
    columns[0].metric("Run", run_id or "Concrete experiment result")
    columns[1].metric("Study revision", revision_id or "Not applicable")
    columns[2].metric("Seed / replicate", seed if seed is not None else "Multiple")


def _recorded_evidence(
    artifact: ConcreteWorkbenchArtifact,
    evidence_ids: Sequence[str],
) -> None:
    labels = {option.evidence_id: option.label for option in evidence_options(artifact)}
    st.markdown("**Recorded evidence**")
    for evidence_id in evidence_ids:
        st.write(f"✓ {labels.get(evidence_id, evidence_id)}")


def _render_workbench_provenance(value: WorkbenchRunProvenance) -> None:
    st.subheader("Study / run provenance")
    _table(workbench_provenance_rows(value))


def _render_scientific_provenance(value: ScientificRunProvenance) -> None:
    st.subheader("Scientific replicate provenance")
    _table(scientific_provenance_rows(value))


def _table(rows: Sequence[dict[str, object]]) -> None:
    if not rows:
        st.caption("No rows to display.")
        return
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _line_chart(
    rows: Sequence[dict[str, object]],
    *,
    x: str,
    y: str | Sequence[str],
) -> None:
    if rows:
        st.line_chart(rows, x=x, y=y, use_container_width=True)


def _bar_chart(
    rows: Sequence[dict[str, object]],
    *,
    x: str,
    y: str | Sequence[str],
) -> None:
    if rows:
        st.bar_chart(rows, x=x, y=y, use_container_width=True)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = ["render_results_page"]
