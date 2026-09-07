"""Validation and compatibility coverage for the bounded WB4 reference recipe."""

from __future__ import annotations

import json
from typing import Any, cast

import attrs
import pytest

from evo_engine.workbench.controlled_locomotion import (
    IncompatibleManifestError,
    WorkbenchNotReadyError,
)
from evo_engine.workbench.reference_ecology import (
    EVENT_EVIDENCE_ID,
    EXPLORATION_MOVEMENT_SLOT,
    GENETIC_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    MUTATION_ENABLED_SLOT,
    PEDIGREE_EVIDENCE_ID,
    POPULATION_EVIDENCE_ID,
    REFERENCE_RECIPE_ID,
    REFERENCE_RECIPE_VERSION,
    RESOURCE_GEOGRAPHY_SLOT,
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
    slot_metadata,
)
from evo_engine.workbench.reference_study import (
    REFERENCE_STUDY_FORMAT_ID,
    REFERENCE_STUDY_FORMAT_VERSION,
    ReferenceStudyRevision,
    create_reference_study_revision,
    diff_reference_study_revisions,
    fork_reference_study_revision,
    run_reference_study_revision,
)
from evo_engine.workbench.study import WorkbenchRunProvenance


def _rich_intent() -> ReferenceEcologyIntent:
    return attrs.evolve(
        default_reference_ecology_intent(),
        horizon=2,
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


def _revision() -> ReferenceStudyRevision:
    return create_reference_study_revision(
        revision_id="validation-study",
        intent=attrs.evolve(default_reference_ecology_intent(), horizon=2, seed=11),
    )


def _revision_payload() -> dict[str, Any]:
    payload = json.loads(_revision().to_json())
    assert isinstance(payload, dict)
    return payload


def _manifest_payload() -> dict[str, Any]:
    payload = json.loads(resolve_reference_ecology(_rich_intent()).to_json())
    assert isinstance(payload, dict)
    return payload


def _provenance(revision: ReferenceStudyRevision) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id="validation-run",
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )


@pytest.mark.parametrize(
    "requested, error_type, match",
    [
        (cast(Any, [POPULATION_EVIDENCE_ID]), TypeError, "tuple"),
        (
            (POPULATION_EVIDENCE_ID, POPULATION_EVIDENCE_ID),
            ValueError,
            "duplicate",
        ),
        (("",), TypeError, "non-empty evidence ID"),
        ((cast(Any, 3),), TypeError, "non-empty evidence ID"),
    ],
)
def test_reference_evidence_plan_rejects_malformed_requests(
    requested: Any,
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        ReferenceEvidencePlan(requested=requested)


def test_slot_metadata_and_advisories_reject_unsupported_inputs() -> None:
    with pytest.raises(KeyError, match="Unsupported reference-ecology slot"):
        slot_metadata("reference-ecology.unknown")
    with pytest.raises(KeyError):
        is_slot_applicable(default_reference_ecology_intent(), "reference-ecology.unknown")
    with pytest.raises(TypeError, match="ReferenceEvidencePlan"):
        evidence_advisories(cast(Any, object()))
    assert evidence_advisories(ReferenceEvidencePlan()) == ()


def test_reference_readiness_reports_draft_for_missing_authoring_state() -> None:
    readiness = assess_reference_readiness(
        ReferenceEcologyIntent(),
        ReferenceEvidencePlan(requested=()),
    )
    assert readiness.state == "draft"
    assert any(item.code == "missing-selection" for item in readiness.diagnostics)
    assert any(item.code == "missing-evidence" for item in readiness.diagnostics)


def test_reference_readiness_reports_blocked_for_unsupported_authoring_state() -> None:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        width=cast(Any, True),
        founder_population=101,
        seed=cast(Any, "seed"),
        exploration_movement="teleport",
        resource_geography="many_patches",
        mutation_enabled=cast(Any, "yes"),
        recombination_probability_ppm=-1,
    )
    readiness = assess_reference_readiness(
        intent,
        ReferenceEvidencePlan(requested=("reference-ecology.unsupported",)),
    )
    assert readiness.state == "blocked"
    assert any(item.slot_id == EXPLORATION_MOVEMENT_SLOT for item in readiness.diagnostics)
    assert any(item.slot_id == RESOURCE_GEOGRAPHY_SLOT for item in readiness.diagnostics)
    assert any(item.slot_id == MUTATION_ENABLED_SLOT for item in readiness.diagnostics)
    assert any(item.code == "unsupported-evidence" for item in readiness.diagnostics)


