"""Focused contracts for E6 rare-lineage invasion."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.experiments.e6_invasion import (
    E6_BURN_IN_STEPS,
    E6_HORIZON,
    E6_RECIPROCAL_PAIRS,
    build_e6_treatment,
    run_e6_invasion_pair,
    validate_e6_matched_arm_integrity,
)


def test_e6_treatment_space_is_bounded_to_reciprocal_three_four_pairs() -> None:
    neutral = build_e6_treatment(role="neutral", resident_speed=4, entrant_speed=4)
    mutant = build_e6_treatment(role="mutant", resident_speed=4, entrant_speed=3)

    assert neutral.treatment_id == "neutral-resident-4-entrant-4"
    assert mutant.treatment_id == "mutant-resident-4-entrant-3"
    assert E6_RECIPROCAL_PAIRS == ((4, 3), (3, 4))

    with pytest.raises(ValueError):
        build_e6_treatment(role="neutral", resident_speed=4, entrant_speed=3)
    with pytest.raises(ValueError):
        build_e6_treatment(role="mutant", resident_speed=4, entrant_speed=2)


def test_e6_matched_integrity_rejects_hidden_resident_change() -> None:
    neutral = build_e6_treatment(role="neutral", resident_speed=4, entrant_speed=4)
    mutant = build_e6_treatment(role="mutant", resident_speed=4, entrant_speed=3)
    validate_e6_matched_arm_integrity(neutral, mutant)

    hidden_change = attrs.evolve(mutant, resident_speed=3, entrant_speed=4)
    with pytest.raises(ValueError):
        validate_e6_matched_arm_integrity(neutral, hidden_change)


def test_real_e6_pair_uses_exact_checkpoint_and_explicit_admission() -> None:
    pair = run_e6_invasion_pair(
        resident_speed=4,
        mutant_speed=3,
        seed=13,
        run_role="discovery",
    )

    assert pair.neutral.burn_in_checkpoint == pair.mutant.burn_in_checkpoint
    assert pair.neutral.burn_in_checkpoint.step_index == E6_BURN_IN_STEPS
    assert pair.neutral.intervention.organism_id == pair.mutant.intervention.organism_id
    assert pair.neutral.intervention.mechanism == (
        "experiment_external_newborn_like_admission"
    )
    assert pair.neutral.intervention.entrant_speed == 4
    assert pair.mutant.intervention.entrant_speed == 3
    assert pair.neutral.trajectory[0].count("rare") == 1
    assert pair.mutant.trajectory[0].count("rare") == 1
    assert pair.neutral.trajectory[0].step_index == E6_BURN_IN_STEPS
    assert pair.neutral.trajectory[-1].step_index == E6_HORIZON
    assert pair.mutant.trajectory[-1].step_index == E6_HORIZON
