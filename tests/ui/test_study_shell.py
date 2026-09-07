"""Tests for WU1 concrete Workbench routing and persistence."""

from __future__ import annotations

import json

import pytest

import evo_engine.workbench.study as persisted_study
from evo_engine.workbench import (
    B3_STUDY_FORMAT_ID,
    B3_VALIDATED_SCENARIO_ID,
    EXPERIMENT_DEFINITION_FORMAT_ID,
    IncompatibleManifestError,
    STUDY_FORMAT_ID,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
    fork_b3_study_revision,
)
from evo_engine.ui.study_shell import (
    UnsupportedStudyArtifactError,
    artifact_kind,
    artifact_readiness,
    artifact_revision_id,
    artifact_run_count,
    artifact_type_label,
    load_concrete_artifact,
    new_b3_flagship,
    new_controlled_run,
    new_environment_selection_comparison,
    new_max_speed_sweep,
    new_reference_ecology,
    serialize_concrete_artifact,
)


def _supported_artifacts() -> tuple[object, ...]:
    return (
        new_controlled_run(revision_id="controlled-test"),
        new_b3_flagship(revision_id="b3-test"),
        new_reference_ecology(revision_id="reference-test"),
        new_max_speed_sweep(),
        new_environment_selection_comparison(),
    )


def test_supported_concrete_artifacts_round_trip_through_exact_loaders() -> None:
    for artifact in _supported_artifacts():
        encoded = serialize_concrete_artifact(artifact)  # type: ignore[arg-type]
        loaded = load_concrete_artifact(encoded)

        assert type(loaded) is type(artifact)
        assert loaded == artifact
        assert serialize_concrete_artifact(loaded) == encoded


def test_load_dispatch_classifies_all_supported_artifact_families() -> None:
    artifacts = _supported_artifacts()

    assert isinstance(artifacts[0], StudyRevision)
    assert isinstance(artifacts[1], B3StudyRevision)
    assert isinstance(artifacts[2], ReferenceStudyRevision)
    assert isinstance(artifacts[3], MaxSpeedSweepDefinition)
    assert isinstance(artifacts[4], EnvironmentSelectionComparisonDefinition)
    assert tuple(artifact_kind(item) for item in artifacts) == (
        "controlled-run",
        "b3-flagship",
        "reference-ecology",
        "max-speed-sweep",
        "environment-selection-comparison",
    )


def test_loading_controlled_revision_never_re_resolves_current_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision = new_controlled_run(revision_id="exact-controlled")
    encoded = revision.to_json()

    def fail_if_resolved(*args: object, **kwargs: object) -> object:
        raise AssertionError("UI load must not re-resolve stored intent")

    monkeypatch.setattr(
        persisted_study,
        "resolve_controlled_locomotion",
        fail_if_resolved,
    )

    loaded = load_concrete_artifact(encoded)

    assert isinstance(loaded, StudyRevision)
    assert loaded.to_json() == encoded
    assert loaded.manifest.to_json() == revision.manifest.to_json()


def test_invalid_and_unknown_formats_are_rejected() -> None:
    with pytest.raises(UnsupportedStudyArtifactError, match="valid JSON"):
        load_concrete_artifact("not-json")

    with pytest.raises(UnsupportedStudyArtifactError, match="encode an object"):
        load_concrete_artifact("[]")

    with pytest.raises(UnsupportedStudyArtifactError, match="format identity"):
        load_concrete_artifact(json.dumps({"format_id": "future-study"}))


def test_unknown_experiment_pattern_is_rejected_without_fallback() -> None:
    encoded = json.dumps(
        {
            "format_id": EXPERIMENT_DEFINITION_FORMAT_ID,
            "format_version": 1,
            "pattern_id": "future-pattern",
        }
    )

    with pytest.raises(UnsupportedStudyArtifactError, match="pattern identity"):
        load_concrete_artifact(encoded)


def test_forward_study_format_version_is_rejected_by_concrete_loader() -> None:
    revision = new_controlled_run(revision_id="future-version")
    decoded = json.loads(revision.to_json())
    assert decoded["format_id"] == STUDY_FORMAT_ID
    decoded["format_version"] = 999

    with pytest.raises(ValueError, match="format version"):
        load_concrete_artifact(json.dumps(decoded))


def test_incompatible_manifest_error_propagates_for_truthful_exact_reproduction() -> None:
    revision = new_controlled_run(revision_id="incompatible-manifest")
    decoded = json.loads(revision.to_json())
    manifest = json.loads(decoded["manifest_json"])
    manifest["recipe_version"] = 999
    decoded["manifest_json"] = json.dumps(manifest)

    with pytest.raises(IncompatibleManifestError):
        load_concrete_artifact(json.dumps(decoded))


def test_new_b3_entry_is_canonical_radius_one_only() -> None:
    revision = new_b3_flagship(revision_id="canonical-b3")

    assert revision.scenario_identity == B3_VALIDATED_SCENARIO_ID
    assert artifact_kind(revision) == "b3-flagship"
    assert artifact_type_label(revision) == "Curated B3 study revision"


def test_saved_b3_sensitivity_fork_can_open_without_becoming_new_study_choice() -> None:
    canonical = new_b3_flagship(revision_id="canonical-b3")
    sensitivity = fork_b3_study_revision(
        canonical,
        revision_id="radius-two-b3",
    )
    assert sensitivity.scenario_identity is None
    assert json.loads(sensitivity.to_json())["format_id"] == B3_STUDY_FORMAT_ID

    loaded = load_concrete_artifact(sensitivity.to_json())

    assert isinstance(loaded, B3StudyRevision)
    assert artifact_type_label(loaded) == "B3-derived custom study revision"
    assert loaded.parent_revision_id == canonical.revision_id


def test_revision_and_readiness_metadata_are_exposed_only_where_authoritative() -> None:
    controlled = new_controlled_run(revision_id="controlled-ready")
    sweep = new_max_speed_sweep()

    assert artifact_revision_id(controlled) == "controlled-ready"
    assert artifact_run_count(controlled) == 0
    assert artifact_readiness(controlled) is not None
    assert artifact_readiness(controlled).state == "ready"  # type: ignore[union-attr]

    assert artifact_revision_id(sweep) is None
    assert artifact_run_count(sweep) is None
    assert artifact_readiness(sweep) is None
