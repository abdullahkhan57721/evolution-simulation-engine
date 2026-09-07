"""Focused contracts for the bounded WB4 reference-ecology recipe."""

from __future__ import annotations

import json

import attrs
import pytest

from evo_engine.workbench.controlled_locomotion import IncompatibleManifestError
from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_X_SLOT,
    PATCH_2_X_SLOT,
    REFERENCE_EXPERT_SLOT_IDS,
    REFERENCE_EXTENSION_CAPABILITIES,
    REFERENCE_SLOT_METADATA,
    REFERENCE_SUPPORT_TIERS,
    SPATIAL_EVIDENCE_ID,
    ReferenceEcologyIntent,
    ReferenceEcologyManifest,
    ReferenceEvidencePlan,
    assess_reference_readiness,
    compile_reference_ecology,
    default_reference_ecology_intent,
    evidence_advisories,
    is_slot_applicable,
    resolve_reference_ecology,
    semantic_reference_diff,
)


def _rich_intent() -> ReferenceEcologyIntent:
    return attrs.evolve(
        default_reference_ecology_intent(),
        horizon=5,
        seed=17,
        max_speed=2,
        sensory_range=5,
        sensory_accuracy=90,
        exploration_movement="gaussian",
        gaussian_standard_deviation=2,
        resource_geography="two_patches",
        patch_1_center_x=2,
        patch_1_center_y=5,
        patch_1_radius=1,
        patch_2_center_x=9,
        patch_2_center_y=5,
        patch_2_radius=1,
    )


def test_support_tiers_are_explicit_without_manufactured_expert_controls() -> None:
    assert {tier for tier, _ in REFERENCE_SUPPORT_TIERS} == {
        "guided",
        "advanced",
        "expert",
        "extension",
    }
    assert {item.support_tier for item in REFERENCE_SLOT_METADATA} == {
        "guided",
        "advanced",
    }
    assert REFERENCE_EXPERT_SLOT_IDS == ()
    assert REFERENCE_EXTENSION_CAPABILITIES


def test_semantic_slot_identity_does_not_use_python_paths() -> None:
    for item in REFERENCE_SLOT_METADATA:
        assert item.slot_id.startswith("reference-ecology.")
        assert "evo_engine" not in item.slot_id
        assert "src/" not in item.slot_id
        assert "__" not in item.slot_id


def test_default_reference_intent_is_ready() -> None:
    intent = default_reference_ecology_intent()
    assert assess_reference_readiness(intent).state == "ready"


def test_rich_reference_recipe_resolves_deterministically() -> None:
    intent = _rich_intent()
    first = resolve_reference_ecology(intent)
    second = resolve_reference_ecology(intent)
    assert first == second
    assert first.digest == second.digest


def test_applicability_is_recipe_local_and_explicit() -> None:
    intent = _rich_intent()
    assert is_slot_applicable(intent, GAUSSIAN_STDDEV_SLOT)
    assert is_slot_applicable(intent, PATCH_1_X_SLOT)
    assert is_slot_applicable(intent, MUTATION_PROBABILITY_SLOT)

    simple = attrs.evolve(
        intent,
        exploration_movement="moore",
        resource_geography="uniform",
        mutation_enabled=False,
    )
    assert not is_slot_applicable(simple, GAUSSIAN_STDDEV_SLOT)
    assert not is_slot_applicable(simple, PATCH_1_X_SLOT)
    assert not is_slot_applicable(simple, MUTATION_PROBABILITY_SLOT)


def test_non_gaussian_movement_normalizes_stale_gaussian_value_away() -> None:
    manifest = resolve_reference_ecology(
        attrs.evolve(
            _rich_intent(),
            exploration_movement="moore",
            gaussian_standard_deviation=9,
        )
    )
    assert manifest.explicit_value_or_none(GAUSSIAN_STDDEV_SLOT) is None


def test_disabled_mutation_normalizes_stale_mutation_parameters_away() -> None:
    manifest = resolve_reference_ecology(
        attrs.evolve(
            _rich_intent(),
            mutation_enabled=False,
            mutation_probability_ppm=99_999,
            mutation_max_change=4,
        )
    )
    assert manifest.explicit_value_or_none(MUTATION_PROBABILITY_SLOT) is None
    assert manifest.explicit_value_or_none(MUTATION_MAX_CHANGE_SLOT) is None
    assert manifest.derived_value(
        "reference-ecology.effective-mutation-probability-ppm"
    ) == 0
    assert manifest.derived_value("reference-ecology.effective-mutation-max-change") == 0


