"""Tests for E3 controlled ecological-performance measurement and integrity."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.experiments.e3_performance import (
    E3_HORIZON,
    E3_TOTAL_INITIAL_RESOURCES,
    build_e3_treatment,
    run_e3_replicate,
    run_e3_replicates,
    summarize_e3_treatment,
    validate_e3_cost_sensitivity_integrity,
    validate_e3_environment_treatment_integrity,
    validate_e3_speed_treatment_integrity,
)


def test_e3_environments_hold_total_resource_amount_fixed() -> None:
    """Test local and corridor environments differ in geography, not resource total."""
    local = build_e3_treatment(max_speed=4, environment="local_resource")
    corridor = build_e3_treatment(max_speed=4, environment="separated_corridor")

    assert sum(amount for _, _, amount in local.resource_deposits) == (
        E3_TOTAL_INITIAL_RESOURCES
    )
    assert sum(amount for _, _, amount in corridor.resource_deposits) == (
        E3_TOTAL_INITIAL_RESOURCES
    )
    assert local.resource_deposits != corridor.resource_deposits


def test_e3_speed_integrity_allows_only_monomorphic_capacity_difference() -> None:
    """Test speed treatments reject a hidden environmental or energetic change."""
    control = build_e3_treatment(max_speed=2, environment="separated_corridor")
    treatment = build_e3_treatment(max_speed=7, environment="separated_corridor")

    validate_e3_speed_treatment_integrity(control, treatment)

    invalid = attrs.evolve(treatment, locomotion_cost_coefficient=0)
    with pytest.raises(ValueError, match="outside monomorphic max_speed"):
        validate_e3_speed_treatment_integrity(control, invalid)


def test_e3_environment_integrity_allows_only_resource_geography_difference() -> None:
    """Test matched-speed environments reject an unintended second difference."""
    control = build_e3_treatment(max_speed=4, environment="local_resource")
    treatment = build_e3_treatment(max_speed=4, environment="separated_corridor")

    validate_e3_environment_treatment_integrity(control, treatment)

    invalid = attrs.evolve(treatment, locomotion_cost_coefficient=0)
    with pytest.raises(ValueError, match="outside resource geography"):
        validate_e3_environment_treatment_integrity(control, invalid)


def test_e3_cost_sensitivity_changes_only_locomotion_use_cost() -> None:
    """Test zero-cost sensitivity preserves the frozen corridor treatment."""
    control = build_e3_treatment(max_speed=4, environment="separated_corridor")
    sensitivity = build_e3_treatment(
        max_speed=4,
        environment="separated_corridor",
        locomotion_cost_coefficient=0,
    )

    validate_e3_cost_sensitivity_integrity(control, sensitivity)

    invalid = attrs.evolve(sensitivity, max_speed=5)
    with pytest.raises(ValueError, match="outside locomotion cost coefficient"):
        validate_e3_cost_sensitivity_integrity(control, invalid)


def test_local_resource_replicate_has_no_travel_advantage_or_energy_residual() -> None:
    """Test the local-resource null uses committed evidence and closes energy."""
    outcome = run_e3_replicate(
        build_e3_treatment(max_speed=6, environment="local_resource"),
        seed=17,
    )

    assert outcome.provenance.seed == 17
    assert outcome.provenance.horizon_step_index == E3_HORIZON
    assert outcome.locomotion.total_realized_distance == 0.0
    assert outcome.locomotion.total_locomotion_energy_expenditure == 0
    assert outcome.total_resource_consumed > 0
    assert outcome.cumulative_birth_count > 0
    assert outcome.boundary_clipping_event_count == 0
    assert outcome.energy_budget_residual == 0
    assert outcome.energy_trajectory[0].step_index == 0
    assert outcome.energy_trajectory[-1].step_index == E3_HORIZON


def test_corridor_replicate_separates_travel_cost_resource_and_reproduction() -> None:
    """Test one corridor run exposes the full committed causal measurement ladder."""
    outcome = run_e3_replicate(
        build_e3_treatment(max_speed=3, environment="separated_corridor"),
        seed=17,
    )

    assert outcome.locomotion.total_realized_distance > 0.0
    assert outcome.locomotion.total_locomotion_energy_expenditure > 0
    assert outcome.total_resource_consumed > 0
    assert outcome.cumulative_birth_count >= 0
    assert outcome.final_population_size >= 0
    assert outcome.boundary_clipping_event_count == 0
    assert outcome.energy_budget_residual == 0

    for point in outcome.energy_trajectory:
        assert point.total_population_energy >= 0


def test_e3_treatment_summary_preserves_runs_as_replicates() -> None:
    """Test treatment aggregation keeps seed-level birth outcomes inspectable."""
    treatment = build_e3_treatment(max_speed=2, environment="separated_corridor")
    outcomes = run_e3_replicates(treatment, seeds=(17, 29))

    summary = summarize_e3_treatment(outcomes)

    assert summary.replicate_count == 2
    assert summary.seeds == (17, 29)
    assert summary.birth_counts == tuple(
        outcome.cumulative_birth_count for outcome in outcomes
    )
    assert summary.mean_cumulative_birth_count == sum(summary.birth_counts) / 2


def test_e3_replicate_seed_list_rejects_duplicate_pseudoreplicates() -> None:
    """Test duplicate seeds cannot masquerade as independent replicates."""
    treatment = build_e3_treatment(max_speed=2, environment="local_resource")

    with pytest.raises(ValueError, match="must not contain duplicates"):
        run_e3_replicates(treatment, seeds=(17, 17))
