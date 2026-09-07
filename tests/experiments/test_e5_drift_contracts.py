"""Focused contract and guard tests for the E5 drift experiment layer."""

from __future__ import annotations

from typing import Any, cast

import attrs
import pytest

import evo_engine.experiments.e5_drift as e5
from evo_engine.experiments.science import FixedHorizonTimeToEvent
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import (
    IndividualGeneticTraitObservation,
    IndividualGeneticTraitSnapshot,
    IndividualLifeHistory,
)


def _point(step: int, a_count: int, b_count: int) -> e5.E5LineageCompositionPoint:
    population_size = a_count + b_count
    frequencies = e5._lineage_frequencies((a_count, b_count))
    return e5.E5LineageCompositionPoint(
        step_index=step,
        population_size=population_size,
        counts=(a_count, b_count),
        frequencies=frequencies,
    )


def _trait_observations(
    trait_name: str = MAX_SPEED,
) -> tuple[IndividualGeneticTraitObservation, ...]:
    return tuple(
        IndividualGeneticTraitObservation(
            step_index=step,
            trait_names=(trait_name,),
            individuals=(),
        )
        for step in range(e5.E5_HORIZON + 1)
    )


@pytest.fixture(scope="module")
def neutral_outcome() -> e5.E5ReplicateOutcome:
    return e5.run_e5_replicate(
        e5.build_e5_treatment(mode="neutral", founder_count=2),
        seed=11,
        run_role="discovery",
    )


@pytest.fixture(scope="module")
def weak_outcome() -> e5.E5ReplicateOutcome:
    return e5.run_e5_replicate(
        e5.build_e5_treatment(mode="weak_selection", founder_count=2),
        seed=11,
        run_role="discovery",
    )


def test_treatment_specification_rejects_out_of_scope_values() -> None:
    with pytest.raises(ValueError, match="mode must"):
        e5.E5TreatmentSpecification(
            mode=cast(Any, "other"),
            founder_count=2,
        )
    with pytest.raises(ValueError, match="founder_count must"):
        e5.E5TreatmentSpecification(mode="neutral", founder_count=4)
    with pytest.raises(ValueError, match="assignment_phase"):
        e5.E5TreatmentSpecification(
            mode="neutral",
            founder_count=2,
            assignment_phase=2,
        )
    with pytest.raises(ValueError, match="weak_pair must"):
        e5.E5TreatmentSpecification(
            mode="weak_selection",
            founder_count=2,
            weak_pair=(3, 5),
        )


def test_treatment_resource_budget_and_seed_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    treatment = e5.build_e5_treatment(mode="weak_selection", founder_count=2)
    assert treatment.group_speeds == e5.E5_WEAK_PAIR
    assert treatment.treatment_id.endswith("phase-0")
    with pytest.raises(TypeError, match="seed"):
        treatment.to_config(seed=cast(Any, "11"))

    monkeypatch.setattr(e5, "E5_RESOURCE_PER_FOUNDER", 421)
    with pytest.raises(ValueError, match="divide equally"):
        _ = treatment.resource_deposits


def test_composition_point_validates_extinction_and_frequency_semantics() -> None:
    with pytest.raises(ValueError, match="exactly two groups"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=1,
            counts=cast(Any, (1,)),
            frequencies=(1.0, 0.0),
        )
    with pytest.raises(ValueError, match="exactly two groups"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=1,
            counts=(1, 0),
            frequencies=cast(Any, (1.0,)),
        )
    with pytest.raises(ValueError, match="greater than or equal"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=0,
            counts=(-1, 1),
            frequencies=(0.0, 1.0),
        )
    with pytest.raises(ValueError, match="counts must equal"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=3,
            counts=(1, 1),
            frequencies=(0.5, 0.5),
        )
    with pytest.raises(ValueError, match="extinct lineage frequencies"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=0,
            counts=(0, 0),
            frequencies=(0.0, 0.0),
        )
    with pytest.raises(ValueError, match="nonempty lineage frequencies"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=1,
            counts=(1, 0),
            frequencies=(None, 0.0),
        )
    with pytest.raises(ValueError, match="finite in"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=1,
            counts=(1, 0),
            frequencies=(float("nan"), 0.0),
        )
    with pytest.raises(ValueError, match="sum to one"):
        e5.E5LineageCompositionPoint(
            step_index=0,
            population_size=2,
            counts=(1, 1),
            frequencies=(0.4, 0.4),
        )

    extinct = _point(4, 0, 0)
    assert extinct.frequencies == (None, None)
    assert _point(0, 1, 1).frequency("A") == pytest.approx(0.5)
    assert _point(0, 1, 1).count("B") == 1
    with pytest.raises(ValueError, match="group must"):
        _point(0, 1, 1).count(cast(Any, "C"))


