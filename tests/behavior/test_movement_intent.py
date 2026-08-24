"""Tests for movement-intent models."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    REPRODUCTION,
    SURVIVAL,
    EnergyThresholdMovementIntent,
    FixedMovementIntent,
    MovementIntentModel,
    determine_movement_purpose,
)
from tests.helpers import add_organism, make_state


def test_fixed_movement_intent_defaults_to_exploration() -> None:
    """Test undirected movement defaults to exploratory purpose."""
    state = make_state()
    organism = add_organism(state)
    model = FixedMovementIntent()

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == EXPLORATION
    )


def test_fixed_movement_intent_supports_other_purposes() -> None:
    """Test fixed intent may represent another behavioral purpose."""
    state = make_state()
    organism = add_organism(state)
    model = FixedMovementIntent(
        behavioral_purpose=ENERGY_ACQUISITION,
    )

    assert (
        determine_movement_purpose(
            model,
            organism,
            simulation_state=state,
        )
        == ENERGY_ACQUISITION
    )


@pytest.mark.parametrize(
    "purpose",
    [
        "",
        " ",
        None,
        1,
    ],
)
def test_fixed_movement_intent_rejects_invalid_purpose(purpose: object) -> None:
    """Test fixed movement purposes must be nonblank strings."""
    with pytest.raises((TypeError, ValueError)):
        FixedMovementIntent(behavioral_purpose=purpose)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("energy", "expected_purpose"),
    [
        (0, ENERGY_ACQUISITION),
        (9, ENERGY_ACQUISITION),
        (10, EXPLORATION),
        (11, EXPLORATION),
    ],
)
def test_energy_threshold_movement_intent_uses_current_energy(
    energy: int,
    expected_purpose: str,
) -> None:
    """Test energy below the threshold switches movement to acquisition."""
    state = make_state()
    organism = add_organism(
        state,
        energy=energy,
    )
    model = EnergyThresholdMovementIntent(
        energy_threshold=10,
    )

    assert (
        determine_movement_purpose(
            model,
            organism,
            simulation_state=state,
        )
        == expected_purpose
    )


def test_energy_threshold_movement_intent_responds_to_energy_change() -> None:
    """Test movement intent is derived each time from mutable current energy."""
    state = make_state()
    organism = add_organism(
        state,
        energy=5,
    )
    model = EnergyThresholdMovementIntent(
        energy_threshold=10,
    )

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == ENERGY_ACQUISITION
    )

    organism.energy = 10

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == EXPLORATION
    )


def test_energy_threshold_movement_intent_supports_configurable_purposes() -> None:
    """Test threshold intent can switch between arbitrary valid purposes."""
    state = make_state()
    organism = add_organism(
        state,
        energy=2,
    )
    model = EnergyThresholdMovementIntent(
        energy_threshold=3,
        low_energy_purpose=SURVIVAL,
        otherwise_purpose=REPRODUCTION,
    )

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == SURVIVAL
    )

    organism.energy = 3

    assert (
        model.determine_purpose(
            organism,
            simulation_state=state,
        )
        == REPRODUCTION
    )


@pytest.mark.parametrize(
    "energy_threshold",
    [
        -1,
        1.0,
        True,
    ],
)
def test_energy_threshold_movement_intent_rejects_invalid_threshold(
    energy_threshold: object,
) -> None:
    """Test movement-intent energy thresholds are nonnegative integers."""
    with pytest.raises((TypeError, ValueError)):
        EnergyThresholdMovementIntent(
            energy_threshold=cast(int, energy_threshold),
        )


@pytest.mark.parametrize(
    ("low_energy_purpose", "otherwise_purpose"),
    [
        ("", EXPLORATION),
        (" ", EXPLORATION),
        (cast(str, None), EXPLORATION),
        (cast(str, 1), EXPLORATION),
        (ENERGY_ACQUISITION, ""),
        (ENERGY_ACQUISITION, " "),
        (ENERGY_ACQUISITION, cast(str, None)),
        (ENERGY_ACQUISITION, cast(str, 1)),
    ],
)
def test_energy_threshold_movement_intent_rejects_invalid_purposes(
    low_energy_purpose: str,
    otherwise_purpose: str,
) -> None:
    """Test both threshold-selected purposes must be nonblank strings."""
    with pytest.raises((TypeError, ValueError)):
        EnergyThresholdMovementIntent(
            energy_threshold=10,
            low_energy_purpose=low_energy_purpose,
            otherwise_purpose=otherwise_purpose,
        )


def test_movement_intent_protocol_accepts_structural_implementation() -> None:
    """Test custom intent models need not inherit from engine classes."""

    class CustomIntent:
        def determine_purpose(
            self,
            organism,
            *,
            simulation_state,
        ) -> str:
            return ENERGY_ACQUISITION

    assert isinstance(CustomIntent(), MovementIntentModel)


def test_determine_movement_purpose_validates_custom_model_output() -> None:
    """Test the movement boundary validates custom intent return values."""

    class InvalidIntent:
        def determine_purpose(
            self,
            organism,
            *,
            simulation_state,
        ):
            return 1

    state = make_state()
    organism = add_organism(state)

    with pytest.raises(TypeError):
        determine_movement_purpose(
            InvalidIntent(),  # type: ignore[arg-type]
            organism,
            simulation_state=state,
        )
