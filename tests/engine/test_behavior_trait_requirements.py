"""Tests for trait requirements declared by shared behavior configuration."""

from __future__ import annotations

import pytest

from evo_engine.behavior import EnergyConservationBehavior
from evo_engine.energetics import DevelopmentalEnergyThreshold
from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
)
from evo_engine.genetics import ENERGY_CONSERVATION_THRESHOLD
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture, make_integer_architecture


def _engine_that_runs_zero_steps() -> SimulationEngine:
    return SimulationEngine(
        step_coordinator=SequentialStepCoordinator(stages=()),
        stopping_condition=MaxSteps(max_steps=0),
    )


def test_engine_rejects_missing_behavior_selection_trait_before_step_zero() -> None:
    """Test shared behavior-model trait requirements are validated preflight."""
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=DevelopmentalEnergyThreshold(
                trait_name=ENERGY_CONSERVATION_THRESHOLD,
            )
        ),
    )

    with pytest.raises(ValueError, match=ENERGY_CONSERVATION_THRESHOLD):
        _engine_that_runs_zero_steps().run(simulation)

    assert simulation.state.step_index == 0


def test_engine_accepts_satisfied_behavior_selection_trait_requirement() -> None:
    """Test behavior-model preflight succeeds when architecture defines traits."""
    architecture = make_integer_architecture(ENERGY_CONSERVATION_THRESHOLD)
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=DevelopmentalEnergyThreshold(
                trait_name=ENERGY_CONSERVATION_THRESHOLD,
            )
        ),
    )

    _engine_that_runs_zero_steps().run(simulation)

    assert simulation.state.step_index == 0
