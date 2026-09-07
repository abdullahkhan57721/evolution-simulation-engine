"""WU2 Simulation-page rendering over existing concrete Workbench contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import attrs
import streamlit as st

from evo_engine.ui.simulation_authoring import (
    controlled_draft_readiness,
    normalize_reference_draft,
    reference_draft_readiness,
    reference_has_expert_controls,
    reference_slots_for_disclosure,
    save_b3_radius_sensitivity_child,
    save_controlled_child,
    save_reference_child,
    semantic_slot_label,
    simulation_semantic_diff,
)
from evo_engine.ui.study_shell import ConcreteWorkbenchArtifact
from evo_engine.workbench import (
    B3CuratedDiff,
    B3StudyRevision,
    ControlledLocomotionDiff,
    ControlledLocomotionIntent,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceEcologyDiff,
    ReferenceEcologyIntent,
    ReferenceStudyRevision,
    StudyRevision,
    WorkbenchReadiness,
    assess_b3_readiness,
    evidence_advisories,
    resolve_controlled_locomotion,
    resolve_reference_ecology,
)
from evo_engine.workbench.controlled_locomotion import (
    MAX_SPEED_SLOT as CONTROLLED_MAX_SPEED_SLOT,
)
from evo_engine.workbench.controlled_locomotion import (
    RESOURCE_GEOGRAPHY_SLOT as CONTROLLED_RESOURCE_GEOGRAPHY_SLOT,
)
from evo_engine.workbench.controlled_locomotion import (
    SEED_SLOT as CONTROLLED_SEED_SLOT,
)
from evo_engine.workbench.controlled_locomotion import SUPPORTED_RESOURCE_GEOGRAPHIES
from evo_engine.workbench.reference_ecology import (
    EXPLORATION_MOVEMENT_SLOT,
    FOUNDER_ENERGY_SLOT,
    FOUNDER_POPULATION_SLOT,
    GAUSSIAN_STDDEV_SLOT,
    HORIZON_SLOT,
    MAX_SPEED_SLOT as REFERENCE_MAX_SPEED_SLOT,
    MUTATION_ENABLED_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_RADIUS_SLOT,
    PATCH_1_X_SLOT,
    PATCH_1_Y_SLOT,
    PATCH_2_RADIUS_SLOT,
    PATCH_2_X_SLOT,
    PATCH_2_Y_SLOT,
    RECOMBINATION_PROBABILITY_SLOT,
    RESOURCE_AMOUNT_SLOT,
    RESOURCE_DEPOSITS_SLOT,
    RESOURCE_GEOGRAPHY_SLOT as REFERENCE_RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT as REFERENCE_SEED_SLOT,
    SENSORY_ACCURACY_SLOT,
    SENSORY_RANGE_SLOT,
    WORLD_HEIGHT_SLOT,
    WORLD_WIDTH_SLOT,
)

_DRAFT_INTENT_KEY = "wu2_simulation_draft_intent"
_DRAFT_REVISION_KEY = "wu2_simulation_draft_revision_id"

_CONTROLLED_DYNAMIC_DERIVED = (
    "controlled-locomotion.initial-focal-max-speed",
    "controlled-locomotion.resource-deposit-layout",
)
_CONTROLLED_FROZEN = (
    "controlled-locomotion.inherited-traits",
    "controlled-locomotion.genetics",
    "controlled-locomotion.inheritance",
    "controlled-locomotion.mutation",
    "controlled-locomotion.sensing",
    "controlled-locomotion.movement-targeting",
    "controlled-locomotion.horizon-step-index",
    "controlled-locomotion.locomotion-cost-coefficient",
    "controlled-locomotion.reproduction-minimum-energy",
    "controlled-locomotion.reproduction-energy-investment",
    "controlled-locomotion.mate-search",
    "controlled-locomotion.predation",
    "controlled-locomotion.metabolism",
    "controlled-locomotion.growth",
    "controlled-locomotion.aging",
    "controlled-locomotion.renewable-resource-generation",
)
_REFERENCE_DYNAMIC_DERIVED = (
    "reference-ecology.resolved-resource-placement",
    "reference-ecology.resolved-exploration-pattern",
    "reference-ecology.effective-mutation-probability-ppm",
    "reference-ecology.effective-mutation-max-change",
)
_REFERENCE_FROZEN = (
    "reference-ecology.fixed-reference-config",
    "reference-ecology.genome-structure",
    "reference-ecology.genetic-expression",
    "reference-ecology.inheritance",
    "reference-ecology.development",
    "reference-ecology.reproduction",
    "reference-ecology.food-targeting",
    "reference-ecology.mate-targeting",
)
_B3_SUMMARY = (
    ("Study design", "b3.study-design"),
    ("Control environment", "b3.control-resource-geography"),
    ("Treatment environment", "b3.treatment-resource-geography"),
    ("Treatment integrity", "b3.treatment-integrity"),
    ("Focal trait", "b3.focal-trait"),
    ("Focal trait semantics", "b3.focal-trait-semantics"),
    ("Founder variants", "b3.founder-variant-values"),
    ("Founder construction", "b3.founder-construction"),
    ("Run horizon", "b3.config.max-steps"),
    ("Mutation probability (ppm)", "b3.config.mutation-probability-ppm"),
    ("Mutation maximum change", "b3.config.mutation-max-change"),
    ("Inheritance", "b3.inheritance"),
    ("Mating system", "b3.mating-types"),
    ("Counterbalance design", "b3.counterbalance-design"),
)


def clear_simulation_authoring_state() -> None:
    """Clear private WU2 draft/widget state when application context changes."""
    for key in tuple(st.session_state):
        if str(key).startswith("wu2_"):
            st.session_state.pop(key, None)


def render_simulation_page(
    artifact: ConcreteWorkbenchArtifact,
    *,
    diff_parent: ConcreteWorkbenchArtifact | None,
    new_revision_id: Callable[[str], str],
) -> ConcreteWorkbenchArtifact | None:
    """Render WU2 Simulation authoring and return a newly saved child if requested."""
    st.header("Simulation")
    if isinstance(artifact, StudyRevision):
        return _render_controlled(artifact, diff_parent, new_revision_id)
    if isinstance(artifact, ReferenceStudyRevision):
        return _render_reference(artifact, diff_parent, new_revision_id)
    if isinstance(artifact, B3StudyRevision):
        return _render_b3(artifact, diff_parent, new_revision_id)
    if isinstance(
        artifact,
        (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
    ):
        st.info(
            "This Study is a concrete experiment definition. Its simulation factors "
            "remain fixed here; experiment authoring belongs to the Experiment page "
            "in WU3."
        )
        return None
    raise TypeError("Unsupported Workbench artifact for Simulation rendering.")


def _render_controlled(
    parent: StudyRevision,
    diff_parent: ConcreteWorkbenchArtifact | None,
    new_revision_id: Callable[[str], str],
) -> StudyRevision | None:
    draft = _controlled_draft(parent)
    authoring, meaning = st.columns((3, 2))
    with authoring:
        st.subheader("Authoring")
        st.caption(
            "Explicit semantic choices only; recipe assumptions remain read-only."
        )

        st.markdown("#### Movement & sensing")
        max_speed = _integer_input(
            "Maximum speed",
            draft.max_speed,
            key=_widget_key(parent.revision_id, "controlled-max-speed"),
        )

        st.markdown("#### Environment")
        options = tuple(sorted(SUPPORTED_RESOURCE_GEOGRAPHIES))
        resource_geography = st.selectbox(
            "Resource geography",
            options,
            index=_option_index(options, draft.resource_geography),
            format_func=_humanize,
            key=_widget_key(parent.revision_id, "controlled-resource-geography"),
        )

        st.markdown("#### Run")
        seed = _integer_input(
            "Random seed",
            draft.seed,
            key=_widget_key(parent.revision_id, "controlled-seed"),
        )
        draft = ControlledLocomotionIntent(
            max_speed=max_speed,
            resource_geography=resource_geography,
            seed=seed,
        )
        _store_draft(parent.revision_id, draft)
        readiness = controlled_draft_readiness(parent, draft)
        _render_slot_diagnostics(readiness)

    preview = None
    if readiness.state == "ready":
        preview = resolve_controlled_locomotion(draft, parent.evidence_plan)
    with meaning:
        _render_readiness(readiness)
        _render_controlled_meaning(parent, draft, preview)

    changed = draft != parent.intent
    if changed:
        st.info(
            "Unsaved draft: the current revision remains immutable until a child "
            "revision is saved."
        )
    if st.button(
        "Save new revision",
        type="primary",
        disabled=readiness.state != "ready" or not changed,
        key=_widget_key(parent.revision_id, "controlled-save-child"),
    ):
        return save_controlled_child(
            parent,
            draft=draft,
            revision_id=new_revision_id("controlled"),
        )

    _render_parent_diff(diff_parent, parent)
    return None


def _render_reference(
    parent: ReferenceStudyRevision,
    diff_parent: ConcreteWorkbenchArtifact | None,
    new_revision_id: Callable[[str], str],
) -> ReferenceStudyRevision | None:
    draft = _reference_draft(parent)
    authoring, meaning = st.columns((3, 2))
    with authoring:
        st.subheader("Authoring")
        disclosure = cast(
            str,
            st.radio(
                "Disclosure",
                ("Guided", "Advanced"),
                horizontal=True,
                key=_widget_key(parent.revision_id, "reference-disclosure"),
            ),
        )
        if disclosure not in ("Guided", "Advanced"):
            raise ValueError("Unexpected disclosure selection.")
        draft = _render_reference_guided(parent, draft)

        if disclosure == "Advanced":
            draft = _render_reference_advanced(parent, draft)
            if not reference_has_expert_controls():
                st.caption(
                    "No Expert controls are currently authorable. Extension/internal "
                    "engine composition remains outside this bounded recipe."
                )

        normalized = normalize_reference_draft(draft)
        normalization_notice = normalized != draft
        draft = normalized
        _store_draft(parent.revision_id, draft)
        readiness = reference_draft_readiness(parent, draft)
        if normalization_notice:
            st.info(
                "A value became inapplicable and was removed from the draft's "
                "scientific meaning by the current WB4 applicability rules."
            )
        _render_slot_diagnostics(readiness)

    preview = None
    if readiness.state == "ready":
        preview = resolve_reference_ecology(draft, parent.evidence_plan)
    with meaning:
        _render_readiness(readiness)
        for advisory in evidence_advisories(parent.evidence_plan):
            st.warning(advisory.message)
        _render_reference_meaning(parent, draft, preview)

    changed = draft != parent.intent
    if changed:
        st.info(
            "Unsaved draft: saving creates a new immutable reference-ecology child "
            "revision; the parent is not mutated."
        )
    if st.button(
        "Save new revision",
        type="primary",
        disabled=readiness.state != "ready" or not changed,
        key=_widget_key(parent.revision_id, "reference-save-child"),
    ):
        return save_reference_child(
            parent,
            draft=draft,
            revision_id=new_revision_id("reference"),
        )

    _render_parent_diff(diff_parent, parent)
    return None


def _render_reference_guided(
    parent: ReferenceStudyRevision,
    draft: ReferenceEcologyIntent,
) -> ReferenceEcologyIntent:
    visible = {
        item.slot_id for item in reference_slots_for_disclosure(draft, "Guided")
    }

    st.markdown("#### Environment")
    width = _integer_input(
        "World width",
        draft.width,
        key=_widget_key(parent.revision_id, WORLD_WIDTH_SLOT),
    )
    height = _integer_input(
        "World height",
        draft.height,
        key=_widget_key(parent.revision_id, WORLD_HEIGHT_SLOT),
    )
    geography_options = ("uniform", "two_patches")
    geography = st.selectbox(
        "Resource geography",
        geography_options,
        index=_option_index(geography_options, draft.resource_geography),
        format_func=_humanize,
        key=_widget_key(parent.revision_id, REFERENCE_RESOURCE_GEOGRAPHY_SLOT),
    )

    st.markdown("#### Population")
    founder_population = _integer_input(
        "Founder population",
        draft.founder_population,
        key=_widget_key(parent.revision_id, FOUNDER_POPULATION_SLOT),
    )
    founder_energy = _integer_input(
        "Founder starting energy",
        draft.founder_energy,
        key=_widget_key(parent.revision_id, FOUNDER_ENERGY_SLOT),
    )

    st.markdown("#### Movement & sensing")
    max_speed = _integer_input(
        "Founder maximum speed",
        draft.max_speed,
        key=_widget_key(parent.revision_id, REFERENCE_MAX_SPEED_SLOT),
    )
    sensory_range = _integer_input(
        "Founder sensory range",
        draft.sensory_range,
        key=_widget_key(parent.revision_id, SENSORY_RANGE_SLOT),
    )
    sensory_accuracy = _integer_input(
        "Founder sensory accuracy",
        draft.sensory_accuracy,
        key=_widget_key(parent.revision_id, SENSORY_ACCURACY_SLOT),
    )
    movement_options = ("moore", "von_neumann", "uniform", "gaussian")
    movement = st.selectbox(
        "Exploration movement",
        movement_options,
        index=_option_index(movement_options, draft.exploration_movement),
        format_func=_humanize,
        key=_widget_key(parent.revision_id, EXPLORATION_MOVEMENT_SLOT),
    )

    st.markdown("#### Run")
    horizon = _integer_input(
        "Run horizon",
        draft.horizon,
        key=_widget_key(parent.revision_id, HORIZON_SLOT),
    )
    seed = _integer_input(
        "Random seed",
        draft.seed,
        key=_widget_key(parent.revision_id, REFERENCE_SEED_SLOT),
    )

    required_guided = {
        WORLD_WIDTH_SLOT,
        WORLD_HEIGHT_SLOT,
        FOUNDER_POPULATION_SLOT,
        FOUNDER_ENERGY_SLOT,
        HORIZON_SLOT,
        REFERENCE_SEED_SLOT,
        REFERENCE_MAX_SPEED_SLOT,
        SENSORY_RANGE_SLOT,
        SENSORY_ACCURACY_SLOT,
        EXPLORATION_MOVEMENT_SLOT,
        REFERENCE_RESOURCE_GEOGRAPHY_SLOT,
    }
    if not required_guided <= visible:
        raise RuntimeError(
            "Current WB4 Guided metadata no longer matches the WU2 surface."
        )

    return attrs.evolve(
        draft,
        width=width,
        height=height,
        founder_population=founder_population,
        founder_energy=founder_energy,
        horizon=horizon,
        seed=seed,
        max_speed=max_speed,
        sensory_range=sensory_range,
        sensory_accuracy=sensory_accuracy,
        exploration_movement=movement,
        resource_geography=geography,
    )


def _render_reference_advanced(
    parent: ReferenceStudyRevision,
    draft: ReferenceEcologyIntent,
) -> ReferenceEcologyIntent:
    visible = {
        item.slot_id for item in reference_slots_for_disclosure(draft, "Advanced")
    }

    st.markdown("#### Advanced movement")
    gaussian = draft.gaussian_standard_deviation
    if GAUSSIAN_STDDEV_SLOT in visible:
        gaussian = _integer_input(
            "Gaussian standard deviation",
            gaussian,
            key=_widget_key(parent.revision_id, GAUSSIAN_STDDEV_SLOT),
        )

    st.markdown("#### Advanced resources")
    resource_amount = _integer_input(
        "Renewable resource amount",
        draft.resource_generation_amount,
        key=_widget_key(parent.revision_id, RESOURCE_AMOUNT_SLOT),
    )
    deposits = _integer_input(
        "Resource deposits per step",
        draft.resource_deposits_per_step,
        key=_widget_key(parent.revision_id, RESOURCE_DEPOSITS_SLOT),
    )

    patch_values = (
        draft.patch_1_center_x,
        draft.patch_1_center_y,
        draft.patch_1_radius,
        draft.patch_2_center_x,
        draft.patch_2_center_y,
        draft.patch_2_radius,
    )
    patch_slots = (
        PATCH_1_X_SLOT,
        PATCH_1_Y_SLOT,
        PATCH_1_RADIUS_SLOT,
        PATCH_2_X_SLOT,
        PATCH_2_Y_SLOT,
        PATCH_2_RADIUS_SLOT,
    )
    patch_labels = (
        "Patch 1 center x",
        "Patch 1 center y",
        "Patch 1 radius",
        "Patch 2 center x",
        "Patch 2 center y",
        "Patch 2 radius",
    )
    mutable_patch = list(patch_values)
    for index, slot_id in enumerate(patch_slots):
        if slot_id in visible:
            mutable_patch[index] = _integer_input(
                patch_labels[index],
                mutable_patch[index],
                key=_widget_key(parent.revision_id, slot_id),
            )

    st.markdown("#### Evolution / inheritance")
    mutation_enabled = st.checkbox(
        "Mutation enabled",
        value=bool(draft.mutation_enabled),
        key=_widget_key(parent.revision_id, MUTATION_ENABLED_SLOT),
    )
    draft_with_dependencies = attrs.evolve(
        draft,
        gaussian_standard_deviation=gaussian,
        resource_generation_amount=resource_amount,
        resource_deposits_per_step=deposits,
        patch_1_center_x=mutable_patch[0],
        patch_1_center_y=mutable_patch[1],
        patch_1_radius=mutable_patch[2],
        patch_2_center_x=mutable_patch[3],
        patch_2_center_y=mutable_patch[4],
        patch_2_radius=mutable_patch[5],
        mutation_enabled=mutation_enabled,
    )
    visible = {
        item.slot_id
        for item in reference_slots_for_disclosure(draft_with_dependencies, "Advanced")
    }
    mutation_probability = draft.mutation_probability_ppm
    mutation_max_change = draft.mutation_max_change
    if MUTATION_PROBABILITY_SLOT in visible:
        mutation_probability = _integer_input(
            "Mutation probability (ppm)",
            mutation_probability,
            key=_widget_key(parent.revision_id, MUTATION_PROBABILITY_SLOT),
        )
    if MUTATION_MAX_CHANGE_SLOT in visible:
        mutation_max_change = _integer_input(
            "Mutation maximum change",
            mutation_max_change,
            key=_widget_key(parent.revision_id, MUTATION_MAX_CHANGE_SLOT),
        )
    recombination = _integer_input(
        "Recombination probability (ppm)",
        draft.recombination_probability_ppm,
        key=_widget_key(parent.revision_id, RECOMBINATION_PROBABILITY_SLOT),
    )
    return attrs.evolve(
        draft_with_dependencies,
        mutation_probability_ppm=mutation_probability,
        mutation_max_change=mutation_max_change,
        recombination_probability_ppm=recombination,
    )


def _render_b3(
    revision: B3StudyRevision,
    diff_parent: ConcreteWorkbenchArtifact | None,
    new_revision_id: Callable[[str], str],
) -> B3StudyRevision | None:
    readiness = assess_b3_readiness(revision.intent, revision.evidence_plan)
    design, identity = st.columns((3, 2))
    with design:
        if revision.scenario_identity is not None:
            st.success("Validated B3 flagship")
        else:
            st.warning(
                "B3-derived radius-sensitivity Study — not the validated radius-1 "
                "flagship identity."
            )
        st.subheader("Scientific design")
        _render_named_manifest_values(revision.manifest, _B3_SUMMARY)

    with identity:
        _render_readiness(readiness)
        st.subheader("Scenario identity")
        _display_value("Scenario origin", revision.scenario_origin)
        _display_value(
            "Validated scenario identity",
            (
                revision.scenario_identity
                if revision.scenario_identity is not None
                else "None"
            ),
        )
        if revision.scenario_identity is None:
            st.caption(
                "The B3 origin is preserved, but the validated radius-1 identity and "
                "its representative/headline handoff are not inherited."
            )
        _render_provenance(revision)

    if revision.scenario_identity is not None:
        st.caption(
            "Radius sensitivity is a scientific fork action, not an editable B3 "
            "form field."
        )
        if st.button(
            "Fork radius-sensitivity Study",
            type="primary",
            key=_widget_key(revision.revision_id, "b3-radius-fork"),
        ):
            return save_b3_radius_sensitivity_child(
                revision,
                revision_id=new_revision_id("b3-radius2"),
            )

    _render_parent_diff(diff_parent, revision)
    return None


def _render_controlled_meaning(
    parent: StudyRevision,
    draft: ControlledLocomotionIntent,
    preview: Any | None,
) -> None:
    st.subheader("Scientific meaning")
    if preview is None:
        st.info(
            "This draft is not currently resolvable. The saved parent manifest remains "
            "the authoritative scientific meaning."
        )
        manifest = parent.manifest
    else:
        manifest = preview
    st.markdown("#### Explicit selections")
    _render_pairs(manifest.explicit_values)
    st.markdown("#### Derived")
    _render_selected_values(manifest, _CONTROLLED_DYNAMIC_DERIVED)
    st.markdown("#### Frozen assumptions")
    _render_selected_values(manifest, _CONTROLLED_FROZEN)
    _render_provenance(
        parent,
        preview_manifest=preview if draft != parent.intent else None,
    )


def _render_reference_meaning(
    parent: ReferenceStudyRevision,
    draft: ReferenceEcologyIntent,
    preview: Any | None,
) -> None:
    st.subheader("Scientific meaning")
    if preview is None:
        st.info(
            "This draft is not currently resolvable. The saved parent manifest remains "
            "the authoritative scientific meaning."
        )
        manifest = parent.manifest
    else:
        manifest = preview
    st.markdown("#### Explicit selections")
    _render_pairs(manifest.explicit_values)
    st.markdown("#### Derived")
    _render_selected_values(manifest, _REFERENCE_DYNAMIC_DERIVED)
    st.markdown("#### Frozen assumptions")
    _render_selected_values(manifest, _REFERENCE_FROZEN)
    _render_provenance(
        parent,
        preview_manifest=preview if draft != parent.intent else None,
    )


def _render_parent_diff(
    diff_parent: ConcreteWorkbenchArtifact | None,
    current: ConcreteWorkbenchArtifact,
) -> None:
    parent_revision_id = getattr(current, "parent_revision_id", None)
    if parent_revision_id is None:
        return
    if diff_parent is None:
        st.caption(
            f"Parent revision `{parent_revision_id}` is recorded, but its artifact is "
            "not loaded in this session; semantic diff is unavailable."
        )
        return
    if getattr(diff_parent, "revision_id", None) != parent_revision_id:
        return

    diff = simulation_semantic_diff(
        cast(StudyRevision | ReferenceStudyRevision | B3StudyRevision, diff_parent),
        cast(StudyRevision | ReferenceStudyRevision | B3StudyRevision, current),
    )
    st.divider()
    st.subheader("Changes from parent")
    _render_change_section("Explicit changes", diff.explicit_changes)
    _render_change_section("Derived changes", diff.derived_changes)

    if isinstance(diff, B3CuratedDiff):
        if diff.scenario_identity_change is not None:
            st.markdown("#### Identity changes")
            _display_change(
                "Validated scenario identity",
                diff.scenario_identity_change.before,
                diff.scenario_identity_change.after,
            )
            if diff.scenario_identity_change.after is None:
                st.warning(
                    "The child remains B3-derived, but it is not the validated "
                    "radius-1 flagship."
                )
        if diff.unchanged_frozen_slots:
            with st.expander("Unchanged frozen assumptions"):
                for slot_id in diff.unchanged_frozen_slots:
                    st.write(f"• {semantic_slot_label(slot_id)}")
    elif isinstance(diff, (ControlledLocomotionDiff, ReferenceEcologyDiff)):
        st.caption(
            "Frozen recipe identity remains unchanged; derived differences above are "
            "reported by the existing concrete Workbench semantic-diff contract."
        )


def _render_change_section(title: str, changes: tuple[object, ...]) -> None:
    st.markdown(f"#### {title}")
    if not changes:
        st.caption("No changes.")
        return
    for change in changes:
        _display_change(
            semantic_slot_label(cast(str, getattr(change, "slot_id"))),
            getattr(change, "before"),
            getattr(change, "after"),
        )


def _display_change(label: str, before: object, after: object) -> None:
    st.write(f"**{label}:** `{_format_value(before)}` → `{_format_value(after)}`")


def _render_readiness(readiness: WorkbenchReadiness) -> None:
    st.subheader("Readiness")
    if readiness.state == "ready":
        st.success("Ready")
    elif readiness.state == "draft":
        st.info("Draft")
    else:
        st.error("Blocked")
    for diagnostic in readiness.diagnostics:
        st.write(diagnostic.message)
        if diagnostic.remediation is not None:
            st.caption(diagnostic.remediation)


def _render_slot_diagnostics(readiness: WorkbenchReadiness) -> None:
    if not readiness.diagnostics:
        return
    st.markdown("#### Authoring diagnostics")
    for diagnostic in readiness.diagnostics:
        label = (
            semantic_slot_label(diagnostic.slot_id)
            if diagnostic.slot_id is not None
            else "Study"
        )
        st.error(f"{label}: {diagnostic.message}")


def _render_pairs(values: tuple[tuple[str, object], ...]) -> None:
    for slot_id, value in values:
        _display_value(semantic_slot_label(slot_id), value)


def _render_selected_values(manifest: Any, slot_ids: tuple[str, ...]) -> None:
    for slot_id in slot_ids:
        try:
            value = manifest.derived_value(slot_id)
        except KeyError:
            continue
        _display_value(semantic_slot_label(slot_id), value)


def _render_named_manifest_values(
    manifest: Any,
    entries: tuple[tuple[str, str], ...],
) -> None:
    for label, slot_id in entries:
        try:
            value = manifest.derived_value(slot_id)
        except KeyError:
            continue
        _display_value(label, value)


def _display_value(label: str, value: object) -> None:
    st.write(f"**{label}:** `{_format_value(value)}`")


def _render_provenance(revision: Any, preview_manifest: Any | None = None) -> None:
    manifest = revision.manifest
    with st.expander("Scientific provenance"):
        _display_value("Revision ID", revision.revision_id)
        if revision.parent_revision_id is not None:
            _display_value("Parent revision", revision.parent_revision_id)
        _display_value("Saved manifest digest", manifest.digest)
        _display_value("Recipe", f"{manifest.recipe_id} v{manifest.recipe_version}")
        _display_value(
            "Compiler",
            f"{manifest.compiler_id} v{manifest.compiler_version}",
        )
        _display_value(
            "Engine compatibility",
            f"{manifest.engine_distribution}=={manifest.engine_version}",
        )
        if preview_manifest is not None and preview_manifest.digest != manifest.digest:
            _display_value("Unsaved preview digest", preview_manifest.digest)


def _controlled_draft(parent: StudyRevision) -> ControlledLocomotionIntent:
    draft = st.session_state.get(_DRAFT_INTENT_KEY)
    if (
        st.session_state.get(_DRAFT_REVISION_KEY) != parent.revision_id
        or not isinstance(draft, ControlledLocomotionIntent)
    ):
        draft = parent.intent
        _store_draft(parent.revision_id, draft)
    return draft


def _reference_draft(parent: ReferenceStudyRevision) -> ReferenceEcologyIntent:
    draft = st.session_state.get(_DRAFT_INTENT_KEY)
    if (
        st.session_state.get(_DRAFT_REVISION_KEY) != parent.revision_id
        or not isinstance(draft, ReferenceEcologyIntent)
    ):
        draft = parent.intent
        _store_draft(parent.revision_id, draft)
    return draft


def _store_draft(revision_id: str, draft: object) -> None:
    st.session_state[_DRAFT_REVISION_KEY] = revision_id
    st.session_state[_DRAFT_INTENT_KEY] = draft


def _integer_input(label: str, value: int | None, *, key: str) -> int | None:
    raw = st.number_input(label, value=value, step=1, key=key)
    return None if raw is None else int(raw)


def _option_index(options: tuple[str, ...], value: str | None) -> int:
    if value in options:
        return options.index(cast(str, value))
    return 0


def _widget_key(revision_id: str, name: str) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in name)
    revision = "".join(
        character if character.isalnum() else "_" for character in revision_id
    )
    return f"wu2_{revision}_{safe}"


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


def _format_value(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "on" if value else "off"
    return str(value)


__all__ = [
    "clear_simulation_authoring_state",
    "render_simulation_page",
]
