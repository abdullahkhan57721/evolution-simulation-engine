"""WB2 tests for curated B3 identity, exact reproduction, and fork lineage."""

from __future__ import annotations

import json
from typing import cast

import attrs
import pytest

import evo_engine.workbench.b3_curated as b3_module
from evo_engine.experiments.b3_flagship import (
    B3FounderReproductiveSuccess,
    B3MatchedPairSummary,
    B3ResourceGenerationAudit,
    B3ResourceGeography,
    B3RunSummary,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_BROAD_PATCH_RADIUS,
    B3_COMPACT_PATCH_RADIUS,
    B3_CONFIRMATION_SEEDS,
    B3_COUNTERBALANCE_SEEDS,
    B3_PRIMARY_STEP,
    B3FlagshipSpecification,
    build_b3_flagship_specification,
)
from evo_engine.workbench import IncompatibleManifestError
from evo_engine.workbench.b3_curated import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3_SCENARIO_ORIGIN_ID,
    B3_TREATMENT_RADIUS_SLOT,
    B3_VALIDATED_SCENARIO_ID,
    B3EvidencePlan,
    B3StudyRevision,
    compile_b3_curated,
    create_b3_study_revision,
    diff_b3_study_revisions,
    fork_b3_study_revision,
    run_b3_study_revision,
)


def _canonical(revision_id: str = "b3-r1") -> B3StudyRevision:
    return create_b3_study_revision(revision_id=revision_id)


def _summary(specification: object) -> B3RunSummary:
    spec = cast(B3FlagshipSpecification, specification)
    return B3RunSummary(
        seed=spec.seed,
        environment=spec.environment,
        founder_assignment=spec.founder_assignment,
        extinction_step=None,
        genetic_trajectory=(),
        population_trajectory=(),
        founder_reproductive_success=B3FounderReproductiveSuccess(
            low_speed_count=10,
            low_speed_mean=0.0,
            high_speed_count=10,
            high_speed_mean=0.0,
        ),
        resource_geography=B3ResourceGeography(
            resource_cell_observations=0,
            compact_support_cell_observations=0,
            compact_support_fraction=None,
            unique_resource_cells=0,
        ),
        resource_generation_audit=B3ResourceGenerationAudit(
            generation_event_count=0,
            total_generated_amount=0,
            compact_support_event_count=0,
            compact_support_fraction=None,
            unique_generation_cells=0,
        ),
        mechanism_episodes=(),
    )


def test_canonical_b3_round_trips_exact_manifest_and_validated_identity() -> None:
    revision = _canonical()

    encoded = revision.to_json()
    loaded = B3StudyRevision.from_json(encoded)

    assert loaded == revision
    assert loaded.to_json() == encoded
    assert loaded.manifest.to_json() == revision.manifest.to_json()
    assert loaded.manifest.digest == revision.manifest.digest
    assert loaded.scenario_origin == B3_SCENARIO_ORIGIN_ID
    assert loaded.scenario_identity == B3_VALIDATED_SCENARIO_ID
    assert loaded.study_kind == "validated-b3"
    assert loaded.evidence_plan.requested == B3_REQUIRED_EVIDENCE_IDS


def test_load_uses_stored_b3_manifest_without_reresolving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = _canonical()
    encoded = revision.to_json()

    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("load must not resolve current B3 defaults")

    monkeypatch.setattr(b3_module, "resolve_b3_curated", fail_if_called)

    loaded = B3StudyRevision.from_json(encoded)
    assert loaded.manifest == revision.manifest


