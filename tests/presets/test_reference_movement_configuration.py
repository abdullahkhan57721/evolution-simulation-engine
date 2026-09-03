"""Tests for typed exploration movement in the reference ecology preset."""

from __future__ import annotations

import pytest

from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceExplorationMovement,
    ReferenceGaussianMovement,
    ReferenceMooreMovement,
    ReferenceUniformMovement,
    ReferenceVonNeumannMovement,
    build_reference_ecology,
    build_reference_engine,
)
from evo_engine.processes import Movement
from evo_engine.spatial.movement_patterns import (
    GaussianRandom,
    MooreRandom,
    UniformRandom,
    VonNeumannRandom,
)


def _movement_process(config: ReferenceEcologyConfig) -> Movement:
    engine = build_reference_engine(config)
    for stage in engine.step_coordinator.stages:
        for process in stage.processes:
            if isinstance(process, Movement):
                return process
    raise AssertionError("Reference lifecycle did not contain Movement.")


def test_reference_movement_defaults_to_moore_random() -> None:
    """Test the new config boundary preserves the existing reference default."""
    config = ReferenceEcologyConfig()

    assert isinstance(config.exploration_movement, ReferenceMooreMovement)
    assert isinstance(_movement_process(config).movement_pattern, MooreRandom)


@pytest.mark.parametrize(
    ("movement_config", "expected_pattern_type"),
    (
        (ReferenceMooreMovement(), MooreRandom),
        (ReferenceVonNeumannMovement(), VonNeumannRandom),
        (ReferenceUniformMovement(), UniformRandom),
        (ReferenceGaussianMovement(standard_deviation=3), GaussianRandom),
    ),
)
def test_reference_movement_variants_build_existing_spatial_strategies(
    movement_config: ReferenceExplorationMovement,
    expected_pattern_type: type[object],
) -> None:
    """Test preset data variants map only to existing spatial strategies."""
    process = _movement_process(
        ReferenceEcologyConfig(exploration_movement=movement_config)
    )

    assert isinstance(process.movement_pattern, expected_pattern_type)
    if isinstance(movement_config, ReferenceGaussianMovement):
        assert isinstance(process.movement_pattern, GaussianRandom)
        assert (
            process.movement_pattern.standard_deviation
            == movement_config.standard_deviation
        )


def test_reference_gaussian_movement_rejects_negative_standard_deviation() -> None:
    """Test Gaussian variant validation mirrors the existing spatial contract."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        ReferenceGaussianMovement(standard_deviation=-1)


def test_reference_config_rejects_unsupported_movement_data() -> None:
    """Test runtime strategy objects cannot bypass the typed preset boundary."""
    with pytest.raises(TypeError, match="exploration_movement"):
        ReferenceEcologyConfig(
            exploration_movement=MooreRandom(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "movement_config",
    (
        ReferenceMooreMovement(),
        ReferenceVonNeumannMovement(),
        ReferenceUniformMovement(),
        ReferenceGaussianMovement(standard_deviation=2),
    ),
)
def test_reference_ecology_runs_with_every_exposed_movement_variant(
    movement_config: ReferenceExplorationMovement,
) -> None:
    """Test every exposed movement variant compiles and executes deterministically."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            width=4,
            height=4,
            initial_population=4,
            max_steps=1,
            seed=17,
            exploration_movement=movement_config,
        )
    )

    ecology.engine.run(ecology.simulation)

    assert ecology.simulation.state.step_index == 1