def test_reference_readiness_requires_active_conditional_values() -> None:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        exploration_movement="gaussian",
        gaussian_standard_deviation=None,
        resource_geography="two_patches",
        patch_1_center_x=None,
        patch_1_center_y=None,
        patch_1_radius=None,
        patch_2_center_x=None,
        patch_2_center_y=None,
        patch_2_radius=None,
        mutation_enabled=True,
        mutation_probability_ppm=None,
        mutation_max_change=None,
    )
    readiness = assess_reference_readiness(intent)
    assert readiness.state == "draft"
    assert len(readiness.diagnostics) >= 9


def test_reference_readiness_blocks_patch_centers_outside_world() -> None:
    intent = attrs.evolve(
        _rich_intent(),
        patch_1_center_x=cast(int, _rich_intent().width),
        patch_2_center_y=cast(int, _rich_intent().height),
    )
    readiness = assess_reference_readiness(intent)
    assert readiness.state == "blocked"
    assert sum("inside the world" in item.message for item in readiness.diagnostics) == 2


def test_reference_readiness_type_checks_public_inputs() -> None:
    with pytest.raises(TypeError, match="ReferenceEcologyIntent"):
        assess_reference_readiness(cast(Any, object()))
    with pytest.raises(TypeError, match="ReferenceEvidencePlan"):
        assess_reference_readiness(
            default_reference_ecology_intent(),
            cast(Any, object()),
        )


def test_resolve_rejects_nonready_intent() -> None:
    with pytest.raises(WorkbenchNotReadyError):
        resolve_reference_ecology(ReferenceEcologyIntent())


@pytest.mark.parametrize("movement", ["moore", "von_neumann", "uniform", "gaussian"])
def test_compile_reconstructs_every_supported_exploration_movement(movement: str) -> None:
    intent = attrs.evolve(
        default_reference_ecology_intent(),
        horizon=1,
        exploration_movement=movement,
        gaussian_standard_deviation=1 if movement == "gaussian" else 9,
    )
    prepared = compile_reference_ecology(resolve_reference_ecology(intent))
    assert prepared.compiled.simulation.state.step_index == 0


@pytest.mark.parametrize(
    "evidence_id",
    [
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
        PEDIGREE_EVIDENCE_ID,
        GENETIC_EVIDENCE_ID,
        SPATIAL_EVIDENCE_ID,
    ],
)
def test_compile_reconstructs_each_supported_evidence_stream(evidence_id: str) -> None:
    plan = ReferenceEvidencePlan(requested=(evidence_id,))
    prepared = compile_reference_ecology(
        resolve_reference_ecology(default_reference_ecology_intent(), plan),
        plan,
    )
    assert prepared.compiled.simulation.state.step_index == 0


def test_compile_validates_manifest_and_evidence_inputs() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    with pytest.raises(TypeError, match="ReferenceEcologyManifest"):
        compile_reference_ecology(cast(Any, object()))
    with pytest.raises(TypeError, match="ReferenceEvidencePlan"):
        compile_reference_ecology(manifest, cast(Any, object()))
    with pytest.raises(ValueError, match="at least one evidence"):
        compile_reference_ecology(manifest, ReferenceEvidencePlan(requested=()))
    with pytest.raises(ValueError, match="Unsupported reference evidence IDs"):
        compile_reference_ecology(
            manifest,
            ReferenceEvidencePlan(requested=("reference-ecology.unsupported",)),
        )


def test_compile_rejects_incompatible_engine_version() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    incompatible = attrs.evolve(manifest, engine_version="999.999")
    with pytest.raises(IncompatibleManifestError, match="different engine version"):
        compile_reference_ecology(incompatible)


def test_semantic_reference_diff_validates_inputs() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    with pytest.raises(TypeError, match="ReferenceEcologyManifest"):
        semantic_reference_diff(cast(Any, object()), manifest)
    assert semantic_reference_diff(manifest, manifest).explicit_changes == ()
    assert semantic_reference_diff(manifest, manifest).derived_changes == ()