def test_replicate_outcome_constructor_guards(
    neutral_outcome: e5.E5ReplicateOutcome,
) -> None:
    p0 = _point(0, 1, 1)
    p60 = _point(e5.E5_HORIZON, 1, 1)

    with pytest.raises(TypeError, match="treatment"):
        attrs.evolve(neutral_outcome, treatment=cast(Any, object()))
    with pytest.raises(TypeError, match="provenance"):
        attrs.evolve(neutral_outcome, provenance=cast(Any, object()))
    with pytest.raises(ValueError, match="include committed step zero"):
        attrs.evolve(neutral_outcome, trajectory=())
    with pytest.raises(ValueError, match="begin at committed step zero"):
        attrs.evolve(neutral_outcome, trajectory=(_point(1, 1, 1), p60))
    with pytest.raises(ValueError, match="frozen E5 horizon"):
        attrs.evolve(neutral_outcome, trajectory=(p0, _point(59, 1, 1)))
    with pytest.raises(ValueError, match="equal A/B founder counts"):
        attrs.evolve(
            neutral_outcome,
            trajectory=(_point(0, 2, 1), _point(e5.E5_HORIZON, 2, 1)),
        )
    with pytest.raises(TypeError, match="group_a_loss"):
        attrs.evolve(neutral_outcome, group_a_loss=cast(Any, object()))
    with pytest.raises(ValueError, match="right-censored fixation"):
        attrs.evolve(neutral_outcome, fixation_winner="A")

    observed_fixation = FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=e5.E5_HORIZON,
        observed_step_index=e5.E5_HORIZON,
    )
    with pytest.raises(ValueError, match="identify winner"):
        attrs.evolve(
            neutral_outcome,
            fixation=observed_fixation,
            fixation_winner=None,
        )


def test_frequency_change_is_undefined_after_whole_population_extinction(
    neutral_outcome: e5.E5ReplicateOutcome,
) -> None:
    extinct = attrs.evolve(
        neutral_outcome,
        trajectory=(
            _point(0, 1, 1),
            _point(e5.E5_HORIZON, 0, 0),
        ),
    )
    assert extinct.final_population_size == 0
    assert extinct.group_a_frequency_change is None


def test_assignment_and_treatment_integrity_guards() -> None:
    assert e5.assignment_phase_for_replicate(0) == 0
    assert e5.assignment_phase_for_replicate(1) == 1
    with pytest.raises(ValueError, match="greater than or equal"):
        e5.assignment_phase_for_replicate(-1)

    neutral = e5.build_e5_treatment(mode="neutral", founder_count=2)
    with pytest.raises(ValueError, match="neutral control"):
        e5.validate_e5_mode_integrity(neutral, neutral)
    with pytest.raises(ValueError, match="founder count"):
        e5.validate_e5_founder_size_integrity(
            neutral,
            attrs.evolve(
                e5.build_e5_treatment(mode="neutral", founder_count=8),
                assignment_phase=1,
            ),
        )
    with pytest.raises(ValueError, match="assignment phase"):
        e5.validate_e5_assignment_phase_integrity(
            neutral,
            attrs.evolve(neutral, weak_pair=e5.E5_WEAK_PAIR_ALTERNATIVE),
        )
    with pytest.raises(TypeError, match="treatment"):
        e5.validate_e5_founder_size_integrity(cast(Any, object()), neutral)


def test_run_entry_points_reject_invalid_seed_sets() -> None:
    with pytest.raises(TypeError, match="treatment"):
        e5.run_e5_replicate(cast(Any, object()), seed=1, run_role=None)
    with pytest.raises(TypeError, match="seed"):
        e5.run_e5_replicate(
            e5.build_e5_treatment(mode="neutral", founder_count=2),
            seed=cast(Any, "1"),
            run_role=None,
        )
    with pytest.raises(ValueError, match="must not be empty"):
        e5.run_e5_seed_set(
            mode="neutral",
            founder_count=2,
            seeds=(),
            run_role=None,
        )
    with pytest.raises(ValueError, match="duplicates"):
        e5.run_e5_seed_set(
            mode="neutral",
            founder_count=2,
            seeds=(1, 1),
            run_role=None,
        )
    with pytest.raises(TypeError, match="seeds\[0\]"):
        e5.run_e5_seed_set(
            mode="neutral",
            founder_count=2,
            seeds=cast(Any, ("1",)),
            run_role=None,
        )


