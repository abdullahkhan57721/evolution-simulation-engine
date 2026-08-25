"""Tests for environmental forcing policies."""

from __future__ import annotations

import math

import pytest

from evo_engine.ecology import (
    LinearEnvironmentalForcing,
    ScheduledEnvironmentalForcing,
    SinusoidalEnvironmentalForcing,
)


def test_linear_environmental_forcing_uses_step_index() -> None:
    """Test linear forcing returns the configured temporal trajectory."""
    forcing = LinearEnvironmentalForcing(initial_value=10, change_per_step=2.5)

    assert forcing.value_at(0) == 10
    assert forcing.value_at(4) == 20


def test_sinusoidal_environmental_forcing_repeats_after_period() -> None:
    """Test seasonal forcing repeats exactly one period later."""
    forcing = SinusoidalEnvironmentalForcing(
        mean=20,
        amplitude=5,
        period_steps=4,
    )

    assert forcing.value_at(0) == pytest.approx(20)
    assert forcing.value_at(1) == pytest.approx(25)
    assert forcing.value_at(4) == pytest.approx(20)


def test_scheduled_environmental_forcing_changes_only_listed_steps() -> None:
    """Test scheduled forcing represents discrete disturbances or regimes."""
    forcing = ScheduledEnvironmentalForcing(
        schedule=((2, 30), (5, 12.5)),
    )

    assert forcing.value_at(1) is None
    assert forcing.value_at(2) == 30
    assert forcing.value_at(5) == 12.5


def test_forcing_rejects_invalid_parameters() -> None:
    """Test environmental forcing rejects ambiguous or non-finite inputs."""
    with pytest.raises(ValueError):
        SinusoidalEnvironmentalForcing(mean=20, amplitude=-1, period_steps=4)

    with pytest.raises(ValueError):
        LinearEnvironmentalForcing(initial_value=math.inf, change_per_step=1)

    with pytest.raises(ValueError, match="strictly increasing"):
        ScheduledEnvironmentalForcing(schedule=((2, 1), (2, 3)))
