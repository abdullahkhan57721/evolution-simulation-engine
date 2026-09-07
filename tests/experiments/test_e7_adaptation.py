"""Tests for E7 mutation-driven adaptation and convergence evidence."""

from __future__ import annotations

from evo_engine.experiments.e7_adaptation import (
    E7_REFERENCE_REGION,
    E7_SPEED_DOMAIN,
    build_e7_treatment,
    e7_distribution_overlap,
    run_e7_replicate,
    summarize_e7_starting_condition,
)


def test_e7_treatment_preserves_controlled_nonfocal_biology() -> None:
    """Test E7 changes only declared population/resource/horizon/focal settings."""
    treatment = build_e7_treatment(starting_speed=3)
    config = treatment.to_config(seed=17)

    assert len(config.founders) == 8
    assert {founder.max_speed for founder in config.founders} == {3}
    assert sum(deposit.amount for deposit in config.resource_deposits) == 3360
    assert config.max_steps == 60
    assert config.initial_energy == 100
    assert config.body_mass == 1
    assert config.locomotion_cost_coefficient == 1
    assert config.locomotion_distance_exponent == 2
    assert config.resource_request_amount == 10
    assert config.reproduction_minimum_energy == 140
    assert config.reproduction_energy_investment == 20
    assert treatment.mutation_policy.probability_ppm == 1_000_000
    assert treatment.mutation_policy.max_change == 1


def test_e7_forced_focal_mutation_is_evidence_derived_and_bounded() -> None:
    """Test committed pedigree/trait evidence exposes only ±1 focal transitions."""
    treatment = build_e7_treatment(
        starting_speed=3,
        horizon=25,
        mutation_probability_ppm=1_000_000,
    )

    outcome = run_e7_replicate(
        treatment,
        seed=17,
        run_role="discovery",
    )

    assert len(outcome.trait_trajectory) == 26
    assert outcome.initial_distribution.count(3) == 8
    assert outcome.birth_count > 0
    assert outcome.realized_mutation_count == outcome.birth_count
    assert all(transition.changed for transition in outcome.mutation_transitions)
    assert all(
        abs(transition.offspring_speed - transition.parent_speed) == 1
        for transition in outcome.mutation_transitions
    )
    for point in outcome.trait_trajectory:
        assert len(point.counts) == len(E7_SPEED_DOMAIN)
        assert sum(point.counts) == point.population_size
        assert all(0 <= speed < len(E7_SPEED_DOMAIN) for speed in point.modal_speeds)


def test_e7_endpoint_summary_keeps_run_as_replicate() -> None:
    """Test endpoint aggregation weights each run once and preserves distributions."""
    treatment = build_e7_treatment(
        starting_speed=3,
        horizon=20,
        mutation_probability_ppm=1_000_000,
    )
    outcomes = tuple(
        run_e7_replicate(treatment, seed=seed, run_role="discovery")
        for seed in (17, 29)
    )

    summary = summarize_e7_starting_condition(outcomes)

    assert summary.replicate_count == 2
    assert summary.seeds == (17, 29)
    assert summary.defined_endpoint_count + summary.extinction_count == 2
    if summary.defined_endpoint_count:
        assert all(value is not None for value in summary.endpoint_distribution)
        assert (
            abs(sum(value or 0.0 for value in summary.endpoint_distribution) - 1.0)
            < 1e-9
        )
    assert e7_distribution_overlap(summary, summary) == 1.0


def test_e7_reference_region_is_bounded_inside_legal_domain() -> None:
    """Test the scientific reference region is narrower than the mutation domain."""
    assert E7_REFERENCE_REGION == (2, 3, 4)
    assert E7_SPEED_DOMAIN[0] == 0
    assert E7_SPEED_DOMAIN[-1] == 20
    assert min(E7_REFERENCE_REGION) > E7_SPEED_DOMAIN[0]
    assert max(E7_REFERENCE_REGION) < E7_SPEED_DOMAIN[-1]
