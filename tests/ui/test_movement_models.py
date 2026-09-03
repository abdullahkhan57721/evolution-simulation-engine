"""Tests for adaptive exploration-movement configuration normalization."""

from __future__ import annotations

import pytest

from evo_engine.presets import (
    ReferenceGaussianMovement,
    ReferenceMooreMovement,
    ReferenceUniformMovement,
    ReferenceVonNeumannMovement,
)
from evo_engine.ui.models import build_curated_config, run_dashboard_reference


@pytest.mark.parametrize(
    ("kind", "expected_type"),
    (
        ("moore", ReferenceMooreMovement),
        ("von_neumann", ReferenceVonNeumannMovement),
        ("uniform", ReferenceUniformMovement),
    ),
)
def test_non_gaussian_movement_ignores_stale_gaussian_state(
    kind: str,
    expected_type: type[object],
) -> None:
    """Test an inactive Gaussian value cannot enter another typed variant."""
    config = build_curated_config(
        exploration_movement_kind=kind,
        gaussian_standard_deviation=-999,
    )

    assert isinstance(config.exploration_movement, expected_type)
    assert not hasattr(config.exploration_movement, "standard_deviation")


def test_gaussian_movement_preserves_active_standard_deviation() -> None:
    """Test active Gaussian controls normalize into the typed preset variant."""
    config = build_curated_config(
        exploration_movement_kind="gaussian",
        gaussian_standard_deviation=7,
    )

    assert config.exploration_movement == ReferenceGaussianMovement(
        standard_deviation=7
    )


def test_gaussian_movement_requires_valid_active_standard_deviation() -> None:
    """Test only the active Gaussian branch validates its dependent value."""
    with pytest.raises(ValueError, match="gaussian_standard_deviation"):
        build_curated_config(
            exploration_movement_kind="gaussian",
            gaussian_standard_deviation=-1,
        )


def test_unknown_movement_kind_has_understandable_normalization_error() -> None:
    """Test arbitrary UI strings cannot become preset/domain configuration."""
    with pytest.raises(ValueError, match="exploration_movement_kind"):
        build_curated_config(exploration_movement_kind="teleport")


def test_equal_movement_inputs_construct_equal_typed_config() -> None:
    """Test movement normalization is deterministic before simulation execution."""
    first = build_curated_config(
        seed=19,
        exploration_movement_kind="gaussian",
        gaussian_standard_deviation=2,
    )
    second = build_curated_config(
        seed=19,
        exploration_movement_kind="gaussian",
        gaussian_standard_deviation=2,
    )

    assert first == second


@pytest.mark.parametrize(
    ("kind", "gaussian_standard_deviation"),
    (
        ("moore", None),
        ("von_neumann", None),
        ("uniform", None),
        ("gaussian", 2),
    ),
)
def test_dashboard_runs_small_reference_with_each_movement_choice(
    kind: str,
    gaussian_standard_deviation: int | None,
) -> None:
    """Test every UI movement choice reaches a real committed simulation run."""
    config = build_curated_config(
        seed=23,
        max_steps=1,
        initial_population=4,
        width=4,
        height=4,
        exploration_movement_kind=kind,
        gaussian_standard_deviation=gaussian_standard_deviation,
    )

    run = run_dashboard_reference(config)

    assert run.completed_steps == 1
    assert run.config is config