def test_manifest_accessors_raise_for_unknown_semantic_ids() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    with pytest.raises(KeyError):
        manifest.explicit_value("reference-ecology.unknown")
    with pytest.raises(KeyError):
        manifest.derived_value("reference-ecology.unknown")
    assert manifest.explicit_value_or_none("reference-ecology.unknown") is None


@pytest.mark.parametrize(
    "mutator, error_type, match",
    [
        (lambda value: cast(Any, 4), TypeError, "string"),
        (lambda value: json.dumps([]), ValueError, "object"),
    ],
)
def test_manifest_from_json_validates_top_level_value(
    mutator: Any,
    error_type: type[Exception],
    match: str,
) -> None:
    value = mutator(resolve_reference_ecology(default_reference_ecology_intent()).to_json())
    with pytest.raises(error_type, match=match):
        ReferenceEcologyManifest.from_json(value)


@pytest.mark.parametrize(
    "field, replacement, match",
    [
        ("recipe_id", 1, "recipe_id"),
        ("recipe_version", "1", "recipe_version"),
        ("explicit_values", "bad", "JSON array"),
        ("explicit_values", [["only-one"]], "two-item arrays"),
        ("explicit_values", [[1, 2]], "string ID and scalar value"),
    ],
)
def test_manifest_from_json_rejects_malformed_fields(
    field: str,
    replacement: Any,
    match: str,
) -> None:
    payload = _manifest_payload()
    payload[field] = replacement
    with pytest.raises((TypeError, ValueError), match=match):
        ReferenceEcologyManifest.from_json(json.dumps(payload))


def test_manifest_constructor_rejects_invalid_identity_and_schema() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    with pytest.raises(ValueError, match="Unsupported reference recipe/compiler identity"):
        attrs.evolve(manifest, recipe_id="other")
    with pytest.raises(ValueError, match="engine_version"):
        attrs.evolve(manifest, engine_version="")
    with pytest.raises(ValueError, match="normalized reference schema"):
        attrs.evolve(manifest, explicit_values=manifest.explicit_values[:-1])
    with pytest.raises(ValueError, match="duplicate semantic IDs"):
        attrs.evolve(
            manifest,
            explicit_values=(*manifest.explicit_values, manifest.explicit_values[0]),
        )
    with pytest.raises(TypeError, match="must be a tuple"):
        attrs.evolve(manifest, explicit_values=cast(Any, list(manifest.explicit_values)))
    with pytest.raises(TypeError, match="two-item tuple"):
        attrs.evolve(manifest, explicit_values=cast(Any, (("bad",),)))
    with pytest.raises(TypeError, match="key must be a non-empty string"):
        attrs.evolve(manifest, explicit_values=cast(Any, (("", 1),)))
    with pytest.raises(TypeError, match="supported scalar"):
        attrs.evolve(manifest, explicit_values=cast(Any, (("bad", 1.5),)))


def test_manifest_constructor_rejects_wrong_derived_schema() -> None:
    manifest = resolve_reference_ecology(default_reference_ecology_intent())
    with pytest.raises(ValueError, match="derived_values"):
        attrs.evolve(manifest, derived_values=manifest.derived_values[:-1])


def test_reference_study_constructor_validates_core_invariants() -> None:
    revision = _revision()
    with pytest.raises(ValueError, match="revision_id"):
        attrs.evolve(revision, revision_id="")
    with pytest.raises(TypeError, match="intent"):
        ReferenceStudyRevision(
            revision_id="bad-intent",
            intent=cast(Any, object()),
            manifest=revision.manifest,
            evidence_plan=revision.evidence_plan,
        )
    with pytest.raises(TypeError, match="manifest"):
        ReferenceStudyRevision(
            revision_id="bad-manifest",
            intent=revision.intent,
            manifest=cast(Any, object()),
            evidence_plan=revision.evidence_plan,
        )
    with pytest.raises(TypeError, match="evidence_plan"):
        ReferenceStudyRevision(
            revision_id="bad-plan",
            intent=revision.intent,
            manifest=revision.manifest,
            evidence_plan=cast(Any, object()),
        )
    with pytest.raises(ValueError, match="parent_revision_id"):
        attrs.evolve(revision, parent_revision_id="")
    with pytest.raises(ValueError, match="must differ"):
        attrs.evolve(revision, parent_revision_id=revision.revision_id)


