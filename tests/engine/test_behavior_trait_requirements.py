"""Tests for trait requirements declared by shared behavior configuration."""

from __future__ import annotations

import pytest

from evo_engine.behavior import EnergyConservationBehavior
from evo_engine.configuration import SimulationSpec
from evo_engine.energetics import DevelopmentalEnergyThreshold
from evo_engine.engine import MaxSteps, SequentialStepCoordinator
from evo_engine.genetics import ENERGY_CONSERVATION_THRESHOLD
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture, make_integer_architecture


def _spec_with_behavior(*, architecture, behavior_selection_model) -> SimulationSpec:
    return SimulationSpec(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        step_coordinator=SequentialStepCoordinator(stages=()),
        stopping_condition=MaxSteps(max_steps=0),
        behavior_selection_model=behavior_selection_model,
    )


def test_configuration_rejects_missing_behavior_selection_trait() -> None:
    """Test behavior-model trait requirements are validated during preflight."""
    architecture = make_empty_architecture()
    spec = _spec_with_behavior(
        architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=DevelopmentalEnergyThreshold(
                trait_name=ENERGY_CONSERVATION_THRESHOLD,
            )
        ),
    )

    with pytest.raises(ValueError, match=ENERGY_CONSERVATION_THRESHOLD):
        spec.compile()


def test_configuration_accepts_satisfied_behavior_selection_trait() -> None:
    """Test preflight succeeds when the biological architecture defines traits."""
    architecture = make_integer_architecture(ENERGY_CONSERVATION_THRESHOLD)
    spec = _spec_with_behavior(
        architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=DevelopmentalEnergyThreshold(
                trait_name=ENERGY_CONSERVATION_THRESHOLD,
            )
        ),
    )

    compiled = spec.compile()

    assert compiled.simulation.state.step_index == 0
