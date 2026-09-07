"""Tests for WB3 controlled experiment authoring and semantic factors."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import evo_engine.workbench.experiments as experiment_module
from evo_engine.experiments.e3_performance import (
    E3_SPEED_GRID,
    build_e3_treatment,
    run_e3_replicate,
    summarize_e3_treatment,
)
from evo_engine.experiments.e4_selection import (
    E4_FOCAL_SPEEDS,
    build_e4_treatment,
    founder_order_for_replicate,
    run_e4_replicate,
    summarize_e4_environment,
)
from evo_engine.workbench import (
    E4_COUNTERBALANCE_ID,
    EVENT_EVIDENCE_ID,
    INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT,
    ControlledLocomotionIntent,
    EnvironmentSelectionComparisonDefinition,
    EvidencePlan,
    MaxSpeedSweepDefinition,
    expand_environment_selection_comparison,
    expand_max_speed_sweep,
    run_environment_selection_comparison,
    run_max_speed_sweep,
    semantic_diff,
)


def _sweep(
    *,
    levels: tuple[int, ...] = (1, 3),
    seeds: tuple[int, ...] = (17, 29),
) -> MaxSpeedSweepDefinition:
    return MaxSpeedSweepDefinition(
        base_intent=ControlledLocomotionIntent(
            resource_geography="separated_corridor"
        ),
        levels=levels,
        seeds=seeds,
    )


def test_e3_sweep_uses_stable_manipulable_semantic_factor() -> None:
    definition = _sweep()

    assert definition.factor_slot_id == MAX_SPEED_SLOT
    assert definition.levels == (1, 3)
    encoded = json.loads(definition.to_json())
    assert encoded["factor_slot_id"] == "controlled-locomotion.max-speed"
    assert "config." not in encoded["factor_slot_id"]
    assert "founders[" not in encoded["factor_slot_id"]

    with pytest.raises(ValueError, match="manipulates only"):
        MaxSpeedSweepDefinition(
            base_intent=ControlledLocomotionIntent(
                resource_geography="separated_corridor"
            ),
            levels=(3,),
            seeds=(17,),
            factor_slot_id=RESOURCE_GEOGRAPHY_SLOT,
        )


def test_e3_sweep_factor_and_replicate_slots_belong_to_expansion() -> None:
    with pytest.raises(ValueError, match="max_speed must be None"):
        MaxSpeedSweepDefinition(
            base_intent=ControlledLocomotionIntent(
                max_speed=3,
                resource_geography="separated_corridor",
            ),
            seeds=(17,),
        )
    with pytest.raises(ValueError, match="seed must be None"):
        MaxSpeedSweepDefinition(
            base_intent=ControlledLocomotionIntent(
                resource_geography="separated_corridor",
                seed=17,
            ),
            seeds=(17,),
        )


@pytest.mark.parametrize("levels", [(0,), (11,), (3, 3)])
def test_e3_sweep_rejects_unsupported_or_duplicate_levels(
    levels: tuple[int, ...],
) -> None:
    with pytest.raises(ValueError):
        _sweep(levels=levels, seeds=(17,))


def test_e3_sweep_preserves_characterized_grid_and_unique_seed_replicates() -> None:
    definition = _sweep(levels=E3_SPEED_GRID, seeds=(17, 29))

    assert definition.levels == tuple(range(1, 11))
    with pytest.raises(ValueError, match="duplicates"):
        _sweep(levels=(3,), seeds=(17, 17))


def test_e3_sweep_requires_exact_analysis_evidence() -> None:
    with pytest.raises(ValueError, match="requires evidence"):
        MaxSpeedSweepDefinition(
            base_intent=ControlledLocomotionIntent(
                resource_geography="separated_corridor"
            ),
            levels=(3,),
            seeds=(17,),
            evidence_plan=EvidencePlan(
                requested=(POPULATION_EVIDENCE_ID,)
            ),
        )
    with pytest.raises(ValueError, match="does not support evidence"):
        MaxSpeedSweepDefinition(
            base_intent=ControlledLocomotionIntent(
                resource_geography="separated_corridor"
            ),
            levels=(3,),
            seeds=(17,),
            evidence_plan=EvidencePlan(
                requested=(
                    POPULATION_EVIDENCE_ID,
                    EVENT_EVIDENCE_ID,
                    INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
                )
            ),
        )


def test_e3_sweep_expands_deterministically_before_compilation() -> None:
    definition = _sweep()

    first = expand_max_speed_sweep(definition)
    second = expand_max_speed_sweep(definition)

    assert first == second
    assert [(item.factor_level, item.seed) for item in first] == [
        (1, 17),
        (1, 29),
        (3, 17),
        (3, 29),
    ]
    assert all(item.factor_slot_id == MAX_SPEED_SLOT for item in first)
    assert all(
        item.manifest.explicit_value(MAX_SPEED_SLOT) == item.factor_level
        for item in first
    )
    assert all(
        item.manifest.explicit_value(SEED_SLOT) == item.seed
        for item in first
    )


def test_e3_same_seed_manifests_differ_only_by_declared_factor() -> None:
    expanded = expand_max_speed_sweep(
        _sweep(levels=(1, 3, 9), seeds=(17,))
    )
    reference = expanded[0]

    for candidate in expanded[1:]:
        difference = semantic_diff(
            reference.manifest,
            candidate.manifest,
        )
        assert {
            change.slot_id
            for change in difference.explicit_changes
        } == {MAX_SPEED_SLOT}


def test_e3_expansion_calls_concrete_treatment_integrity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = experiment_module.validate_e3_speed_treatment_integrity
    calls: list[tuple[object, object]] = []

    def spy(control: object, treatment: object) -> None:
        calls.append((control, treatment))
        original(control, treatment)  # type: ignore[arg-type]

    monkeypatch.setattr(
        experiment_module,
        "validate_e3_speed_treatment_integrity",
        spy,
    )

    expand_max_speed_sweep(_sweep(levels=(1, 3), seeds=(17,)))

    assert len(calls) == 2


def test_e3_workbench_execution_reuses_existing_scientific_results() -> None:
    definition = _sweep(levels=(3,), seeds=(17,))
    result = run_max_speed_sweep(definition)
    treatment = build_e3_treatment(
        max_speed=3,
        environment="separated_corridor",
    )
    direct = run_e3_replicate(
        treatment,
        seed=17,
        run_role="confirmation",
    )

    assert result.replicate_outcomes == (direct,)
    assert result.treatment_summaries == (
        summarize_e3_treatment((direct,)),
    )
    assert result.replicate_outcomes[0].provenance.seed == 17


def test_e3_definition_round_trip_preserves_factor_identity_and_meaning() -> None:
    definition = _sweep(levels=(1, 3, 9), seeds=(17, 29))
    encoded = definition.to_json()

    loaded = MaxSpeedSweepDefinition.from_json(encoded)

    assert loaded == definition
    assert loaded.to_json() == encoded
    assert loaded.factor_slot_id == MAX_SPEED_SLOT
    assert expand_max_speed_sweep(loaded) == expand_max_speed_sweep(
        definition
    )


def test_e4_comparison_uses_resource_geography_as_only_primary_factor() -> None:
    definition = EnvironmentSelectionComparisonDefinition(
        seeds=(5, 17, 29)
    )

    assert definition.factor_slot_id == RESOURCE_GEOGRAPHY_SLOT
    assert definition.focal_speeds == E4_FOCAL_SPEEDS
    encoded = json.loads(definition.to_json())
    assert (
        encoded["factor_slot_id"]
        == "controlled-locomotion.resource-geography"
    )
    assert encoded["counterbalance_id"] == E4_COUNTERBALANCE_ID

    with pytest.raises(ValueError, match="manipulates only"):
        EnvironmentSelectionComparisonDefinition(
            seeds=(5,),
            factor_slot_id=MAX_SPEED_SLOT,
        )


def test_e4_comparison_preserves_frozen_treatments_and_standing_composition() -> None:
    with pytest.raises(ValueError, match="frozen"):
        EnvironmentSelectionComparisonDefinition(
            seeds=(5,),
            control_environment="separated_corridor",
            treatment_environment="local_resource",
        )
    with pytest.raises(ValueError, match="standing focal composition"):
        EnvironmentSelectionComparisonDefinition(
            seeds=(5,),
            focal_speeds=(1, 3, 8),
        )


def test_e4_comparison_requires_complete_focal_and_mechanism_evidence() -> None:
    with pytest.raises(ValueError, match="requires evidence"):
        EnvironmentSelectionComparisonDefinition(
            seeds=(5,),
            evidence_plan=EvidencePlan(
                requested=(
                    POPULATION_EVIDENCE_ID,
                    EVENT_EVIDENCE_ID,
                )
            ),
        )
    with pytest.raises(ValueError, match="does not support evidence"):
        EnvironmentSelectionComparisonDefinition(
            seeds=(5,),
            evidence_plan=EvidencePlan(
                requested=(
                    INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
                    POPULATION_EVIDENCE_ID,
                    EVENT_EVIDENCE_ID,
                    "unknown-evidence",
                )
            ),
        )


def test_e4_expansion_keeps_counterbalance_separate_from_factor_meaning() -> None:
    definition = EnvironmentSelectionComparisonDefinition(
        seeds=(5, 17, 29)
    )

    expanded = expand_environment_selection_comparison(definition)

    assert len(expanded) == 6
    for index, seed in enumerate(definition.seeds):
        control, treatment = expanded[index * 2 : index * 2 + 2]
        expected_order = founder_order_for_replicate(index)
        assert (control.role, treatment.role) == (
            "control",
            "treatment",
        )
        assert (control.seed, treatment.seed) == (seed, seed)
        assert (
            control.factor_slot_id,
            treatment.factor_slot_id,
        ) == (
            RESOURCE_GEOGRAPHY_SLOT,
            RESOURCE_GEOGRAPHY_SLOT,
        )
        assert (
            control.factor_level,
            treatment.factor_level,
        ) == (
            "local_resource",
            "separated_corridor",
        )
        assert (
            control.founder_speed_order,
            treatment.founder_speed_order,
        ) == (
            expected_order,
            expected_order,
        )
        assert (
            control.standing_focal_composition
            == treatment.standing_focal_composition
            == E4_FOCAL_SPEEDS
        )


def test_e4_expansion_calls_concrete_environment_integrity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = experiment_module.validate_e4_environment_treatment_integrity
    calls: list[tuple[object, object]] = []

    def spy(control: object, treatment: object) -> None:
        calls.append((control, treatment))
        original(control, treatment)  # type: ignore[arg-type]

    monkeypatch.setattr(
        experiment_module,
        "validate_e4_environment_treatment_integrity",
        spy,
    )

    expand_environment_selection_comparison(
        EnvironmentSelectionComparisonDefinition(seeds=(5, 17))
    )

    assert len(calls) == 2


def test_e4_workbench_execution_reuses_existing_scientific_results() -> None:
    definition = EnvironmentSelectionComparisonDefinition(seeds=(5,))
    result = run_environment_selection_comparison(definition)
    founder_order = founder_order_for_replicate(0)
    control = build_e4_treatment(
        environment="local_resource",
        founder_speed_order=founder_order,
    )
    treatment = build_e4_treatment(
        environment="separated_corridor",
        founder_speed_order=founder_order,
    )
    direct_control = run_e4_replicate(
        control,
        seed=5,
        run_role="confirmation",
    )
    direct_treatment = run_e4_replicate(
        treatment,
        seed=5,
        run_role="confirmation",
    )

    assert result.replicate_outcomes == (
        direct_control,
        direct_treatment,
    )
    assert result.environment_summaries == (
        summarize_e4_environment((direct_control,)),
        summarize_e4_environment((direct_treatment,)),
    )
    assert tuple(
        outcome.provenance.seed
        for outcome in result.replicate_outcomes
    ) == (5, 5)


def test_e4_definition_round_trip_preserves_counterbalance_and_factor() -> None:
    definition = EnvironmentSelectionComparisonDefinition(
        seeds=(5, 17, 29)
    )
    encoded = definition.to_json()

    loaded = EnvironmentSelectionComparisonDefinition.from_json(encoded)

    assert loaded == definition
    assert loaded.to_json() == encoded
    assert loaded.factor_slot_id == RESOURCE_GEOGRAPHY_SLOT
    assert (
        expand_environment_selection_comparison(loaded)
        == expand_environment_selection_comparison(definition)
    )


def test_e4_definition_rejects_tampered_counterbalance_identity() -> None:
    definition = EnvironmentSelectionComparisonDefinition(seeds=(5,))
    mapping = json.loads(definition.to_json())
    mapping["counterbalance_id"] = "different-scheme"

    with pytest.raises(ValueError, match="counterbalance identity"):
        EnvironmentSelectionComparisonDefinition.from_json(
            json.dumps(mapping)
        )


def test_wb3_does_not_add_generic_experiment_or_statistics_machinery() -> None:
    package_root = Path(experiment_module.__file__).resolve().parent
    forbidden_names = {
        "ConfigurationDiff",
        "AllowedDifference",
        "FactorRegistry",
        "MetricRegistry",
        "StatisticsRegistry",
        "ExperimentRegistry",
        "FactorialExperiment",
    }
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in package_root.glob("*.py")
    )

    for forbidden in forbidden_names:
        assert forbidden not in source