def test_manifest_exposes_frozen_authoritative_b3_assumptions() -> None:
    revision = _canonical()
    manifest = revision.manifest
    authoritative = build_b3_flagship_specification(
        seed=B3_CONFIRMATION_SEEDS[0],
        environment="compact_patch",
    )

    assert manifest.explicit_value(B3_TREATMENT_RADIUS_SLOT) == B3_COMPACT_PATCH_RADIUS
    assert manifest.derived_value("b3.config.width") == authoritative.config.width == 12
    assert (
        manifest.derived_value("b3.config.height") == authoritative.config.height == 12
    )
    assert manifest.derived_value("b3.config.initial-population") == 20
    assert manifest.derived_value("b3.config.initial-energy") == 30
    assert manifest.derived_value("b3.config.max-steps") == 50
    assert manifest.derived_value("b3.config.mutation-probability-ppm") == 0
    assert manifest.derived_value("b3.config.mating-radius") == 3
    assert manifest.derived_value("b3.primary-step-index") == B3_PRIMARY_STEP
    assert manifest.derived_value("b3.confirmation-seeds") == "5,17,29,43,61,79,97,113"
    assert manifest.derived_value("b3.resource-geography.patch-centers") == "2,5;9,5"
    assert manifest.derived_value("b3.inheritance") == "ordinary-reference-sexual"
    assert manifest.derived_value("b3.primary-founder-assignment") == "standard"
    assert manifest.derived_value("b3.counterbalance-founder-assignment") == "swapped"
    assert (
        manifest.derived_value("b3.counterbalance-design")
        == "swap-focal-values-across-deterministic-founder-id-position-pattern"
    )
    assert (
        manifest.derived_value("b3.treatment-integrity")
        == "same-seed-control-and-primary-treatment-differ-only-resource-placement"
    )
    assert (
        manifest.derived_value("b3.rng-coupling")
        == "blocked-by-seed-not-lockstep-after-treatment"
    )
    assert (
        manifest.derived_value("b3.representative-story-semantics")
        == "selected-after-confirmation-by-predeclared-b3-rule"
    )
    assert (
        manifest.derived_value("b3.representative-selection-authority")
        == "existing-b3-scientific-handoff"
    )
    assert "seed-5" not in manifest.to_json()


def test_b3_manifest_remains_renderer_neutral() -> None:
    encoded = _canonical().manifest.to_json().lower()

    for renderer_term in ("camera", "manim", "plotly", "streamlit", "blender", "css"):
        assert renderer_term not in encoded


def test_compile_reuses_authoritative_b3_integrity_and_case_structure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = _canonical()
    calls = 0
    original = b3_module.validate_b3_treatment_integrity

    def spy(control: object, treatment: object) -> None:
        nonlocal calls
        calls += 1
        original(
            cast(B3FlagshipSpecification, control),
            cast(B3FlagshipSpecification, treatment),
        )

    monkeypatch.setattr(b3_module, "validate_b3_treatment_integrity", spy)

    compiled = compile_b3_curated(revision.manifest, revision.evidence_plan)

    assert calls == len(B3_CONFIRMATION_SEEDS) + len(B3_COUNTERBALANCE_SEEDS)
    assert len(compiled.confirmation_pairs) == len(B3_CONFIRMATION_SEEDS)
    assert len(compiled.radius_sensitivity) == len(B3_CONFIRMATION_SEEDS)
    assert len(compiled.counterbalanced_pairs) == len(B3_COUNTERBALANCE_SEEDS)
    assert {pair.control.environment for pair in compiled.confirmation_pairs} == {
        "uniform"
    }
    assert {pair.treatment.environment for pair in compiled.confirmation_pairs} == {
        "compact_patch"
    }
    assert {run.environment for run in compiled.radius_sensitivity} == {"broad_patch"}


def test_compile_rejects_tampered_or_incompatible_exact_manifest() -> None:
    revision = _canonical()
    values = list(revision.manifest.derived_values)
    index = next(
        index
        for index, (slot_id, _) in enumerate(values)
        if slot_id == "b3.config.mating-radius"
    )
    values[index] = ("b3.config.mating-radius", 999)
    tampered = attrs.evolve(revision.manifest, derived_values=tuple(values))
    incompatible = attrs.evolve(revision.manifest, engine_version="historical-version")

    with pytest.raises(IncompatibleManifestError, match="assumptions"):
        compile_b3_curated(tampered, revision.evidence_plan)
    with pytest.raises(IncompatibleManifestError, match="requires"):
        compile_b3_curated(incompatible, revision.evidence_plan)


def test_radius_two_fork_retains_origin_loses_identity_and_reports_science() -> None:
    parent = _canonical()
    child = fork_b3_study_revision(parent, revision_id="b3-r2")
    difference = diff_b3_study_revisions(parent, child)

    assert child.parent_revision_id == parent.revision_id
    assert child.scenario_origin == B3_SCENARIO_ORIGIN_ID
    assert child.scenario_identity is None
    assert child.study_kind == "b3-derived-custom"
    assert child.intent.treatment_radius == B3_BROAD_PATCH_RADIUS
    assert [
        (change.slot_id, change.before, change.after)
        for change in difference.explicit_changes
    ] == [
        (
            B3_TREATMENT_RADIUS_SLOT,
            B3_COMPACT_PATCH_RADIUS,
            B3_BROAD_PATCH_RADIUS,
        )
    ]
    assert difference.scenario_identity_change is not None
    assert difference.scenario_identity_change.before == B3_VALIDATED_SCENARIO_ID
    assert difference.scenario_identity_change.after is None
    derived = {change.slot_id for change in difference.derived_changes}
    assert "b3.treatment-resource-geography" in derived
    assert "b3.resource-geography.patch-radius" in derived
    assert "b3.radius-sensitivity-role" in derived
    assert "b3.radius-sensitivity-founder-assignment" in derived
    assert "b3.representative-story-semantics" in derived
    assert "b3.representative-selection-authority" in derived
    assert "b3.original-headline-claim-applicability" in derived
    assert "b3.counterbalance-founder-assignment" in difference.unchanged_frozen_slots
    assert "b3.config.mutation-probability-ppm" in difference.unchanged_frozen_slots


