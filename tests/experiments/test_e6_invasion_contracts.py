"""Guard contracts for the frozen E6 rare-lineage invasion assay."""

from __future__ import annotations

import math
from typing import Any, cast

import attrs
import pytest

import evo_engine.experiments.e6_invasion as e6
from evo_engine.experiments.science import FixedHorizonTimeToEvent


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
    checkpoint_population = neutral.burn_in_checkpoint.population_size

    assert neutral.burn_in_checkpoint == mutant.burn_in_checkpoint
    assert checkpoint_population >= e6.E6_RESIDENT_FOUNDER_COUNT
    assert neutral.burn_in_checkpoint.step_index == e6.E6_BURN_IN_STEPS
    assert len(neutral.burn_in_checkpoint.world_state_sha256) == 64
    assert len(neutral.burn_in_checkpoint.rng_state_sha256) == 64

    assert neutral.intervention.organism_id == mutant.intervention.organism_id
    assert (
        neutral.intervention.anchor_resident_id
        == mutant.intervention.anchor_resident_id
    )
    assert (neutral.intervention.x, neutral.intervention.y) == (
        mutant.intervention.x,
        mutant.intervention.y,
    )
    assert neutral.intervention.resident_population_size_before == checkpoint_population
    assert neutral.intervention.initial_rare_frequency == pytest.approx(
        1 / (checkpoint_population + 1)
    )
    assert neutral.intervention.age == mutant.intervention.age == 0
    assert neutral.intervention.energy == mutant.intervention.energy == 20
    assert neutral.intervention.body_mass == mutant.intervention.body_mass == 1
    assert (
        neutral.intervention.mating_type == mutant.intervention.mating_type == "clonal"
    )
    assert neutral.intervention.entrant_speed == 4
    assert mutant.intervention.entrant_speed == 3


