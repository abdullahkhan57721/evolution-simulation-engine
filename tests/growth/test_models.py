"""Tests for organism growth models."""

from __future__ import annotations

import pytest

from evo_engine.growth import FixedGrowthRate
from tests.helpers import add_organism, make_state


def test_fixed_growth_rate_returns_configured_amount() -> None:
    """Test fixed potential growth is independent of current target distance."""
    state = make_state()
    organism = add_organism(state)

    gain = FixedGrowthRate(
        amount_per_timestep=4,
    ).determine_body_mass_gain(
        organism,
        target_body_mass=10,
        simulation_state=state,
    )

    assert gain == 4


@pytest.mark.parametrize(
    "value",
    [
        -1,
        1.5,
        True,
        "1",
        None,
    ],
)
def test_fixed_growth_rate_rejects_invalid_amount(value: object) -> None:
    """Test fixed growth-rate configuration requires a nonnegative integer."""
    with pytest.raises((TypeError, ValueError)):
        FixedGrowthRate(
            amount_per_timestep=value,  # type: ignore[arg-type]
        )