def test_fork_is_immutable_and_rejects_arbitrary_b3_editing() -> None:
    parent = _canonical()
    parent_json = parent.to_json()

    child = fork_b3_study_revision(parent, revision_id="b3-r2")

    assert parent.to_json() == parent_json
    assert parent.scenario_identity == B3_VALIDATED_SCENARIO_ID
    assert parent.intent.treatment_radius == B3_COMPACT_PATCH_RADIUS
    assert child.runs == ()
    with pytest.raises(ValueError, match="only the B3 radius-1 to radius-2 fork"):
        fork_b3_study_revision(
            parent,
            revision_id="unsupported",
            treatment_radius=3,
        )


def test_radius_two_compile_promotes_existing_sensitivity_without_duplication() -> None:
    child = fork_b3_study_revision(_canonical(), revision_id="b3-r2")

    compiled = compile_b3_curated(child.manifest, child.evidence_plan)

    assert compiled.radius_sensitivity == ()
    assert {pair.treatment.environment for pair in compiled.confirmation_pairs} == {
        "broad_patch"
    }
    assert {pair.control.environment for pair in compiled.confirmation_pairs} == {
        "uniform"
    }
    assert {pair.treatment.environment for pair in compiled.counterbalanced_pairs} == {
        "broad_patch"
    }


def test_run_consumes_existing_b3_summary_contracts_and_preserves_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = _canonical()

    monkeypatch.setattr(
        b3_module, "run_b3_flagship", lambda specification: specification
    )
    monkeypatch.setattr(b3_module, "summarize_b3_run", _summary)

    result = run_b3_study_revision(revision, run_id="b3-run")

    assert result.scenario_origin == B3_SCENARIO_ORIGIN_ID
    assert result.scenario_identity == B3_VALIDATED_SCENARIO_ID
    assert result.provenance.study_revision_id == revision.revision_id
    assert result.provenance.manifest_digest == revision.manifest.digest
    assert result.provenance.evidence_ids == B3_REQUIRED_EVIDENCE_IDS
    assert len(result.confirmation) == len(B3_CONFIRMATION_SEEDS)
    assert all(
        isinstance(artifacts.summary, B3MatchedPairSummary)
        for artifacts in result.confirmation
    )
    assert all(
        isinstance(artifacts.summary, B3RunSummary)
        for artifacts in result.radius_sensitivity
    )
    assert len(result.counterbalanced) == len(B3_COUNTERBALANCE_SEEDS)


def test_recorded_b3_run_provenance_round_trips_without_mutating_science(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = _canonical()
    empty = b3_module.CompiledB3CuratedStudy(
        confirmation_pairs=(),
        radius_sensitivity=(),
        counterbalanced_pairs=(),
    )
    monkeypatch.setattr(b3_module, "compile_b3_curated", lambda *args: empty)

    result = run_b3_study_revision(revision, run_id="run-1")
    recorded = revision.with_run(result.provenance)

    assert revision.runs == ()
    assert recorded.runs == (result.provenance,)
    assert recorded.manifest == revision.manifest
    assert B3StudyRevision.from_json(recorded.to_json()) == recorded


def test_curated_b3_evidence_plan_cannot_drop_authoritative_streams() -> None:
    with pytest.raises(ValueError, match="requires its frozen existing evidence set"):
        B3EvidencePlan(requested=(B3_REQUIRED_EVIDENCE_IDS[0],))


def test_b3_loader_fails_honestly_on_unknown_format_instead_of_migrating() -> None:
    payload = json.loads(_canonical().to_json())
    payload["format_version"] = 2

    with pytest.raises(ValueError, match="format version"):
        B3StudyRevision.from_json(json.dumps(payload))


def test_b3_values_are_immutable() -> None:
    revision = _canonical()

    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        revision.scenario_identity = None  # type: ignore[misc]
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        revision.manifest.explicit_values = ()  # type: ignore[misc]
