"""Integration tests for movement intent and behavior selection."""

from __future__ import annotations

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    EnergyConservationBehavior,
    FixedMovementIntent,
)
from evo_engine.energetics import FixedLocomotionCost
from evo_engine.engine import Simulation
from evo_engine.processes import Movement
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import UniformRandom
from evo_engine.world import WorldState
from tests.helpers import add_organism, make_integer_architecture


def test_low_energy_exploratory_movement_is_suppressed_before_pattern() -> None:
    """Test conservation suppresses exploration before displacement work."""

    class PatternThatMustNotRun:
        def choose_displacement(self, *, rng, max_speed):
            raise AssertionError("suppressed movement must not sample displacement")

    architecture = make_integer_architecture("max_speed")
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    add_organism(
        simulation.state,
        trait_values={"max_speed": 1},
        energy=9,
    )
    process = Movement(
        movement_pattern=PatternThatMustNotRun(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=1),
    )

    assert process.propose_events(simulation.state) == []


def test_low_energy_energy_acquisition_movement_remains_allowed() -> None:
    """Test conservation permits movement motivated by energy acquisition."""
    architecture = make_integer_architecture("max_speed")
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
        seed=1,
    )
    organism = add_organism(
        simulation.state,
        trait_values={"max_speed": 0},
        energy=1,
        x=1,
        y=1,
    )
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=1),
        movement_intent_model=FixedMovementIntent(
            behavioral_purpose=ENERGY_ACQUISITION,
        ),
    )

    events = process.propose_events(simulation.state)

    assert len(events) == 1
    assert events[0].organism_id == organism.id
    assert events[0].behavioral_purpose == ENERGY_ACQUISITION


def test_dynamic_movement_intent_is_resolved_per_organism() -> None:
    """Test one Movement process may produce different purposes per organism."""

    class EnergyAwareIntent:
        def determine_purpose(
            self,
            organism,
            *,
            simulation_state,
        ) -> str:
            if organism.energy < 10:
                return ENERGY_ACQUISITION
            return EXPLORATION

    architecture = make_integer_architecture("max_speed")
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    low_energy = add_organism(
        simulation.state,
        trait_values={"max_speed": 0},
        energy=5,
    )
    high_energy = add_organism(
        simulation.state,
        trait_values={"max_speed": 0},
        energy=20,
    )
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=1),
        movement_intent_model=EnergyAwareIntent(),
    )

    events = process.propose_events(simulation.state)

    purposes_by_organism = {
        event.organism_id: event.behavioral_purpose for event in events
    }
    assert purposes_by_organism == {
        low_energy.id: ENERGY_ACQUISITION,
        high_energy.id: EXPLORATION,
    }
