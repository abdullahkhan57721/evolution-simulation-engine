"""Focused WU3 tests for Evidence and concrete Experiment UI helpers."""

from __future__ import annotations

import pytest

from evo_engine.ui.evidence_authoring import (
    evidence_advisories_for_artifact,
    evidence_options,
    requested_evidence_ids,
    save_evidence_child,
)
from evo_engine.ui.experiment_authoring import (
    b3_case_counts,
    environment_run_rows,
    max_speed_run_rows,
    update_environment_selection_comparison,
    update_max_speed_sweep,
)
from evo_engine.ui.study_shell import (
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
)
from evo_engine.workbench import (
    B3_REQUIRED_EVIDENCE_IDS,
    E3_SWEEP_REQUIRED_EVIDENCE,
    E4_COMPARISON_REQUIRED_EVIDENCE,
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    REFERENCE_SPATIAL_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
)


def test_controlled_evidence_change_creates_child_without_mutating_parent() -> None:
    parent = new_controlled_run(revision_id="controlled-parent")

    child = save_evidence_child(
        parent,
        requested=(POPULATION_EVIDENCE_ID,),
        revision_id="controlled-child",
    )

    assert parent.evidence_plan.requested == (
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
    )
    assert child.parent_revision_id == parent.revision_id
    assert child.evidence_plan.requested == (POPULATION_EVIDENCE_ID,)
    assert child.intent == parent.intent
    assert child.manifest == parent.manifest


def test_reference_evidence_options_and_spatial_advisory_use_wb4_contract() -> None:
    parent = new_reference_ecology(revision_id="reference-parent")
    requested = (*parent.evidence_plan.requested, REFERENCE_SPATIAL_EVIDENCE_ID)
    child = save_evidence_child(
        parent,
        requested=requested,
        revision_id="reference-child",
    )

    labels = {option.label for option in evidence_options(child)}
    advisories = evidence_advisories_for_artifact(child)

    assert "Spatial history" in labels
    assert child.parent_revision_id == parent.revision_id
    assert len(advisories) == 1
    assert advisories[0].code == "high-volume-spatial-evidence"
    assert advisories[0].evidence_id == REFERENCE_SPATIAL_EVIDENCE_ID


def test_b3_and_controlled_experiment_evidence_are_locked_to_authoritative_sets() -> (
    None
):
    b3 = new_b3_flagship(revision_id="b3")
    e3 = new_max_speed_sweep()
    e4 = new_environment_selection_comparison()

    assert requested_evidence_ids(b3) == B3_REQUIRED_EVIDENCE_IDS
    assert all(option.required for option in evidence_options(b3))
    assert set(requested_evidence_ids(e3)) == E3_SWEEP_REQUIRED_EVIDENCE
    assert all(option.required for option in evidence_options(e3))
    assert set(requested_evidence_ids(e4)) == E4_COMPARISON_REQUIRED_EVIDENCE
    assert all(option.required for option in evidence_options(e4))


def test_e3_authoring_preserves_factor_identity_and_authoritative_expansion() -> None:
    definition = new_max_speed_sweep()
    candidate = update_max_speed_sweep(
        definition,
        levels=(1, 3, 5),
        seeds=(17, 29),
    )
    rows = max_speed_run_rows(candidate)

    assert candidate.factor_slot_id == MAX_SPEED_SLOT
    assert candidate.base_intent.max_speed is None
    assert candidate.base_intent.seed is None
    assert [(row.maximum_speed, row.seed) for row in rows] == [
        (1, 17),
        (1, 29),
        (3, 17),
        (3, 29),
        (5, 17),
        (5, 29),
    ]


@pytest.mark.parametrize(
    ("levels", "seeds", "message"),
    (
        ((1, 1), (17,), "duplicates"),
        ((0,), (17,), "characterized Workbench"),
        ((1,), (17, 17), "duplicates"),
    ),
)
def test_e3_invalid_levels_and_seeds_fail_through_definition_contract(
    levels: tuple[int, ...],
    seeds: tuple[int, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        update_max_speed_sweep(new_max_speed_sweep(), levels=levels, seeds=seeds)


def test_e4_authoring_preserves_fixed_factor_roles_composition_and_counterbalance() -> (
    None
):
    definition = update_environment_selection_comparison(
        new_environment_selection_comparison(),
        seeds=(101, 202),
    )
    rows = environment_run_rows(definition)

    assert definition.factor_slot_id == RESOURCE_GEOGRAPHY_SLOT
    assert definition.control_environment == "local_resource"
    assert definition.treatment_environment == "separated_corridor"
    assert definition.focal_speeds == (1, 3, 9)
    assert [(row.seed, row.role) for row in rows] == [
        (101, "control"),
        (101, "treatment"),
        (202, "control"),
        (202, "treatment"),
    ]
    for control, treatment in zip(rows[::2], rows[1::2], strict=True):
        assert control.seed == treatment.seed
        assert control.founder_speed_order == treatment.founder_speed_order
        assert control.standing_focal_composition == (1, 3, 9)
        assert treatment.standing_focal_composition == (1, 3, 9)


def test_b3_case_counts_come_from_authoritative_compilation() -> None:
    counts = b3_case_counts(new_b3_flagship(revision_id="b3-counts"))

    assert counts.confirmation_pairs > 0
    assert counts.radius_sensitivity_runs > 0
    assert counts.counterbalanced_pairs > 0
    assert counts.total_simulations == (
        counts.confirmation_pairs * 2
        + counts.radius_sensitivity_runs
        + counts.counterbalanced_pairs * 2
    )
