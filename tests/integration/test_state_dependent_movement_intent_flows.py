"""Integration tests for state-dependent movement intent."""

from __future__ import annotations

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    EnergyConservationBehavior,
    EnergyThresholdMovementIntent,
    NearestResourceTarget,
)
from evo_engine.energetics import FixedLocomotionCost
from evo_engine.engine import Simulation
from evo_engine.genetics.builtin_traits import MAX_SPEED, SENSORY_RANGE
from evo_engine.processes import Movement
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.world import WorldState
from tests.helpers import add_organism, make_integer_architecture


def test_movement_switches_between_foraging_and_exploration_with_energy() -> None:
    """Test one movement process derives different intent from current energy."""

    class ExploratoryPattern:
        def choose_displacement(self, *, rng, max_speed):
            return (0, 1)

    architecture = make_integer_architecture(MAX_SPEED, SENSORY_RANGE)
    simulation = Simulation(
        initial_world_state=WorldState(width=8, height=4),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    organism = add_organism(
        simulation.state,
        trait_values={
            MAX_SPEED: 1,
            SENSORY_RANGE: 4,
        },
        energy=5,
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(x=4, y=1, amount=5)
    process = Movement(
        movement_pattern=ExploratoryPattern(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_intent_model=EnergyThresholdMovementIntent(
            energy_threshold=10,
        ),
        movement_target_model=NearestResourceTarget(),
    )

    low_energy_event = process.propose_events(simulation.state)[0]

    assert low_energy_event.behavioral_purpose == ENERGY_ACQUISITION
    assert (low_energy_event.target_x, low_energy_event.target_y) == (4, 1)
    assert (low_energy_event.dx, low_energy_event.dy) == (1, 0)

    organism.energy = 10

    sufficient_energy_event = process.propose_events(simulation.state)[0]

    assert sufficient_energy_event.behavioral_purpose == EXPLORATION
    assert sufficient_energy_event.target_x is None
    assert sufficient_energy_event.target_y is None
    assert (sufficient_energy_event.dx, sufficient_energy_event.dy) == (0, 1)
