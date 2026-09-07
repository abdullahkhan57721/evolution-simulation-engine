"""Adversarial validation coverage for WB1 persisted study contracts."""

from __future__ import annotations

import json

import attrs
import pytest

import evo_engine.workbench.controlled_locomotion as locomotion_module
from evo_engine.workbench import (
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT,
    ControlledLocomotionIntent,
    ControlledLocomotionManifest,
    EvidencePlan,
    IncompatibleManifestError,
    StudyRevision,
    WorkbenchRunProvenance,
    assess_readiness,
    compile_controlled_locomotion,
    create_study_revision,
    diff_study_revisions,
    fork_study_revision,
    resolve_controlled_locomotion,
    run_study_revision,
    semantic_diff,
)


def _manifest() -> ControlledLocomotionManifest:
    return resolve_controlled_locomotion(
        ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=17,
        )
    )


def _revision() -> StudyRevision:
    return create_study_revision(
        revision_id="study-r1",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=17,
        ),
    )


def _provenance(revision: StudyRevision) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id="run-1",
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=("run-1:evidence",),
        result_references=("run-1:result",),
    )


def test_evidence_plan_rejects_blank_or_non_string_entries() -> None:
    with pytest.raises(TypeError, match=r"requested\[0\]"):
        EvidencePlan(requested=("",))
    with pytest.raises(TypeError, match=r"requested\[0\]"):
        EvidencePlan(requested=(1,))  # type: ignore[arg-type]


def test_readiness_and_compile_reject_wrong_public_argument_types() -> None:
    with pytest.raises(TypeError, match="intent"):
        assess_readiness(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="evidence_plan"):
        assess_readiness(ControlledLocomotionIntent(), object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="manifest"):
        compile_controlled_locomotion(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="evidence_plan"):
        compile_controlled_locomotion(_manifest(), object())  # type: ignore[arg-type]


def test_manifest_rejects_identity_version_and_explicit_slot_corruption() -> None:
    manifest = _manifest()
    with pytest.raises(IncompatibleManifestError, match="identity"):
        attrs.evolve(manifest, recipe_version=2)
    with pytest.raises(TypeError, match="engine_version"):
        attrs.evolve(manifest, engine_version="")
    with pytest.raises(ValueError, match="stable order"):
        attrs.evolve(
            manifest, explicit_values=tuple(reversed(manifest.explicit_values))
        )


def test_manifest_value_pairs_reject_invalid_container_items_keys_values_and_duplicates() -> (
    None
):
    manifest = _manifest()
    with pytest.raises(TypeError, match="must be a tuple"):
        attrs.evolve(manifest, derived_values=[])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="two-item tuple"):
        attrs.evolve(manifest, derived_values=(("only-one",),))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="non-empty string"):
        attrs.evolve(manifest, derived_values=(("", 1),))
    with pytest.raises(ValueError, match="duplicate semantic IDs"):
        attrs.evolve(manifest, derived_values=(("same", 1), ("same", 2)))
    with pytest.raises(TypeError, match="manifest scalar"):
        attrs.evolve(manifest, derived_values=(("float", 1.5),))  # type: ignore[arg-type]


def test_manifest_unknown_semantic_value_raises_key_error() -> None:
    manifest = _manifest()
    with pytest.raises(KeyError, match="unknown"):
        manifest.explicit_value("unknown")
    with pytest.raises(KeyError, match="unknown"):
        manifest.derived_value("unknown")


def test_manifest_loader_rejects_non_string_non_object_and_bad_required_fields() -> (
    None
):
    manifest = _manifest()
    with pytest.raises(TypeError, match="string"):
        ControlledLocomotionManifest.from_json(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="object"):
        ControlledLocomotionManifest.from_json("[]")

    payload = json.loads(manifest.to_json())
    payload["recipe_id"] = None
    with pytest.raises(TypeError, match="recipe_id"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))

    payload = json.loads(manifest.to_json())
    payload["recipe_version"] = "1"
    with pytest.raises(TypeError, match="recipe_version"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))


def test_manifest_loader_rejects_bad_json_pair_shapes() -> None:
    manifest = _manifest()

    payload = json.loads(manifest.to_json())
    payload["derived_values"] = "bad"
    with pytest.raises(TypeError, match="JSON array"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))

    payload = json.loads(manifest.to_json())
    payload["derived_values"] = [["only-one"]]
    with pytest.raises(TypeError, match="two-item JSON array"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))

    payload = json.loads(manifest.to_json())
    payload["derived_values"] = [[1, 2]]
    with pytest.raises(TypeError, match="must be a string"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))

    payload = json.loads(manifest.to_json())
    payload["derived_values"] = [["float", 1.5]]
    with pytest.raises(TypeError, match="manifest scalar"):
        ControlledLocomotionManifest.from_json(json.dumps(payload))


