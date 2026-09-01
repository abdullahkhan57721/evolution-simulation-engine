"""Tests for exact reference-ecology checkpoint persistence and resume."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from evo_engine.engine import MaxSteps
from evo_engine.experiments import (
    load_reference_checkpoint,
    read_reference_checkpoint_manifest,
    resume_reference_checkpoint,
    write_reference_checkpoint,
)
from evo_engine.presets import (
    ReferenceEcology,
    ReferenceEcologyConfig,
    build_reference_ecology,
)


def _config() -> ReferenceEcologyConfig:
    return ReferenceEcologyConfig(
        width=4,
        height=4,
        initial_population=4,
        max_steps=4,
        seed=31,
    )


def _partially_run_ecology() -> ReferenceEcology:
    ecology = build_reference_ecology(_config())
    ecology.engine.stopping_condition = MaxSteps(max_steps=2)
    ecology.engine.run(ecology.simulation)
    ecology.engine.stopping_condition = MaxSteps(max_steps=ecology.config.max_steps)
    return ecology


def _assert_equivalent_ecologies(
    actual: ReferenceEcology,
    expected: ReferenceEcology,
) -> None:
    assert actual.config == expected.config
    assert actual.simulation.state.step_index == expected.simulation.state.step_index
    assert (
        actual.simulation.state.domain_state == expected.simulation.state.domain_state
    )
    assert (
        actual.simulation.state.last_step_telemetry
        == expected.simulation.state.last_step_telemetry
    )
    assert (
        actual.simulation.state.rng.getstate()
        == expected.simulation.state.rng.getstate()
    )
    assert actual.recorder.observations == expected.recorder.observations
    assert (
        actual.genetic_recorder.observations == expected.genetic_recorder.observations
    )
    assert actual.event_recorder.steps == expected.event_recorder.steps
    assert actual.pedigree_recorder.records == expected.pedigree_recorder.records


def test_checkpoint_restores_exact_reference_ecology_and_rng(tmp_path: Path) -> None:
    """Test checkpoint load preserves state, history, identity wiring, and RNG."""
    ecology = _partially_run_ecology()

    checkpoint_path = write_reference_checkpoint(ecology, tmp_path / "run.evochk")
    restored = load_reference_checkpoint(checkpoint_path)

    _assert_equivalent_ecologies(restored, ecology)
    assert restored.recorder in restored.engine.observers
    assert restored.genetic_recorder in restored.engine.observers
    assert restored.pedigree_recorder in restored.engine.observers
    assert restored.event_recorder in restored.engine.telemetry_observers
    assert restored.pedigree_recorder in restored.engine.telemetry_observers


def test_resume_checkpoint_matches_uninterrupted_run(tmp_path: Path) -> None:
    """Test save/load continuation is identical to an uninterrupted simulation."""
    uninterrupted = build_reference_ecology(_config())
    uninterrupted.engine.run(uninterrupted.simulation)

    interrupted = _partially_run_ecology()
    checkpoint_path = write_reference_checkpoint(
        interrupted,
        tmp_path / "interrupted.evochk",
    )
    resumed = resume_reference_checkpoint(checkpoint_path)

    _assert_equivalent_ecologies(resumed, uninterrupted)


def test_checkpoint_manifest_is_self_describing(tmp_path: Path) -> None:
    """Test manifest exposes reproducibility and exact-state metadata."""
    ecology = _partially_run_ecology()
    checkpoint_path = write_reference_checkpoint(ecology, tmp_path / "run.evochk")

    manifest = read_reference_checkpoint_manifest(checkpoint_path)

    assert manifest.format_version == 1
    assert manifest.step_index == 2
    assert json.loads(manifest.config_json)["seed"] == ecology.config.seed
    assert len(manifest.payload_sha256) == 64
    assert len(manifest.rng_state_sha256) == 64


def test_checkpoint_load_rejects_corrupted_payload(tmp_path: Path) -> None:
    """Test payload integrity is verified before unpickling."""
    ecology = _partially_run_ecology()
    checkpoint_path = write_reference_checkpoint(ecology, tmp_path / "run.evochk")

    with ZipFile(checkpoint_path, "r") as archive:
        manifest_bytes = archive.read("manifest.json")
        payload = archive.read("reference_ecology.pkl")

    with ZipFile(checkpoint_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        archive.writestr("reference_ecology.pkl", payload + b"corruption")

    with pytest.raises(ValueError, match="SHA-256 digest"):
        load_reference_checkpoint(checkpoint_path)


def test_checkpoint_read_rejects_non_archive(tmp_path: Path) -> None:
    """Test invalid checkpoint containers fail with a domain-level error."""
    checkpoint_path = tmp_path / "invalid.evochk"
    checkpoint_path.write_text("not a checkpoint", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid reference checkpoint archive"):
        read_reference_checkpoint_manifest(checkpoint_path)
