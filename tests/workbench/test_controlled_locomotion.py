"""Tests for the bounded controlled-locomotion Workbench recipe."""

from __future__ import annotations

import json

import attrs
import pytest

from evo_engine.experiments.e3_performance import E3_SPEED_GRID, build_e3_treatment
from evo_engine.genetics import MAX_SPEED
from evo_engine.presets.controlled_locomotion import ControlledLocomotionFounder
from evo_engine.workbench import (
    COMPILER_ID,
    COMPILER_VERSION,
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RECIPE_ID,
    RECIPE_VERSION,
    RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT,
    SUPPORTED_MAX_SPEED_MAXIMUM,
    SUPPORTED_MAX_SPEED_MINIMUM,
    ControlledLocomotionIntent,
    ControlledLocomotionManifest,
    EvidencePlan,
    IncompatibleManifestError,
    WorkbenchNotReadyError,
    assess_readiness,
    compile_controlled_locomotion,
    resolve_controlled_locomotion,
    semantic_diff,
)


def _intent(
    *,
    max_speed: int = 3,
    geography: str = "local_resource",
    seed: int = 17,
) -> ControlledLocomotionIntent:
    return ControlledLocomotionIntent(
        max_speed=max_speed,
        resource_geography=geography,
        seed=seed,
    )


def test_recipe_identity_and_semantic_slots_are_stable_scientific_ids() -> None:
    assert RECIPE_ID == "controlled-clonal-locomotion"
    assert RECIPE_VERSION == 1
    assert COMPILER_ID == "workbench.controlled-clonal-locomotion"
    assert COMPILER_VERSION == 1
    assert (MAX_SPEED_SLOT, RESOURCE_GEOGRAPHY_SLOT, SEED_SLOT) == (
        "controlled-locomotion.max-speed",
        "controlled-locomotion.resource-geography",
        "controlled-locomotion.seed",
    )
    for semantic_id in (MAX_SPEED_SLOT, RESOURCE_GEOGRAPHY_SLOT, SEED_SLOT):
        assert ".py" not in semantic_id
        assert "evo_engine." not in semantic_id
        assert ":" not in semantic_id


def test_workbench_range_matches_characterized_e3_grid_not_engine_range() -> None:
    assert SUPPORTED_MAX_SPEED_MINIMUM == min(E3_SPEED_GRID) == 1
    assert SUPPORTED_MAX_SPEED_MAXIMUM == max(E3_SPEED_GRID) == 10

    # The lower controlled-locomotion model remains broader: this is not a new
    # biological/engine invariant.
    assert ControlledLocomotionFounder(max_speed=0, x=0, y=0).max_speed == 0
    assert ControlledLocomotionFounder(max_speed=20, x=0, y=0).max_speed == 20


@pytest.mark.parametrize("max_speed", [0, 11])
def test_outside_workbench_speed_range_is_blocked(max_speed: int) -> None:
    readiness = assess_readiness(_intent(max_speed=max_speed))

    assert readiness.state == "blocked"
    assert any(
        diagnostic.code == "unsupported-value" and diagnostic.slot_id == MAX_SPEED_SLOT
        for diagnostic in readiness.diagnostics
    )
    with pytest.raises(WorkbenchNotReadyError) as error:
        resolve_controlled_locomotion(_intent(max_speed=max_speed))
    assert error.value.readiness == readiness


def test_incomplete_intent_is_draft_and_reports_missing_selections() -> None:
    readiness = assess_readiness(ControlledLocomotionIntent())

    assert readiness.state == "draft"
    assert {diagnostic.slot_id for diagnostic in readiness.diagnostics} == {
        MAX_SPEED_SLOT,
        RESOURCE_GEOGRAPHY_SLOT,
        SEED_SLOT,
    }


def test_unsupported_geography_and_evidence_are_recipe_owned_blockers() -> None:
    readiness = assess_readiness(
        _intent(geography="arbitrary_patch"),
        EvidencePlan(requested=("unknown-evidence",)),
    )

    assert readiness.state == "blocked"
    assert {diagnostic.code for diagnostic in readiness.diagnostics} == {
        "unsupported-value",
        "unsupported-evidence",
    }


def test_empty_evidence_plan_remains_draft() -> None:
    readiness = assess_readiness(_intent(), EvidencePlan(requested=()))

    assert readiness.state == "draft"
    assert readiness.diagnostics[0].code == "missing-evidence"


def test_resolution_is_deterministic_and_separates_explicit_from_derived() -> None:
    first = resolve_controlled_locomotion(_intent())
    second = resolve_controlled_locomotion(_intent())

    assert first == second
    assert first.digest == second.digest
    assert first.explicit_values == (
        (MAX_SPEED_SLOT, 3),
        (RESOURCE_GEOGRAPHY_SLOT, "local_resource"),
        (SEED_SLOT, 17),
    )
    assert first.derived_value("controlled-locomotion.initial-focal-max-speed") == 3
    assert first.derived_value("controlled-locomotion.inherited-traits") == MAX_SPEED
    assert first.derived_value("controlled-locomotion.inheritance") == "clonal"
    assert first.derived_value("controlled-locomotion.mutation") == "off"
    assert first.derived_value("controlled-locomotion.sensing") == "perfect-full-world"
    assert (
        first.derived_value("controlled-locomotion.movement-targeting")
        == "nearest-resource"
    )
    for absent_process in (
        "mate-search",
        "predation",
        "metabolism",
        "growth",
        "aging",
        "renewable-resource-generation",
    ):
        assert first.derived_value(f"controlled-locomotion.{absent_process}") is False