def test_uniform_resources_normalize_stale_patch_geometry_away() -> None:
    manifest = resolve_reference_ecology(
        attrs.evolve(_rich_intent(), resource_geography="uniform")
    )
    assert manifest.explicit_value_or_none(PATCH_1_X_SLOT) is None
    assert manifest.explicit_value_or_none(PATCH_2_X_SLOT) is None


def test_manifest_round_trip_is_exact_and_canonical() -> None:
    manifest = resolve_reference_ecology(_rich_intent())
    loaded = ReferenceEcologyManifest.from_json(manifest.to_json())
    assert loaded == manifest
    assert loaded.to_json() == manifest.to_json()
    assert loaded.digest == manifest.digest


def test_manifest_fingerprints_noneditable_reference_assumptions() -> None:
    manifest = resolve_reference_ecology(_rich_intent())
    fixed_json = manifest.derived_value("reference-ecology.fixed-reference-config")
    assert isinstance(fixed_json, str)
    fixed = json.loads(fixed_json)
    assert "traits" in fixed
    assert "physiological_tradeoffs" in fixed
    assert "mating_type_investment_scales" in fixed
    assert "resource_request_amount" in fixed


def test_tampered_derived_assumptions_fail_before_execution() -> None:
    manifest = resolve_reference_ecology(_rich_intent())
    derived = list(manifest.derived_values)
    index = next(
        index
        for index, (slot_id, _) in enumerate(derived)
        if slot_id == "reference-ecology.fixed-reference-config"
    )
    derived[index] = (derived[index][0], "{}")
    tampered = attrs.evolve(manifest, derived_values=tuple(derived))
    with pytest.raises(IncompatibleManifestError):
        compile_reference_ecology(tampered)


def test_compile_delegates_to_existing_reference_preflight() -> None:
    manifest = resolve_reference_ecology(_rich_intent())
    prepared = compile_reference_ecology(manifest)
    assert prepared.compiled.simulation.state.step_index == 0
    assert prepared.evidence.population_recorder is not None
    assert prepared.evidence.event_recorder is not None


def test_lower_reference_validation_remains_authoritative() -> None:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        width=4,
        height=4,
        founder_population=100,
    )
    assert assess_reference_readiness(intent).state == "ready"
    manifest = resolve_reference_ecology(intent)
    with pytest.raises(ValueError, match="initial_population"):
        compile_reference_ecology(manifest)


def test_all_curated_evidence_reconstructs_fresh_existing_recorders() -> None:
    plan = ReferenceEvidencePlan(
        requested=(
            "reference-ecology.population-traits",
            "reference-ecology.committed-events",
            "reference-ecology.pedigree",
            "reference-ecology.genetic-composition",
            SPATIAL_EVIDENCE_ID,
        )
    )
    manifest = resolve_reference_ecology(_rich_intent(), plan)
    first = compile_reference_ecology(manifest, plan)
    second = compile_reference_ecology(manifest, plan)
    assert first.evidence.population_recorder is not second.evidence.population_recorder
    assert first.evidence.pedigree_recorder is not second.evidence.pedigree_recorder
    assert first.evidence.genetic_recorder is not second.evidence.genetic_recorder
    assert first.evidence.spatial_recorder is not second.evidence.spatial_recorder


def test_spatial_evidence_has_nonblocking_volume_advisory() -> None:
    plan = ReferenceEvidencePlan(requested=(SPATIAL_EVIDENCE_ID,))
    assert assess_reference_readiness(_rich_intent(), plan).state == "ready"
    advisories = evidence_advisories(plan)
    assert len(advisories) == 1
    assert advisories[0].evidence_id == SPATIAL_EVIDENCE_ID


def test_semantic_diff_uses_stable_recipe_meaning() -> None:
    before = resolve_reference_ecology(_rich_intent())
    after = resolve_reference_ecology(attrs.evolve(_rich_intent(), max_speed=3))
    diff = semantic_reference_diff(before, after)
    assert [change.slot_id for change in diff.explicit_changes] == [
        "reference-ecology.founder-max-speed"
    ]