def test_compile_rejects_persisted_values_outside_recipe_contract() -> None:
    manifest = _manifest()
    explicit = dict(manifest.explicit_values)

    out_of_range = attrs.evolve(
        manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, 0),
            (RESOURCE_GEOGRAPHY_SLOT, explicit[RESOURCE_GEOGRAPHY_SLOT]),
            (SEED_SLOT, explicit[SEED_SLOT]),
        ),
    )
    with pytest.raises(IncompatibleManifestError, match="outside WB1 support"):
        compile_controlled_locomotion(out_of_range)

    wrong_speed_type = attrs.evolve(
        manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, True),
            (RESOURCE_GEOGRAPHY_SLOT, explicit[RESOURCE_GEOGRAPHY_SLOT]),
            (SEED_SLOT, explicit[SEED_SLOT]),
        ),
    )
    with pytest.raises(IncompatibleManifestError, match="must remain an integer"):
        compile_controlled_locomotion(wrong_speed_type)

    wrong_geography = attrs.evolve(
        manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, explicit[MAX_SPEED_SLOT]),
            (RESOURCE_GEOGRAPHY_SLOT, "unsupported"),
            (SEED_SLOT, explicit[SEED_SLOT]),
        ),
    )
    with pytest.raises(IncompatibleManifestError, match="resource geography"):
        compile_controlled_locomotion(wrong_geography)

    wrong_seed_type = attrs.evolve(
        manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, explicit[MAX_SPEED_SLOT]),
            (RESOURCE_GEOGRAPHY_SLOT, explicit[RESOURCE_GEOGRAPHY_SLOT]),
            (SEED_SLOT, "17"),
        ),
    )
    with pytest.raises(IncompatibleManifestError, match="must remain an integer"):
        compile_controlled_locomotion(wrong_seed_type)


def test_semantic_diff_rejects_wrong_types_and_mismatched_derived_ids() -> None:
    manifest = _manifest()
    with pytest.raises(TypeError, match="before and after"):
        semantic_diff(object(), manifest)  # type: ignore[arg-type]

    mismatched = attrs.evolve(manifest, derived_values=(("different-id", 1),))
    with pytest.raises(ValueError, match="matching recipe-scoped value IDs"):
        semantic_diff(manifest, mismatched)


def test_source_tree_engine_version_fallback_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_distribution(_: str) -> str:
        raise locomotion_module.metadata.PackageNotFoundError

    monkeypatch.setattr(locomotion_module.metadata, "version", missing_distribution)
    manifest = resolve_controlled_locomotion(
        ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=17,
        )
    )
    assert manifest.engine_version == "source-tree-uninstalled"


def test_run_provenance_validates_required_strings_and_string_tuples() -> None:
    revision = _revision()
    kwargs = {
        "run_id": "run-1",
        "study_revision_id": revision.revision_id,
        "manifest_digest": revision.manifest.digest,
        "evidence_ids": revision.evidence_plan.requested,
        "evidence_references": (),
        "result_references": (),
    }
    for field in ("run_id", "study_revision_id", "manifest_digest"):
        bad = dict(kwargs)
        bad[field] = " "
        with pytest.raises(TypeError, match=field):
            WorkbenchRunProvenance(**bad)  # type: ignore[arg-type]

    bad_tuple = dict(kwargs)
    bad_tuple["evidence_ids"] = [EVENT_EVIDENCE_ID]
    with pytest.raises(TypeError, match="evidence_ids"):
        WorkbenchRunProvenance(**bad_tuple)  # type: ignore[arg-type]

    bad_entry = dict(kwargs)
    bad_entry["evidence_references"] = ("",)
    with pytest.raises(TypeError, match="evidence_references"):
        WorkbenchRunProvenance(**bad_entry)  # type: ignore[arg-type]


def test_study_revision_rejects_wrong_core_types_parent_and_runs() -> None:
    revision = _revision()
    with pytest.raises(TypeError, match="revision_id"):
        attrs.evolve(revision, revision_id=" ")
    with pytest.raises(TypeError, match="intent"):
        attrs.evolve(revision, intent=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="manifest"):
        attrs.evolve(revision, manifest=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="evidence_plan"):
        attrs.evolve(revision, evidence_plan=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="parent_revision_id"):
        attrs.evolve(revision, parent_revision_id=" ")
    with pytest.raises(ValueError, match="must differ"):
        attrs.evolve(revision, parent_revision_id=revision.revision_id)
    with pytest.raises(TypeError, match="runs must be a tuple"):
        attrs.evolve(revision, runs=[])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"runs\[0\]"):
        attrs.evolve(revision, runs=(object(),))  # type: ignore[arg-type]


