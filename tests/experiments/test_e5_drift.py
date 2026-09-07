"""Tests for E5 finite-population lineage and weak-selection evidence."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.experiments.e5_drift import (
    E5_FOUNDER_COUNTS,
    E5_NEUTRAL_SPEED,
    E5_RESOURCE_PER_FOUNDER,
    E5_WEAK_PAIR,
    assignment_phase_for_replicate,
    build_e5_treatment,
    compare_e5_weak_to_neutral,
    run_e5_replicate,
    run_e5_seed_set,
    summarize_e5_regime,
    validate_e5_assignment_phase_integrity,
    validate_e5_founder_size_integrity,
    validate_e5_mode_integrity,
)


def test_neutral_labels_do_not_change_modeled_founder_biology() -> None:
    """Test neutral phase reversal changes analysis labels but not simulation config."""
    phase_a = build_e5_treatment(
        mode="neutral",
        founder_count=8,
        assignment_phase=0,
    )
    phase_b = build_e5_treatment(
        mode="neutral",
        founder_count=8,
        assignment_phase=1,
    )

    validate_e5_assignment_phase_integrity(phase_a, phase_b)
    assert phase_a.founder_groups != phase_b.founder_groups
    assert phase_a.to_config(seed=11) == phase_b.to_config(seed=11)
    assert set(phase_a.founder_speeds) == {E5_NEUTRAL_SPEED}


def test_weak_phase_reversal_counterbalances_speed_to_founder_id() -> None:
    """Test weak-selection phase reversal swaps only focal speed assignment order."""
    phase_a = build_e5_treatment(
        mode="weak_selection",
        founder_count=8,
        assignment_phase=0,
    )
    phase_b = build_e5_treatment(
        mode="weak_selection",
        founder_count=8,
        assignment_phase=1,
    )

    validate_e5_assignment_phase_integrity(phase_a, phase_b)
    assert phase_a.founder_speeds == (3, 4, 3, 4, 3, 4, 3, 4)
    assert phase_b.founder_speeds == (4, 3, 4, 3, 4, 3, 4, 3)


def test_founder_size_scales_only_declared_population_resource_budget() -> None:
    """Test founder-size treatments preserve explicit resource-per-founder scaling."""
    small = build_e5_treatment(mode="neutral", founder_count=2)
    large = build_e5_treatment(mode="neutral", founder_count=32)

    validate_e5_founder_size_integrity(small, large)
    assert sum(amount for _, _, amount in small.resource_deposits) == (
        E5_RESOURCE_PER_FOUNDER * 2
    )
    assert sum(amount for _, _, amount in large.resource_deposits) == (
        E5_RESOURCE_PER_FOUNDER * 32
    )
    assert tuple((x, y) for x, y, _ in small.resource_deposits) == tuple(
        (x, y) for x, y, _ in large.resource_deposits
    )


def test_mode_integrity_rejects_an_unintended_second_difference() -> None:
    """Test neutral-to-weak comparison permits only the focal speed composition."""
    neutral = build_e5_treatment(mode="neutral", founder_count=8)
    weak = build_e5_treatment(mode="weak_selection", founder_count=8)

    validate_e5_mode_integrity(neutral, weak)

    invalid = attrs.evolve(weak, founder_count=32)
    with pytest.raises(ValueError, match="focal inherited speed composition"):
        validate_e5_mode_integrity(neutral, invalid)


def test_real_neutral_replicate_uses_pedigree_ancestry_and_explicit_censoring() -> None:
    """Test one real neutral run preserves complete lineage and event semantics."""
    outcome = run_e5_replicate(
        build_e5_treatment(mode="neutral", founder_count=2),
        seed=11,
        run_role="discovery",
    )

    assert outcome.initial_composition.counts == (1, 1)
    assert outcome.initial_composition.frequencies == pytest.approx((0.5, 0.5))
    assert len(outcome.trajectory) == 61
    assert all(
        point.population_size == sum(point.counts) for point in outcome.trajectory
    )
    if outcome.fixation.right_censored:
        assert outcome.fixation_winner is None
    else:
        assert outcome.fixation_winner in ("A", "B")
        assert outcome.fixation.observed_step_index is not None
    if not outcome.extinction.right_censored:
        extinct_step = outcome.extinction.observed_step_index
        assert extinct_step is not None
        point = outcome.trajectory[extinct_step]
        assert point.population_size == 0
        assert point.frequencies == (None, None)


def test_real_weak_replicate_preserves_only_declared_clonal_speeds() -> None:
    """Test one real weak-selection run completes through pedigree/trait cross-checks."""
    outcome = run_e5_replicate(
        build_e5_treatment(mode="weak_selection", founder_count=2),
        seed=11,
        run_role="discovery",
    )

    assert outcome.treatment.group_speeds == E5_WEAK_PAIR
    assert outcome.initial_composition.counts == (1, 1)
    assert outcome.trajectory[-1].step_index == 60


def test_regime_summary_uses_runs_and_keeps_full_replicate_distribution() -> None:
    """Test E5 summary counts simulation runs rather than organisms."""
    outcomes = run_e5_seed_set(
        mode="neutral",
        founder_count=2,
        seeds=(11, 23, 37),
        run_role="discovery",
    )
    summary = summarize_e5_regime(outcomes)

    assert summary.replicate_count == 3
    assert summary.seeds == (11, 23, 37)
    assert summary.assignment_phases == (0, 1, 0)
    assert len(summary.group_a_frequency_changes) == 3
    assert summary.defined_endpoint_count <= summary.replicate_count


def test_weak_vs_neutral_comparison_requires_matched_founder_size() -> None:
    """Test descriptive signal/spread comparison cannot mix population-size regimes."""
    neutral = summarize_e5_regime(
        run_e5_seed_set(
            mode="neutral",
            founder_count=2,
            seeds=(11, 23),
            run_role="discovery",
        )
    )
    weak = summarize_e5_regime(
        run_e5_seed_set(
            mode="weak_selection",
            founder_count=8,
            seeds=(11, 23),
            run_role="discovery",
        )
    )

    with pytest.raises(ValueError, match="same founder count"):
        compare_e5_weak_to_neutral(neutral, weak)


def test_declared_founder_sizes_remain_even_for_equal_initial_frequencies() -> None:
    """Test all predeclared founder regimes support exact 50/50 initialization."""
    assert all(count % 2 == 0 for count in E5_FOUNDER_COUNTS)
