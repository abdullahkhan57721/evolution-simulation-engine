"""Tests for movement-intent models."""

from __future__ import annotations

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    MovementIntentModel,
    FixedMovementIntent,
    determine_movement_purpose,
)
from tests.helpers import add_organism, make_state


def test_fixed_movement_intent_defaults_to_exploration() -> None:
    """Test undirected movement defaults to exploratory purpose."""
    state = make_state()
    organism = add_organism(state)
    model = FixedMovementIntent()

    assert model.determine_purpose(
        organism,
        simulation_state=state,
    ) == EXPLORATION


def test_fixed_movement_intent_supports_other_purposes() -> None:
    """Test fixed intent may represent another behavioral purpose."""
    state = make_state()
    organism = add_organism(state)
    model = FixedMovementIntent(
        behavioral_purpose=ENERGY_ACQUISITION,
    )

    assert determine_movement_purpose(
        model,
        organism,
        simulation_state=state,
    ) == ENERGY_ACQUISITION


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