def test_persisted_run_mismatch_rejected_for_revision_manifest_and_evidence() -> None:
    revision = _revision()
    provenance = _provenance(revision)
    with pytest.raises(ValueError, match="this study revision"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, study_revision_id="other"),),
        )
    with pytest.raises(ValueError, match="exact manifest"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, manifest_digest="other"),),
        )
    with pytest.raises(ValueError, match="exact evidence plan"):
        attrs.evolve(
            revision,
            runs=(attrs.evolve(provenance, evidence_ids=(EVENT_EVIDENCE_ID,)),),
        )


def test_with_run_rejects_wrong_object_type() -> None:
    with pytest.raises(TypeError, match="provenance"):
        _revision().with_run(object())  # type: ignore[arg-type]


def test_study_loader_rejects_non_string_non_object_and_bad_format_id() -> None:
    revision = _revision()
    with pytest.raises(TypeError, match="string"):
        StudyRevision.from_json(1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="object"):
        StudyRevision.from_json("[]")

    payload = json.loads(revision.to_json())
    payload["format_id"] = "other"
    with pytest.raises(ValueError, match="format ID"):
        StudyRevision.from_json(json.dumps(payload))


def test_study_loader_rejects_bad_nested_containers() -> None:
    revision = _revision()
    for field in ("intent", "evidence_plan"):
        payload = json.loads(revision.to_json())
        payload[field] = []
        with pytest.raises(TypeError, match=field):
            StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["evidence_plan"]["requested"] = "bad"
    with pytest.raises(TypeError, match="evidence_plan.requested"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["runs"] = "bad"
    with pytest.raises(TypeError, match="runs"):
        StudyRevision.from_json(json.dumps(payload))


def test_study_loader_rejects_bad_optional_authoring_values() -> None:
    revision = _revision()

    payload = json.loads(revision.to_json())
    payload["parent_revision_id"] = 1
    with pytest.raises(TypeError, match="parent_revision_id"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["intent"]["max_speed"] = "3"
    with pytest.raises(TypeError, match="max_speed"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["intent"]["resource_geography"] = 3
    with pytest.raises(TypeError, match="resource_geography"):
        StudyRevision.from_json(json.dumps(payload))


def test_study_loader_rejects_bad_run_shapes_lists_and_string_entries() -> None:
    revision = _revision().with_run(_provenance(_revision()))

    payload = json.loads(revision.to_json())
    payload["runs"] = ["bad"]
    with pytest.raises(TypeError, match=r"runs\[0\]"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["runs"][0]["evidence_ids"] = "bad"
    with pytest.raises(TypeError, match="JSON array"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload["runs"][0]["evidence_ids"] = [1]
    with pytest.raises(TypeError, match="non-empty string"):
        StudyRevision.from_json(json.dumps(payload))


def test_study_operations_reject_wrong_types_and_blank_ids() -> None:
    intent = ControlledLocomotionIntent(
        max_speed=3,
        resource_geography="local_resource",
        seed=17,
    )
    with pytest.raises(TypeError, match="revision_id"):
        create_study_revision(revision_id=" ", intent=intent)
    with pytest.raises(TypeError, match="parent"):
        fork_study_revision(object(), revision_id="r2")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="revision_id"):
        fork_study_revision(_revision(), revision_id=" ")
    with pytest.raises(TypeError, match="before and after"):
        diff_study_revisions(object(), _revision())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="revision"):
        run_study_revision(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="run_id"):
        run_study_revision(_revision(), run_id=" ")


def test_run_without_explicit_id_generates_nonempty_provenance_id() -> None:
    result = run_study_revision(
        _revision(),
    )
    assert result.provenance.run_id


def test_study_alignment_rejects_geography_and_seed_mismatch() -> None:
    revision = _revision()
    geography_manifest = attrs.evolve(
        revision.manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, 3),
            (RESOURCE_GEOGRAPHY_SLOT, "separated_corridor"),
            (SEED_SLOT, 17),
        ),
    )
    with pytest.raises(ValueError, match="resource_geography"):
        attrs.evolve(revision, manifest=geography_manifest)

    seed_manifest = attrs.evolve(
        revision.manifest,
        explicit_values=(
            (MAX_SPEED_SLOT, 3),
            (RESOURCE_GEOGRAPHY_SLOT, "local_resource"),
            (SEED_SLOT, 18),
        ),
    )
    with pytest.raises(ValueError, match="seed"):
        attrs.evolve(revision, manifest=seed_manifest)


def test_study_loader_rejects_bad_manifest_json_and_missing_revision_id() -> None:
    revision = _revision()
    payload = json.loads(revision.to_json())
    payload["manifest_json"] = 1
    with pytest.raises(TypeError, match="manifest_json"):
        StudyRevision.from_json(json.dumps(payload))

    payload = json.loads(revision.to_json())
    payload.pop("revision_id")
    with pytest.raises(TypeError, match="revision_id"):
        StudyRevision.from_json(json.dumps(payload))


def test_population_and_event_evidence_ids_remain_distinct() -> None:
    assert POPULATION_EVIDENCE_ID != EVENT_EVIDENCE_ID