def test_reference_study_rejects_stale_or_manifest_mismatched_intent() -> None:
    revision = _revision()
    stale = attrs.evolve(revision.intent, gaussian_standard_deviation=3)
    with pytest.raises(ValueError, match="inactive stale values"):
        attrs.evolve(revision, intent=stale)
    changed = attrs.evolve(revision.intent, max_speed=3)
    with pytest.raises(ValueError, match="does not match stored manifest"):
        attrs.evolve(revision, intent=changed)


def test_reference_study_run_collection_validates_provenance() -> None:
    revision = _revision()
    provenance = _provenance(revision)
    updated = revision.with_run(provenance)
    with pytest.raises(ValueError, match="already recorded"):
        updated.with_run(provenance)
    with pytest.raises(TypeError, match="WorkbenchRunProvenance"):
        revision.with_run(cast(Any, object()))
    with pytest.raises(TypeError, match="runs must be a tuple"):
        attrs.evolve(revision, runs=cast(Any, [provenance]))
    with pytest.raises(TypeError, match=r"runs\[0\]"):
        attrs.evolve(revision, runs=(cast(Any, object()),))
    with pytest.raises(ValueError, match="different study revision"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, study_revision_id="other"),),
        )
    with pytest.raises(ValueError, match="different manifest"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, manifest_digest="other"),),
        )
    with pytest.raises(ValueError, match="different evidence plan"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, evidence_ids=(SPATIAL_EVIDENCE_ID,)),),
        )


def test_reference_study_from_json_validates_top_level_contract() -> None:
    with pytest.raises(TypeError, match="string"):
        ReferenceStudyRevision.from_json(cast(Any, 3))
    with pytest.raises(ValueError, match="object"):
        ReferenceStudyRevision.from_json(json.dumps([]))

    payload = _revision_payload()
    payload["format_id"] = "other"
    with pytest.raises(ValueError, match="format ID"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["format_version"] = REFERENCE_STUDY_FORMAT_VERSION + 1
    with pytest.raises(ValueError, match="format version"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["runs"] = "bad"
    with pytest.raises(TypeError, match="runs must be a JSON array"):
        ReferenceStudyRevision.from_json(json.dumps(payload))


def test_reference_study_from_json_validates_nested_fields() -> None:
    payload = _revision_payload()
    payload["evidence_plan"] = []
    with pytest.raises(TypeError, match="evidence_plan must be a JSON object"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["revision_id"] = 1
    with pytest.raises(TypeError, match="revision_id"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["evidence_plan"]["requested"] = [1]
    with pytest.raises(TypeError, match="requested must be a string array"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["parent_revision_id"] = 1
    with pytest.raises(TypeError, match="parent_revision_id"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["intent"]["width"] = "bad"
    with pytest.raises(TypeError, match="width"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["intent"]["mutation_enabled"] = "bad"
    with pytest.raises(TypeError, match="mutation_enabled"):
        ReferenceStudyRevision.from_json(json.dumps(payload))

    payload = _revision_payload()
    payload["runs"] = [1]
    with pytest.raises(TypeError, match="runs entries"):
        ReferenceStudyRevision.from_json(json.dumps(payload))


def test_reference_study_fork_diff_and_run_validate_types_and_identity() -> None:
    revision = _revision()
    with pytest.raises(TypeError, match="parent"):
        fork_reference_study_revision(
            cast(Any, object()),
            revision_id="child",
            intent=revision.intent,
        )
    with pytest.raises(ValueError, match="new revision_id"):
        fork_reference_study_revision(
            revision,
            revision_id=revision.revision_id,
            intent=revision.intent,
        )
    with pytest.raises(TypeError, match="ReferenceStudyRevision"):
        diff_reference_study_revisions(cast(Any, object()), revision)
    with pytest.raises(TypeError, match="ReferenceStudyRevision"):
        run_reference_study_revision(cast(Any, object()))


def test_reference_study_format_constants_are_stable() -> None:
    assert REFERENCE_STUDY_FORMAT_ID == "evolution-experiment-workbench-reference-study"
    assert REFERENCE_STUDY_FORMAT_VERSION == 1
    assert REFERENCE_RECIPE_ID == "bounded-reference-ecology"
    assert REFERENCE_RECIPE_VERSION == 1
    assert MAX_SPEED_SLOT == "reference-ecology.founder-max-speed"