def test_resource_layout_is_resolved_from_existing_e3_treatment() -> None:
    local = resolve_controlled_locomotion(_intent(geography="local_resource"))
    corridor = resolve_controlled_locomotion(_intent(geography="separated_corridor"))
    local_layout = json.loads(
        str(local.derived_value("controlled-locomotion.resource-deposit-layout"))
    )
    corridor_layout = json.loads(
        str(corridor.derived_value("controlled-locomotion.resource-deposit-layout"))
    )

    assert local_layout == [
        list(deposit)
        for deposit in build_e3_treatment(
            max_speed=3, environment="local_resource"
        ).resource_deposits
    ]
    assert corridor_layout == [
        list(deposit)
        for deposit in build_e3_treatment(
            max_speed=3, environment="separated_corridor"
        ).resource_deposits
    ]
    assert local_layout != corridor_layout


def test_manifest_is_immutable_and_round_trips_canonically() -> None:
    manifest = resolve_controlled_locomotion(_intent())

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        manifest.recipe_version = 2  # type: ignore[misc]
    encoded = manifest.to_json()
    loaded = ControlledLocomotionManifest.from_json(encoded)
    assert loaded == manifest
    assert loaded.to_json() == encoded
    assert loaded.digest == manifest.digest


def test_compile_reconstructs_fresh_existing_recorders_before_preflight() -> None:
    manifest = resolve_controlled_locomotion(_intent())

    first = compile_controlled_locomotion(manifest)
    second = compile_controlled_locomotion(manifest)

    assert first.evidence.population_recorder is not None
    assert first.evidence.event_recorder is not None
    assert second.evidence.population_recorder is not first.evidence.population_recorder
    assert second.evidence.event_recorder is not first.evidence.event_recorder
    assert first.evidence.population_recorder.required_traits == frozenset({MAX_SPEED})
    assert first.compiled.dependency_report.missing == frozenset()
    assert any(
        dependency.name == MAX_SPEED
        for dependency in first.compiled.dependency_report.required
    )


def test_compile_supports_each_concrete_evidence_stream_separately() -> None:
    manifest = resolve_controlled_locomotion(_intent())

    population_only = compile_controlled_locomotion(
        manifest,
        EvidencePlan(requested=(POPULATION_EVIDENCE_ID,)),
    )
    events_only = compile_controlled_locomotion(
        manifest,
        EvidencePlan(requested=(EVENT_EVIDENCE_ID,)),
    )

    assert population_only.evidence.population_recorder is not None
    assert population_only.evidence.event_recorder is None
    assert events_only.evidence.population_recorder is None
    assert events_only.evidence.event_recorder is not None


def test_compile_rejects_empty_or_unsupported_evidence_plan() -> None:
    manifest = resolve_controlled_locomotion(_intent())

    with pytest.raises(ValueError, match="at least one"):
        compile_controlled_locomotion(manifest, EvidencePlan(requested=()))
    with pytest.raises(ValueError, match="Unsupported WB1 evidence"):
        compile_controlled_locomotion(
            manifest,
            EvidencePlan(requested=("unsupported",)),
        )


def test_compile_rejects_incompatible_engine_identity() -> None:
    manifest = resolve_controlled_locomotion(_intent())
    incompatible = attrs.evolve(manifest, engine_version="different-version")

    with pytest.raises(IncompatibleManifestError, match="requires"):
        compile_controlled_locomotion(incompatible)


def test_compile_rejects_tampered_derived_manifest_instead_of_silently_reresolving() -> (
    None
):
    manifest = resolve_controlled_locomotion(_intent())
    tampered = attrs.evolve(
        manifest,
        derived_values=tuple(
            (slot_id, 99 if slot_id == "controlled-locomotion.body-mass" else value)
            for slot_id, value in manifest.derived_values
        ),
    )

    with pytest.raises(IncompatibleManifestError, match="derived values"):
        compile_controlled_locomotion(tampered)


def test_semantic_diff_separates_explicit_change_from_derived_consequence() -> None:
    before = resolve_controlled_locomotion(_intent(max_speed=3))
    after = resolve_controlled_locomotion(_intent(max_speed=4))

    difference = semantic_diff(before, after)

    assert [
        (change.slot_id, change.before, change.after)
        for change in difference.explicit_changes
    ] == [(MAX_SPEED_SLOT, 3, 4)]
    assert any(
        change.slot_id == "controlled-locomotion.initial-focal-max-speed"
        and change.before == 3
        and change.after == 4
        for change in difference.derived_changes
    )
    assert not any(
        change.slot_id == "controlled-locomotion.inheritance"
        for change in difference.derived_changes
    )


def test_semantic_diff_reports_geography_as_scientific_meaning_not_python_paths() -> (
    None
):
    before = resolve_controlled_locomotion(_intent(geography="local_resource"))
    after = resolve_controlled_locomotion(_intent(geography="separated_corridor"))

    difference = semantic_diff(before, after)

    assert [change.slot_id for change in difference.explicit_changes] == [
        RESOURCE_GEOGRAPHY_SLOT
    ]
    assert [change.slot_id for change in difference.derived_changes] == [
        "controlled-locomotion.resource-deposit-layout"
    ]


def test_public_values_reject_wrong_container_and_scalar_types() -> None:
    with pytest.raises(TypeError, match="max_speed"):
        ControlledLocomotionIntent(max_speed=True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="resource_geography"):
        ControlledLocomotionIntent(resource_geography=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="seed"):
        ControlledLocomotionIntent(seed=True)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="requested"):
        EvidencePlan(requested=[EVENT_EVIDENCE_ID])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate"):
        EvidencePlan(requested=(EVENT_EVIDENCE_ID, EVENT_EVIDENCE_ID))