def test_trait_observation_validation_guards() -> None:
    valid = _trait_observations()
    assert e5._validated_trait_observations(valid) == valid
    with pytest.raises(ValueError, match="requires committed"):
        e5._validated_trait_observations(())
    with pytest.raises(ValueError, match="every committed step"):
        e5._validated_trait_observations(valid[:-1])
    with pytest.raises(ValueError, match="only max_speed"):
        e5._validated_trait_observations(_trait_observations("other_trait"))


def test_ancestry_resolution_covers_valid_and_invalid_clonal_pedigrees() -> None:
    founder_a = IndividualLifeHistory(organism_id=1, is_founder=True)
    founder_b = IndividualLifeHistory(organism_id=2, is_founder=True)
    child = IndividualLifeHistory(organism_id=3, parent_ids=(1,))
    resolved = e5._resolve_ancestry_groups(
        (founder_a, founder_b, child),
        founder_group_map={1: "A", 2: "B"},
    )
    assert resolved == {1: "A", 2: "B", 3: "A"}

    with pytest.raises(ValueError, match="unique organism IDs"):
        e5._resolve_ancestry_groups(
            (founder_a, attrs.evolve(founder_a, is_founder=False)),
            founder_group_map={1: "A"},
        )
    with pytest.raises(ValueError, match="missing its analysis-only group"):
        e5._resolve_ancestry_groups((founder_a,), founder_group_map={})
    with pytest.raises(ValueError, match="exactly one recorded parent"):
        e5._resolve_ancestry_groups(
            (
                founder_a,
                founder_b,
                IndividualLifeHistory(organism_id=3, parent_ids=(1, 2)),
            ),
            founder_group_map={1: "A", 2: "B"},
        )
    with pytest.raises(ValueError, match="absent from pedigree records"):
        e5._resolve_ancestry_groups(
            (IndividualLifeHistory(organism_id=3, parent_ids=(99,)),),
            founder_group_map={},
        )
    with pytest.raises(ValueError, match="contains a cycle"):
        e5._resolve_ancestry_groups(
            (
                IndividualLifeHistory(organism_id=3, parent_ids=(4,)),
                IndividualLifeHistory(organism_id=4, parent_ids=(3,)),
            ),
            founder_group_map={},
        )


def test_active_group_and_composition_cross_check_traits() -> None:
    observation = IndividualGeneticTraitObservation(
        step_index=0,
        trait_names=(MAX_SPEED,),
        individuals=(
            IndividualGeneticTraitSnapshot(organism_id=1, trait_values=(3,)),
            IndividualGeneticTraitSnapshot(organism_id=2, trait_values=(4,)),
        ),
    )
    treatment = e5.build_e5_treatment(mode="weak_selection", founder_count=2)
    point = e5._composition_point(
        observation,
        ancestry_groups={1: "A", 2: "B"},
        treatment=treatment,
    )
    assert point.counts == (1, 1)

    with pytest.raises(ValueError, match="no resolved ancestry group"):
        e5._validated_active_group(
            observation,
            organism_id=1,
            ancestry_groups={},
            expected_speed_by_group={"A": 3, "B": 4},
        )
    with pytest.raises(ValueError, match="does not match"):
        e5._validated_active_group(
            observation,
            organism_id=1,
            ancestry_groups={1: "A"},
            expected_speed_by_group={"A": 4, "B": 3},
        )


def test_loss_fixation_and_extinction_helpers_preserve_censoring() -> None:
    p0 = _point(0, 1, 1)
    a_fixed = _point(4, 2, 0)
    b_fixed = _point(5, 0, 2)
    extinct = _point(3, 0, 0)
    balanced = _point(e5.E5_HORIZON, 2, 2)

    assert e5._group_loss_outcome((p0, a_fixed), group="B").observed_step_index == 4
    assert e5._group_loss_outcome((p0, balanced), group="B").right_censored
    fixation, winner = e5._fixation_outcome((p0, a_fixed))
    assert fixation.observed_step_index == 4
    assert winner == "A"
    fixation, winner = e5._fixation_outcome((p0, b_fixed))
    assert fixation.observed_step_index == 5
    assert winner == "B"
    fixation, winner = e5._fixation_outcome((p0, extinct, balanced))
    assert fixation.right_censored
    assert winner is None
    assert e5._extinction_outcome((p0, extinct)).observed_step_index == 3
    assert e5._extinction_outcome((p0, balanced)).right_censored


def test_loss_fixation_consistency_guard(
    neutral_outcome: e5.E5ReplicateOutcome,
) -> None:
    e5._validate_loss_fixation_consistency(neutral_outcome)
    observed_fixation = FixedHorizonTimeToEvent(
        start_step_index=0,
        horizon_step_index=e5.E5_HORIZON,
        observed_step_index=e5.E5_HORIZON,
    )
    inconsistent = attrs.evolve(
        neutral_outcome,
        trajectory=(
            _point(0, 1, 1),
            _point(e5.E5_HORIZON, 2, 0),
        ),
        fixation=observed_fixation,
        fixation_winner="A",
    )
    with pytest.raises(ValueError, match="coincide"):
        e5._validate_loss_fixation_consistency(inconsistent)


