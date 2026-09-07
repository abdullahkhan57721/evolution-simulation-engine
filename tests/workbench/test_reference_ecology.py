"""Focused contracts for the bounded WB4 reference-ecology recipe."""

from __future__ import annotations

import attrs

from evo_engine.workbench.reference_ecology import (
    GAUSSIAN_STDDEV_SLOT,
    MUTATION_MAX_CHANGE_SLOT,
    MUTATION_PROBABILITY_SLOT,
    PATCH_1_X_SLOT,
    PATCH_2_X_SLOT,
    REFERENCE_EXTENSION_CAPABILITIES,
    REFERENCE_SLOT_METADATA,
    ReferenceEcologyIntent,
    ReferenceEvidencePlan,
    assess_reference_readiness,
    compile_reference_ecology,
    resolve_reference_ecology,
    semantic_diff,
)


def _ready_intent() -> ReferenceEcologyIntent:
    return ReferenceEcologyIntent(
        width=12,
        height=12,
        founder_population=20,
        founder_energy=30,
        horizon=30,
        seed=17,
        max_speed=2,
        sensory_range=5,
        sensory_accuracy=90,
        exploration_movement="gaussian",
        gaussian_standard_deviation=2,
        resource_geography="two_patches",
        resource_generation_amount=6,
        resource_deposits_per_step=8,
        patch_1_center_x=2,
        patch_1_center_y=5,
        patch_1_radius=1,
        patch_2_center_x=9,
        patch_2_center_y=5,
        patch_2_radius=1,
        mutation_enabled=True,
        mutation_probability_ppm=10_000,
        mutation_max_change=1,
        recombination_probability_ppm=500_000,
    )


def test_support_tiers_are_explicit_and_do_not_expose_python_paths() -> None:
    tiers = {metadata.support_tier for metadata in REFERENCE_SLOT_METADATA}
    assert tiers == {"guided", "advanced"}
    assert all("." not in metadata.label for metadata in REFERENCE_SLOT_METADATA)
    assert REFERENCE_EXTENSION_CAPABILITIES


def test_ready_rich_reference_recipe_resolves_deterministically() -> None:
    intent = _ready_intent()
    assert assess_reference_readiness(intent).state == "ready"
    assert resolve_reference_ecology(intent) == resolve_reference_ecology(intent)


def test_non_gaussian_movement_normalizes_stale_gaussian_value_away() -> None:
    manifest = resolve_reference_ecology(
        attrs.evolve(
            _ready_intent(),
            exploration_movement="moore",
            gaussian_standard_deviation=9,
        )
    )
    assert manifest.explicit_value_or_none(GAUSSIAN_STDDEV_SLOT) is None


def test_disabled_mutation_normalizes_stale_mutation_parameters_away() -> None:
    manifest = resolve_reference_ecology(
        attrs.evolve(
            _ready_intent(),
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
        attrs.evolve(_ready_intent(), resource_geography="uniform")
    )
    assert manifest.explicit_value_or_none(PATCH_1_X_SLOT) is None
    assert manifest.explicit_value_or_none(PATCH_2_X_SLOT) is None


def test_manifest_round_trip_is_exact_and_canonical() -> None:
    manifest = resolve_reference_ecology(_ready_intent())
    loaded = type(manifest).from_json(manifest.to_json())
    assert loaded == manifest
    assert loaded.to_json() == manifest.to_json()
    assert loaded.digest == manifest.digest


def test_compile_delegates_to_existing_reference_preflight() -> None:
    manifest = resolve_reference_ecology(_ready_intent())
    prepared = compile_reference_ecology(manifest, ReferenceEvidencePlan())
    assert prepared.compiled.simulation.state.step_index == 0
    assert prepared.evidence.population_recorder is not None
    assert prepared.evidence.event_recorder is not None


def test_semantic_diff_uses_stable_recipe_meaning() -> None:
    before = resolve_reference_ecology(_ready_intent())
    after = resolve_reference_ecology(attrs.evolve(_ready_intent(), max_speed=3))
    diff = semantic_diff(before, after)
    assert [change.slot_id for change in diff.explicit_changes] == [
        "reference-ecology.founder-max-speed"
    ]
