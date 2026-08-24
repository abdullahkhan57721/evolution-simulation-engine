"""Tests for configuring behavior selection on simulation state."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.behavior import (
    BehaviorSelectionModel,
    EnergyConservationBehavior,
    UnrestrictedBehavior,
)
from evo_engine.engine import Simulation
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture


def test_simulation_defaults_to_unrestricted_behavior() -> None:
    """Test existing simulations retain unrestricted behavioral semantics."""
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
    )

    assert isinstance(
        simulation.state.behavior_selection_model,
        UnrestrictedBehavior,
    )


def test_simulation_uses_configured_behavior_selection_model() -> None:
    """Test simulations retain the explicitly configured selector."""
    model = EnergyConservationBehavior(
        energy_threshold=10,
    )
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
        behavior_selection_model=model,
    )

    assert simulation.state.behavior_selection_model is model


def test_transactional_state_copy_shares_behavior_selection_configuration() -> None:
    """Test state copies share pure behavior-selection configuration."""
    model = EnergyConservationBehavior(
        energy_threshold=10,
    )
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
        behavior_selection_model=model,
    )

    copied = simulation.state.copy()

    assert copied.behavior_selection_model is model


def test_simulation_rejects_invalid_behavior_selection_model() -> None:
    """Test simulation configuration requires the structural selector contract."""
    with pytest.raises(TypeError, match="BehaviorSelectionModel"):
        Simulation(
            initial_world_state=WorldState(width=3, height=3),
            genetic_architecture=make_empty_architecture(),
            behavior_selection_model=cast(BehaviorSelectionModel, object()),
        )