def test_post_introduction_baseline_and_complete_trajectory_are_explicit(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    for outcome in (pair.neutral, pair.mutant):
        resident_count = outcome.burn_in_checkpoint.population_size
        assert outcome.trajectory[0].step_index == e6.E6_BURN_IN_STEPS
        assert outcome.trajectory[-1].step_index == e6.E6_HORIZON
        assert len(outcome.trajectory) == e6.E6_POST_INTRODUCTION_STEPS + 1
        assert outcome.trajectory[0].counts == (resident_count, 1)
        assert outcome.trajectory[0].frequency("rare") == pytest.approx(
            1 / (resident_count + 1)
        )
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


def test_treatment_validation_rejects_invalid_roles_and_speed_pairs() -> None:
    with pytest.raises(ValueError, match="role"):
        e6.E6TreatmentSpecification(
            role=cast(Any, "other"),
            resident_speed=4,
            entrant_speed=4,
        )
    with pytest.raises(ValueError, match="resident_speed"):
        e6.build_e6_treatment(role="neutral", resident_speed=2, entrant_speed=2)
    with pytest.raises(ValueError, match="neutral entrant_speed"):
        e6.build_e6_treatment(role="neutral", resident_speed=4, entrant_speed=3)
    with pytest.raises(ValueError, match="reciprocal"):
        e6.build_e6_treatment(role="mutant", resident_speed=4, entrant_speed=2)
    with pytest.raises(TypeError, match="value must be"):
        e6.validate_e6_matched_arm_integrity(
            cast(Any, object()),
            e6.build_e6_treatment(role="mutant", resident_speed=4, entrant_speed=3),
        )
    with pytest.raises(ValueError, match="neutral and mutant"):
        neutral = e6.build_e6_treatment(
            role="neutral",
            resident_speed=4,
            entrant_speed=4,
        )
        e6.validate_e6_matched_arm_integrity(neutral, neutral)


def test_checkpoint_validation_guards_exact_burn_in_provenance(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    checkpoint = pair.neutral.burn_in_checkpoint

    invalid_cases: tuple[tuple[str, object, type[Exception], str], ...] = (
        ("resident_speed", 2, ValueError, "resident_speed"),
        ("step_index", e6.E6_BURN_IN_STEPS - 1, ValueError, "burn-in"),
        ("population_size", 0, ValueError, "population_size"),
        ("organism_ids", checkpoint.organism_ids[:-1], ValueError, "complete"),
        (
            "organism_ids",
            tuple(reversed(checkpoint.organism_ids)),
            ValueError,
            "increasing order",
        ),
        (
            "organism_ids",
            (checkpoint.organism_ids[0],) * checkpoint.population_size,
            ValueError,
            "unique",
        ),
        ("world_state_sha256", "bad", ValueError, "SHA-256"),
        ("rng_state_sha256", "g" * 64, ValueError, "SHA-256"),
    )
    for field_name, value, error_type, match in invalid_cases:
        with pytest.raises(error_type, match=match):
            attrs.evolve(checkpoint, **{field_name: value})


def test_intervention_validation_guards_external_admission_contract(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    intervention = pair.neutral.intervention

    invalid_cases: tuple[tuple[str, object, type[Exception], str], ...] = (
        ("mechanism", "birth", ValueError, "mechanism"),
        ("step_index", e6.E6_BURN_IN_STEPS - 1, ValueError, "burn-in"),
        (
            "resident_population_size_before",
            0,
            ValueError,
            "resident_population_size_before",
        ),
        ("initial_rare_frequency", 0.5, ValueError, "initial_rare_frequency"),
        ("age", 1, ValueError, "age"),
        ("energy", 21, ValueError, "energy"),
        ("body_mass", 2, ValueError, "body_mass"),
        ("mating_type", "sexual", ValueError, "mating_type"),
        ("x", -1, ValueError, "x"),
        ("y", -1, ValueError, "y"),
    )
    for field_name, value, error_type, match in invalid_cases:
        with pytest.raises(error_type, match=match):
            attrs.evolve(intervention, **{field_name: value})


def test_lineage_composition_validation_guards_complete_counts_and_frequencies() -> None:
    with pytest.raises(ValueError, match="resident and rare"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=1,
            counts=cast(Any, (1,)),
            frequencies=(1.0, 0.0),
        )
    with pytest.raises(ValueError, match=r"counts\[0\]"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=1,
            counts=(-1, 2),
            frequencies=(0.0, 1.0),
        )
    with pytest.raises(ValueError, match="complete population size"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=3,
            counts=(1, 1),
            frequencies=(0.5, 0.5),
        )
    with pytest.raises(ValueError, match="two lineage frequencies"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=1,
            counts=(1, 0),
            frequencies=cast(Any, (1.0,)),
        )
    with pytest.raises(ValueError, match="extinct"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=0,
            counts=(0, 0),
            frequencies=(0.0, 0.0),
        )
    with pytest.raises(ValueError, match="must be defined"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=1,
            counts=(1, 0),
            frequencies=(None, None),
        )
    with pytest.raises(ValueError, match=r"finite in \[0, 1\]"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=1,
            counts=(1, 0),
            frequencies=(math.inf, -math.inf),
        )
    with pytest.raises(ValueError, match="sum to one"):
        e6.E6LineageCompositionPoint(
            step_index=10,
            population_size=2,
            counts=(1, 1),
            frequencies=(0.4, 0.4),
        )


def test_replicate_validation_guards_baseline_censoring_and_types(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    outcome = pair.neutral
    initial = outcome.initial_composition

    with pytest.raises(TypeError, match="treatment"):
        attrs.evolve(outcome, treatment=cast(Any, object()))
    with pytest.raises(ValueError, match="post-introduction baseline"):
        attrs.evolve(outcome, trajectory=())
    with pytest.raises(ValueError, match="intervention baseline"):
        attrs.evolve(outcome, trajectory=outcome.trajectory[1:])
    with pytest.raises(ValueError, match="candidate E6 horizon"):
        attrs.evolve(outcome, trajectory=outcome.trajectory[:-1])

    bad_rare_count = e6.E6LineageCompositionPoint(
        step_index=initial.step_index,
        population_size=initial.population_size + 1,
        counts=(initial.count("resident"), 2),
        frequencies=(
            initial.count("resident") / (initial.population_size + 1),
            2 / (initial.population_size + 1),
        ),
    )
    with pytest.raises(ValueError, match="one rare organism"):
        attrs.evolve(
            outcome,
            trajectory=(bad_rare_count, *outcome.trajectory[1:]),
        )

    bad_resident_count = e6.E6LineageCompositionPoint(
        step_index=initial.step_index,
        population_size=initial.population_size - 1,
        counts=(initial.count("resident") - 1, 1),
        frequencies=(
            (initial.count("resident") - 1) / (initial.population_size - 1),
            1 / (initial.population_size - 1),
        ),
    )
    with pytest.raises(ValueError, match="initial resident count"):
        attrs.evolve(
            outcome,
            trajectory=(bad_resident_count, *outcome.trajectory[1:]),
        )

    wrong_frequency = e6.E6LineageCompositionPoint(
        step_index=initial.step_index,
        population_size=initial.population_size,
        counts=initial.counts,
        frequencies=(0.8, 0.2),
    )
    with pytest.raises(ValueError, match="initial rare frequency"):
        attrs.evolve(
            outcome,
            trajectory=(wrong_frequency, *outcome.trajectory[1:]),
        )

    with pytest.raises(ValueError, match="rare_birth_count"):
        attrs.evolve(outcome, rare_birth_count=-1)
    with pytest.raises(ValueError, match="fixation winner"):
        attrs.evolve(outcome, fixation_winner="rare")
    with pytest.raises(ValueError, match="fixation winner"):
        attrs.evolve(
            outcome,
            fixation=FixedHorizonTimeToEvent(
                start_step_index=e6.E6_BURN_IN_STEPS,
                horizon_step_index=e6.E6_HORIZON,
                observed_step_index=e6.E6_BURN_IN_STEPS,
            ),
            fixation_winner=None,
        )


def test_pair_validation_guards_exact_checkpoint_seed_and_intervention(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    with pytest.raises(TypeError, match="neutral"):
        e6.E6InvasionPairOutcome(
            neutral=cast(Any, object()),
            mutant=pair.mutant,
        )

    changed_checkpoint = attrs.evolve(
        pair.mutant.burn_in_checkpoint,
        resource_total=pair.mutant.burn_in_checkpoint.resource_total + 1,
    )
    with pytest.raises(ValueError, match="same exact burn-in checkpoint"):
        e6.E6InvasionPairOutcome(
            neutral=pair.neutral,
            mutant=attrs.evolve(pair.mutant, burn_in_checkpoint=changed_checkpoint),
        )

    changed_provenance = attrs.evolve(pair.mutant.provenance, seed=31)
    with pytest.raises(ValueError, match="same seed"):
        e6.E6InvasionPairOutcome(
            neutral=pair.neutral,
            mutant=attrs.evolve(pair.mutant, provenance=changed_provenance),
        )

    changed_id = attrs.evolve(
        pair.mutant.intervention,
        organism_id=pair.mutant.intervention.organism_id + 100,
    )
    with pytest.raises(ValueError, match="same entrant ID"):
        e6.E6InvasionPairOutcome(
            neutral=pair.neutral,
            mutant=attrs.evolve(pair.mutant, intervention=changed_id),
        )

    changed_position = attrs.evolve(
        pair.mutant.intervention,
        x=pair.mutant.intervention.x + 1,
    )
    with pytest.raises(ValueError, match="differ outside"):
        e6.E6InvasionPairOutcome(
            neutral=pair.neutral,
            mutant=attrs.evolve(pair.mutant, intervention=changed_position),
        )


def test_summary_validation_guards_run_level_replicates_and_pairing(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    with pytest.raises(ValueError, match="at least one"):
        e6.summarize_e6_arm(())
    with pytest.raises(TypeError, match="E6ReplicateOutcome"):
        e6.summarize_e6_arm((cast(Any, object()),))
    with pytest.raises(ValueError, match="cannot mix"):
        e6.summarize_e6_arm((pair.neutral, pair.mutant))

    neutral = e6.summarize_e6_arm((pair.neutral,))
    mutant = e6.summarize_e6_arm((pair.mutant,))
    with pytest.raises(TypeError, match="E6ArmSummary"):
        e6.compare_e6_matched_invasion(cast(Any, object()), mutant)
    with pytest.raises(ValueError, match="neutral and mutant"):
        e6.compare_e6_matched_invasion(neutral, neutral)
    with pytest.raises(ValueError, match="one resident background"):
        e6.compare_e6_matched_invasion(
            neutral,
            attrs.evolve(mutant, resident_speed=3),
        )


def test_event_helpers_preserve_first_event_and_right_censoring_semantics() -> None:
    mixed = e6.E6LineageCompositionPoint(
        step_index=e6.E6_BURN_IN_STEPS,
        population_size=2,
        counts=(1, 1),
        frequencies=(0.5, 0.5),
    )
    resident_only = e6.E6LineageCompositionPoint(
        step_index=e6.E6_BURN_IN_STEPS + 1,
        population_size=2,
        counts=(2, 0),
        frequencies=(1.0, 0.0),
    )
    rare_only = e6.E6LineageCompositionPoint(
        step_index=e6.E6_BURN_IN_STEPS + 2,
        population_size=2,
        counts=(0, 2),
        frequencies=(0.0, 1.0),
    )
    extinct = e6.E6LineageCompositionPoint(
        step_index=e6.E6_BURN_IN_STEPS + 3,
        population_size=0,
        counts=(0, 0),
        frequencies=(None, None),
    )

    assert e6._fixation_winner(mixed) is None
    assert e6._fixation_winner(resident_only) == "resident"
    assert e6._fixation_winner(rare_only) == "rare"
    assert e6._fixation_winner(extinct) is None

    censored_fixation, winner = e6._fixation_outcome((mixed,))
    assert censored_fixation.right_censored
    assert winner is None

    observed_fixation, winner = e6._fixation_outcome((mixed, resident_only))
    assert not observed_fixation.right_censored
    assert observed_fixation.observed_step_index == resident_only.step_index
    assert winner == "resident"

    observed = e6._time_to_event(
        (mixed, resident_only),
        predicate=lambda point: point.count("rare") == 0,
    )
    assert observed.observed_step_index == resident_only.step_index
    censored = e6._time_to_event(
        (mixed, resident_only),
        predicate=lambda point: point.population_size == 0,
    )
    assert censored.right_censored


def test_observed_event_validation_rejects_inconsistent_event_steps(
    pair: e6.E6InvasionPairOutcome,
) -> None:
    censored = FixedHorizonTimeToEvent(
        start_step_index=e6.E6_BURN_IN_STEPS,
        horizon_step_index=e6.E6_HORIZON,
    )
    e6._validate_observed_event(
        pair.neutral,
        event=censored,
        predicate=lambda _point: False,
        name="never",
    )

    observed_at_baseline = FixedHorizonTimeToEvent(
        start_step_index=e6.E6_BURN_IN_STEPS,
        horizon_step_index=e6.E6_HORIZON,
        observed_step_index=e6.E6_BURN_IN_STEPS,
    )
    with pytest.raises(ValueError, match="inconsistent"):
        e6._validate_observed_event(
            pair.neutral,
            event=observed_at_baseline,
            predicate=lambda point: point.count("rare") >= 2,
            name="rare expansion",
        )
    with pytest.raises(ValueError, match="step index"):
        e6._point_at_step(pair.neutral.trajectory, None)
    with pytest.raises(ValueError, match="absent"):
        e6._point_at_step(pair.neutral.trajectory, e6.E6_HORIZON + 1)


def test_small_validation_helpers_cover_extinction_safe_edge_contracts() -> None:
    assert e6._lineage_frequencies((0, 0)) == (None, None)
    assert e6._lineage_frequencies((3, 1)) == (0.75, 0.25)
    assert e6._paired_difference(None, 1.0) is None
    assert e6._paired_difference(0.1, 0.3) == pytest.approx(0.2)
    assert e6._mean_or_none(()) is None
    assert e6._median_or_none(()) is None
    assert e6._direction_proportion((), direction="increase") is None
    assert e6._direction_proportion((1.0, -1.0, 0.0), direction="increase") == (
        pytest.approx(1 / 3)
    )
    assert e6._direction_proportion((1.0, -1.0, 0.0), direction="decrease") == (
        pytest.approx(1 / 3)
    )
    assert e6._direction_proportion((1.0, -1.0, 0.0), direction="unchanged") == (
        pytest.approx(1 / 3)
    )
    assert e6._lineage_index("resident") == 0
    assert e6._lineage_index("rare") == 1
    with pytest.raises(ValueError, match="lineage"):
        e6._lineage_index(cast(Any, "other"))

    with pytest.raises(ValueError, match="at least one"):
        e6._validated_unique_seeds(())
    with pytest.raises(TypeError, match=r"seeds\[0\]"):
        e6._validated_unique_seeds((cast(Any, "bad"),))
    with pytest.raises(ValueError, match="unique"):
        e6._validated_unique_seeds((1, 1))

    with pytest.raises(ValueError, match="SHA-256"):
        e6._validate_sha256("abc", name="digest")
    with pytest.raises(ValueError, match="SHA-256"):
        e6._validate_sha256("z" * 64, name="digest")
    assert e6._validate_sha256("a" * 64, name="digest") == "a" * 64