def test_regime_validation_rejects_mixed_or_pseudoreplicated_runs(
    neutral_outcome: e5.E5ReplicateOutcome,
    weak_outcome: e5.E5ReplicateOutcome,
) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        e5.summarize_e5_regime(())
    with pytest.raises(TypeError, match="only E5ReplicateOutcome"):
        e5.summarize_e5_regime(cast(Any, (object(),)))
    with pytest.raises(ValueError, match="one mode"):
        e5.summarize_e5_regime((neutral_outcome, weak_outcome))

    other_seed = attrs.evolve(neutral_outcome.provenance, seed=12)
    other_size = attrs.evolve(
        neutral_outcome,
        treatment=e5.build_e5_treatment(mode="neutral", founder_count=8),
        provenance=other_seed,
    )
    with pytest.raises(ValueError, match="one founder count"):
        e5.summarize_e5_regime((neutral_outcome, other_size))

    alternative_pair = attrs.evolve(
        weak_outcome,
        treatment=attrs.evolve(
            weak_outcome.treatment,
            weak_pair=e5.E5_WEAK_PAIR_ALTERNATIVE,
        ),
        provenance=attrs.evolve(weak_outcome.provenance, seed=12),
    )
    with pytest.raises(ValueError, match="one weak pair"):
        e5.summarize_e5_regime((weak_outcome, alternative_pair))

    duplicate_seed = attrs.evolve(
        neutral_outcome,
        treatment=attrs.evolve(neutral_outcome.treatment, assignment_phase=1),
    )
    with pytest.raises(ValueError, match="unique replicate seeds"):
        e5.summarize_e5_regime((neutral_outcome, duplicate_seed))


def test_weak_neutral_comparison_type_mode_and_signal_branches(
    neutral_outcome: e5.E5ReplicateOutcome,
    weak_outcome: e5.E5ReplicateOutcome,
) -> None:
    neutral = e5.summarize_e5_regime((neutral_outcome,))
    weak = e5.summarize_e5_regime((weak_outcome,))
    assert e5.compare_e5_weak_to_neutral(neutral, weak).signal_to_neutral_sd is None

    with pytest.raises(TypeError, match="E5RegimeSummary"):
        e5.compare_e5_weak_to_neutral(cast(Any, object()), weak)
    with pytest.raises(ValueError, match="neutral and weak_selection"):
        e5.compare_e5_weak_to_neutral(neutral, attrs.evolve(weak, mode="neutral"))

    comparison = e5.compare_e5_weak_to_neutral(
        attrs.evolve(neutral, stddev_group_a_frequency_change=0.1),
        attrs.evolve(weak, mean_group_a_frequency_change=0.05),
    )
    assert comparison.signal_to_neutral_sd == pytest.approx(0.5)


def test_descriptive_statistics_helpers_cover_empty_and_directional_cases() -> None:
    assert e5._mean_or_none(()) is None
    assert e5._median_or_none(()) is None
    assert e5._variance_or_none((1.0,)) is None
    assert e5._stddev_or_none((1.0,)) is None
    assert e5._mean_or_none((1.0, 3.0)) == pytest.approx(2.0)
    assert e5._median_or_none((1.0, 3.0)) == pytest.approx(2.0)
    assert e5._variance_or_none((1.0, 3.0)) == pytest.approx(2.0)
    assert e5._stddev_or_none((1.0, 3.0)) == pytest.approx(2.0**0.5)
    assert e5._direction_proportion((), direction="increase") is None
    assert e5._direction_proportion(
        (1.0, -1.0, 0.0), direction="increase"
    ) == pytest.approx(1 / 3)
    assert e5._direction_proportion(
        (1.0, -1.0, 0.0), direction="decrease"
    ) == pytest.approx(1 / 3)
    assert e5._direction_proportion(
        (1.0, -1.0, 0.0), direction="unchanged"
    ) == pytest.approx(1 / 3)
    with pytest.raises(ValueError, match="must not be empty"):
        e5._proportion((), lambda _: True)


def test_group_index_and_treatment_requirement_guards() -> None:
    assert e5._group_index("A") == 0
    assert e5._group_index("B") == 1
    with pytest.raises(ValueError, match="group must"):
        e5._group_index(cast(Any, "other"))
    with pytest.raises(TypeError, match="treatment"):
        e5._require_treatment(object())
