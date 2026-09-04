"""Tests for E4 standing-variation selection evidence and controls."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.experiments.e4_selection import (
    E4_FOCAL_SPEEDS,
    E4_FOUNDER_ORDERS,
    E4_REVERSED_FOUNDER_ORDER,
    build_e4_treatment,
    founder_order_for_replicate,
    run_e4_replicate,
    run_e4_seed_set,
    summarize_e4_environment,
    validate_e4_environment_treatment_integrity,
    validate_e4_founder_order_integrity,
)


def test_e4_treatment_uses_equal_colocated_standing_variation() -> None:
    """Test E4 begins with one co-located founder for each focal speed."""
    treatment = build_e4_treatment(environment="separated_corridor")
    config = treatment.to_config(seed=17)

    assert tuple(founder.max_speed for founder in config.founders) == E4_FOCAL_SPEEDS
    assert len({(founder.x, founder.y) for founder in config.founders}) == 1
    assert len(config.founders) == 3


def test_e4_founder_counterbalance_rotates_speed_to_id_order() -> None:
    """Test the predeclared counterbalance cycles through all three assignments."""
    assert tuple(founder_order_for_replicate(index) for index in range(6)) == (
        E4_FOUNDER_ORDERS + E4_FOUNDER_ORDERS
    )


def test_e4_environment_integrity_allows_only_resource_environment() -> None:
    """Test matched E4 environments reject an unintended founder-order change."""
    control = build_e4_treatment(
        environment="local_resource",
        founder_speed_order=E4_FOUNDER_ORDERS[1],
    )
    treatment = build_e4_treatment(
        environment="separated_corridor",
        founder_speed_order=E4_FOUNDER_ORDERS[1],
    )

    validate_e4_environment_treatment_integrity(control, treatment)

    invalid = attrs.evolve(treatment, founder_speed_order=E4_FOUNDER_ORDERS[2])
    with pytest.raises(ValueError, match="outside E3 resource environment"):
        validate_e4_environment_treatment_integrity(control, invalid)


def test_e4_founder_order_integrity_allows_only_speed_id_assignment() -> None:
    """Test counterbalance treatments preserve the resource environment."""
    control = build_e4_treatment(
        environment="separated_corridor",
        founder_speed_order=E4_FOUNDER_ORDERS[0],
    )
    treatment = build_e4_treatment(
        environment="separated_corridor",
        founder_speed_order=E4_REVERSED_FOUNDER_ORDER,
    )

    validate_e4_founder_order_integrity(control, treatment)

    invalid = attrs.evolve(treatment, environment="local_resource")
    with pytest.raises(ValueError, match="outside founder speed-to-ID order"):
        validate_e4_founder_order_integrity(control, invalid)


def test_e4_local_replicate_preserves_full_composition_and_closes_energy() -> None:
    """Test a real local run records complete frequencies and exact energy accounting."""
    outcome = run_e4_replicate(
        build_e4_treatment(
            environment="local_resource",
            founder_speed_order=E4_FOUNDER_ORDERS[1],
        ),
        seed=17,
    )

    assert outcome.initial_composition.counts == (1, 1, 1)
    assert outcome.initial_composition.frequencies == pytest.approx(
        (1 / 3, 1 / 3, 1 / 3)
    )
    assert outcome.final_composition.population_size > 0
    assert outcome.boundary_clipping_event_count == 0
    assert outcome.energy_budget_residual == 0
    assert sum(outcome.final_composition.counts) == outcome.final_composition.population_size
    assert all(
        point.population_size == sum(point.counts) for point in outcome.focal_trajectory
    )


def test_e4_corridor_replicate_separates_selection_from_mechanism_evidence() -> None:
    """Test one corridor run exposes frequency change and strategy mechanisms separately."""
    outcome = run_e4_replicate(
        build_e4_treatment(environment="separated_corridor"),
        seed=17,
    )

    assert outcome.initial_composition.counts == (1, 1, 1)
    assert outcome.boundary_clipping_event_count == 0
    assert outcome.energy_budget_residual == 0
    assert all(
        mechanism.max_speed in E4_FOCAL_SPEEDS for mechanism in outcome.mechanisms
    )
    assert (
        sum(mechanism.cumulative_birth_count for mechanism in outcome.mechanisms) >= 0
    )
    assert (
        sum(
            mechanism.total_locomotion_energy_expenditure
            for mechanism in outcome.mechanisms
        )
        > 0
    )


def test_e4_environment_summary_preserves_run_level_replicates() -> None:
    """Test E4 summaries aggregate runs rather than organisms."""
    outcomes = run_e4_seed_set(
        environment="local_resource",
        seeds=(17, 29, 41),
        run_role="confirmation",
    )

    summary = summarize_e4_environment(outcomes)

    assert summary.replicate_count == 3
    assert summary.seeds == (17, 29, 41)
    assert summary.founder_speed_orders == E4_FOUNDER_ORDERS
    assert summary.defined_endpoint_count == 3
    assert summary.extinction_count == 0


def test_e4_seed_set_rejects_duplicate_pseudoreplicates() -> None:
    """Test duplicate seeds cannot masquerade as independent E4 replicates."""
    with pytest.raises(ValueError, match="must not contain duplicates"):
        run_e4_seed_set(
            environment="local_resource",
            seeds=(17, 17),
            run_role="confirmation",
        )
