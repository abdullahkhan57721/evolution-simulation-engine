"""Focused WU2 tests for concrete Simulation authoring helpers."""

from __future__ import annotations

import attrs

from evo_engine.ui.simulation_authoring import (
    normalize_reference_draft,
    reference_has_expert_controls,
    reference_slots_for_disclosure,
    save_b3_radius_sensitivity_child,
    save_controlled_child,
    save_reference_child,
    simulation_semantic_diff,
)
from evo_engine.ui.study_shell import (
    new_b3_flagship,
    new_controlled_run,
    new_reference_ecology,
)
from evo_engine.workbench import (
    B3CuratedDiff,
    B3_VALIDATED_SCENARIO_ID,
    ControlledLocomotionDiff,
    ControlledLocomotionIntent,
    ReferenceEcologyDiff,
)
from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_ENABLED_SLOT,
    RESOURCE_AMOUNT_SLOT,
)


def test_reference_disclosure_uses_current_support_metadata_and_applicability() -> None:
    revision = new_reference_ecology(revision_id="reference-disclosure")
    guided = reference_slots_for_disclosure(revision.intent, "Guided")
    advanced = reference_slots_for_disclosure(revision.intent, "Advanced")

    assert guided
    assert all(item.support_tier == "guided" for item in guided)
    assert {item.slot_id for item in guided} < {item.slot_id for item in advanced}
    assert RESOURCE_AMOUNT_SLOT in {item.slot_id for item in advanced}
    assert MUTATION_ENABLED_SLOT in {item.slot_id for item in advanced}
    assert GAUSSIAN_STDDEV_SLOT not in {item.slot_id for item in advanced}
    assert reference_has_expert_controls() is False


def test_reference_conditional_values_are_cleared_only_when_wb4_marks_them_inactive(
) -> None:
    revision = new_reference_ecology(revision_id="reference-normalization")
    stale = attrs.evolve(
        revision.intent,
        exploration_movement="moore",
        gaussian_standard_deviation=7,
        resource_geography="uniform",
        patch_1_center_x=1,
        patch_1_center_y=1,
        patch_1_radius=2,
        patch_2_center_x=3,
        patch_2_center_y=3,
        patch_2_radius=2,
        mutation_enabled=False,
        mutation_probability_ppm=50_000,
        mutation_max_change=2,
    )

    normalized = normalize_reference_draft(stale)

    assert normalized.gaussian_standard_deviation is None
    assert normalized.patch_1_center_x is None
    assert normalized.patch_1_center_y is None
    assert normalized.patch_1_radius is None
    assert normalized.patch_2_center_x is None
    assert normalized.patch_2_center_y is None
    assert normalized.patch_2_radius is None
    assert normalized.mutation_probability_ppm is None
    assert normalized.mutation_max_change is None


def test_controlled_edit_creates_immutable_child_and_uses_existing_semantic_diff(
) -> None:
    parent = new_controlled_run(revision_id="controlled-parent")
    original_json = parent.to_json()
    draft = ControlledLocomotionIntent(
        max_speed=4,
        resource_geography=parent.intent.resource_geography,
        seed=parent.intent.seed,
    )

    child = save_controlled_child(
        parent,
        draft=draft,
        revision_id="controlled-child",
    )
    diff = simulation_semantic_diff(parent, child)

    assert parent.to_json() == original_json
    assert child.parent_revision_id == parent.revision_id
    assert child.intent.max_speed == 4
    assert isinstance(diff, ControlledLocomotionDiff)
    assert any(change.slot_id.endswith("max-speed") for change in diff.explicit_changes)


def test_reference_save_uses_concrete_fork_and_drops_stale_hidden_state() -> None:
    parent = new_reference_ecology(revision_id="reference-parent")
    original_json = parent.to_json()
    new_speed = 4 if parent.intent.max_speed != 4 else 3
    draft = attrs.evolve(
        parent.intent,
        max_speed=new_speed,
        exploration_movement="moore",
        gaussian_standard_deviation=7,
        resource_geography="uniform",
        patch_1_center_x=1,
        patch_1_center_y=1,
        patch_1_radius=2,
        patch_2_center_x=3,
        patch_2_center_y=3,
        patch_2_radius=2,
        mutation_enabled=False,
        mutation_probability_ppm=50_000,
        mutation_max_change=2,
    )

    child = save_reference_child(
        parent,
        draft=draft,
        revision_id="reference-child",
    )
    diff = simulation_semantic_diff(parent, child)

    assert parent.to_json() == original_json
    assert child.parent_revision_id == parent.revision_id
    assert child.intent.max_speed == new_speed
    assert child.intent.gaussian_standard_deviation is None
    assert child.intent.patch_1_center_x is None
    assert child.intent.patch_1_center_y is None
    assert child.intent.patch_1_radius is None
    assert child.intent.patch_2_center_x is None
    assert child.intent.patch_2_center_y is None
    assert child.intent.patch_2_radius is None
    assert child.intent.mutation_probability_ppm is None
    assert child.intent.mutation_max_change is None
    assert isinstance(diff, ReferenceEcologyDiff)
    assert diff.explicit_changes


def test_b3_radius_fork_preserves_origin_and_loses_validated_identity() -> None:
    parent = new_b3_flagship(revision_id="b3-parent")
    assert parent.scenario_identity == B3_VALIDATED_SCENARIO_ID

    child = save_b3_radius_sensitivity_child(
        parent,
        revision_id="b3-radius-two",
    )
    diff = simulation_semantic_diff(parent, child)

    assert child.parent_revision_id == parent.revision_id
    assert child.scenario_origin == parent.scenario_origin
    assert child.scenario_identity is None
    assert isinstance(diff, B3CuratedDiff)
    assert diff.scenario_identity_change is not None
    assert diff.scenario_identity_change.before == B3_VALIDATED_SCENARIO_ID
    assert diff.scenario_identity_change.after is None
