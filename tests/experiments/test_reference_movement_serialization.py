"""Tests for canonical serialization of reference movement variants."""

from __future__ import annotations

import json

from evo_engine.experiments import run_reference_replicates
from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceGaussianMovement,
    ReferenceUniformMovement,
)


def test_gaussian_movement_serialization_is_self_describing() -> None:
    """Test canonical experiment config records variant identity and parameters."""
    result = run_reference_replicates(
        ReferenceEcologyConfig(
            width=4,
            height=4,
            initial_population=4,
            max_steps=1,
            exploration_movement=ReferenceGaussianMovement(
                standard_deviation=3,
            ),
        ),
        seeds=(17,),
    )

    serialized = json.loads(result.replicates[0].metadata.config_json)

    assert serialized["exploration_movement"] == {
        "kind": "gaussian",
        "standard_deviation": 3,
    }


def test_non_gaussian_serialization_has_no_gaussian_only_parameter() -> None:
    """Test inactive variant data is structurally absent from canonical config."""
    result = run_reference_replicates(
        ReferenceEcologyConfig(
            width=4,
            height=4,
            initial_population=4,
            max_steps=1,
            exploration_movement=ReferenceUniformMovement(),
        ),
        seeds=(19,),
    )

    serialized = json.loads(result.replicates[0].metadata.config_json)

    assert serialized["exploration_movement"] == {"kind": "uniform"}


def test_replicate_seed_replacement_preserves_movement_variant() -> None:
    """Test experiment seed evolution does not rewrite nested movement config."""
    result = run_reference_replicates(
        ReferenceEcologyConfig(
            width=4,
            height=4,
            initial_population=4,
            max_steps=1,
            seed=999,
            exploration_movement=ReferenceGaussianMovement(
                standard_deviation=4,
            ),
        ),
        seeds=(3, 7),
    )

    for seed in result.seeds:
        serialized = json.loads(result.replicate(seed).metadata.config_json)
        assert serialized["seed"] == seed
        assert serialized["exploration_movement"] == {
            "kind": "gaussian",
            "standard_deviation": 4,
        }
