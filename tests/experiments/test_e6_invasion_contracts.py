"""Guard contracts for the frozen E6 rare-lineage invasion assay."""

from __future__ import annotations

import attrs
import pytest

import evo_engine.experiments.e6_invasion as e6


def test_e6_seed_roles_are_disjoint_and_frozen_timing_is_consistent() -> None:
    assert set(e6.E6_DISCOVERY_SEEDS).isdisjoint(e6.E6_CONFIRMATION_SEEDS)
    assert len(e6.E6_DISCOVERY_SEEDS) == 6
    assert len(e6.E6_CONFIRMATION_SEEDS) == 24
    assert e6.E6_BURN_IN_STEPS == 10
    assert e6.E6_POST_INTRODUCTION_STEPS == 50
    assert e6.E6_HORIZON == 60


def test_e6_resident_resource_budget_scales_from_e5_per_founder_contract() -> None:
    treatment = e6.build_e6_treatment(
        role="neutral",
        resident_speed=4,
        entrant_speed=4,
    )
    config = treatment.to_burn_in_config(seed=13)

    assert len(config.founders) == e6.E6_RESIDENT_FOUNDER_COUNT == 8
    assert sum(amount for _, _, amount in treatment.resource_deposits) == (
        e6.E5_RESOURCE_PER_FOUNDER * e6.E6_RESIDENT_FOUNDER_COUNT
    )
    assert len(treatment.resource_deposits) == 4


def test_e6_rejects_duplicate_seed_pseudoreplication_before_execution() -> None:
    with pytest.raises(ValueError, match="unique"):
        e6.run_e6_seed_set(
            resident_speed=4,
            mutant_speed=3,
            seeds=(13, 13),
            run_role="discovery",
        )


@pytest.fixture(scope="module")
def pair() -> e6.E6InvasionPairOutcome:
    return e6.run_e6_invasion_pair(
        resident_speed=4,
        mutant_speed=3,
        seed=13,
        run_role="discovery",
    )


def test_exact_fork_and_admission_provenance_are_matched(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    neutral = pair.neutral
    mutant = pair.mutant

    assert neutral.burn_in_checkpoint == mutant.burn_in_checkpoint
    assert neutral.burn_in_checkpoint.population_size == 8
    assert neutral.burn_in_checkpoint.step_index == e6.E6_BURN_IN_STEPS
    assert len(neutral.burn_in_checkpoint.world_state_sha256) == 64
    assert len(neutral.burn_in_checkpoint.rng_state_sha256) == 64

    assert neutral.intervention.organism_id == mutant.intervention.organism_id
    assert neutral.intervention.anchor_resident_id == mutant.intervention.anchor_resident_id
    assert (neutral.intervention.x, neutral.intervention.y) == (
        mutant.intervention.x,
        mutant.intervention.y,
    )
    assert neutral.intervention.resident_population_size_before == 8
    assert neutral.intervention.initial_rare_frequency == pytest.approx(1 / 9)
    assert neutral.intervention.age == mutant.intervention.age == 0
    assert neutral.intervention.energy == mutant.intervention.energy == 20
    assert neutral.intervention.body_mass == mutant.intervention.body_mass == 1
    assert neutral.intervention.mating_type == mutant.intervention.mating_type == "clonal"
    assert neutral.intervention.entrant_speed == 4
    assert mutant.intervention.entrant_speed == 3


def test_post_introduction_baseline_and_complete_trajectory_are_explicit(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    for outcome in (pair.neutral, pair.mutant):
        assert outcome.trajectory[0].step_index == e6.E6_BURN_IN_STEPS
        assert outcome.trajectory[-1].step_index == e6.E6_HORIZON
        assert len(outcome.trajectory) == e6.E6_POST_INTRODUCTION_STEPS + 1
        assert outcome.trajectory[0].counts == (8, 1)
        assert outcome.trajectory[0].frequency("rare") == pytest.approx(1 / 9)
        assert outcome.provenance.seed == 13
        assert outcome.provenance.run_role == "discovery"


def test_arm_summary_rejects_duplicate_seed_as_pseudoreplication(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    with pytest.raises(ValueError, match="duplicate seeds"):
        e6.summarize_e6_arm((pair.neutral, pair.neutral))


def test_matched_comparison_requires_identical_seed_order(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    neutral = e6.summarize_e6_arm((pair.neutral,))
    mutant = e6.summarize_e6_arm((pair.mutant,))
    comparison = e6.compare_e6_matched_invasion(neutral, mutant)

    assert comparison.seeds == (13,)
    assert comparison.replicate_count == 1

    mismatched = attrs.evolve(mutant, seeds=(31,))
    with pytest.raises(ValueError, match="identical ordered seed sets"):
        e6.compare_e6_matched_invasion(neutral, mismatched)


def test_matched_treatment_integrity_rejects_wrong_resident_background() -> None:
    neutral = e6.build_e6_treatment(
        role="neutral",
        resident_speed=4,
        entrant_speed=4,
    )
    wrong_background = e6.build_e6_treatment(
        role="mutant",
        resident_speed=3,
        entrant_speed=4,
    )

    with pytest.raises(ValueError, match="same resident speed"):
        e6.validate_e6_matched_arm_integrity(neutral, wrong_background)
