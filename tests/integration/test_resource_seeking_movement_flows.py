"""Integration tests for sensory-limited resource-seeking movement."""

from __future__ import annotations

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EnergyConservationBehavior,
    FixedMovementIntent,
    FixedSensoryRange,
    NearestResourceTarget,
    UnrestrictedBehavior,
)
from evo_engine.energetics import FixedLocomotionCost
from evo_engine.engine import Simulation
from evo_engine.genetics.builtin_traits import MAX_SPEED, SENSORY_RANGE
from evo_engine.processes import Movement
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.spatial.movement_patterns import UniformRandom
from evo_engine.world import WorldState
from tests.helpers import add_organism, make_integer_architecture


def test_hungry_organism_moves_toward_detectable_resource() -> None:
    """Test energy-acquisition movement targets visible food under conservation."""
    architecture = make_integer_architecture(MAX_SPEED, SENSORY_RANGE)
    simulation = Simulation(
        initial_world_state=WorldState(width=8, height=3),
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
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=1),
        movement_intent_model=FixedMovementIntent(
            behavioral_purpose=ENERGY_ACQUISITION,
        ),
        movement_target_model=NearestResourceTarget(),
    )

    event = process.propose_events(simulation.state)[0]

    assert event.organism_id == organism.id
    assert (event.target_x, event.target_y) == (4, 1)
    assert (event.dx, event.dy) == (1, 0)
    assert (event.new_x, event.new_y) == (2, 1)
    assert event.behavioral_purpose == ENERGY_ACQUISITION


def test_resource_outside_sensory_range_uses_untargeted_search_pattern() -> None:
    """Test undetected food does not influence search displacement."""

    class SearchPattern:
        def choose_displacement(self, *, rng, max_speed):
            return (0, 1)

    architecture = make_integer_architecture(MAX_SPEED)
    simulation = Simulation(
        initial_world_state=WorldState(width=8, height=4),
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    add_organism(
        simulation.state,
        trait_values={MAX_SPEED: 1},
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(x=6, y=1, amount=10)
    process = Movement(
        movement_pattern=SearchPattern(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_intent_model=FixedMovementIntent(
            behavioral_purpose=ENERGY_ACQUISITION,
        ),
        movement_target_model=NearestResourceTarget(
            sensory_range_model=FixedSensoryRange(radius=2),
        ),
    )

    event = process.propose_events(simulation.state)[0]

    assert event.target_x is None
    assert event.target_y is None
    assert (event.dx, event.dy) == (0, 1)


def test_resource_on_current_cell_prevents_random_departure() -> None:
    """Test a detected resource underfoot keeps the organism at the food cell."""

    class PatternThatMustNotRun:
        def choose_displacement(self, *, rng, max_speed):
            raise AssertionError("targeted movement must bypass fallback search")

    architecture = make_integer_architecture(MAX_SPEED, SENSORY_RANGE)
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    organism = add_organism(
        simulation.state,
        trait_values={
            MAX_SPEED: 1,
            SENSORY_RANGE: 0,
        },
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(x=1, y=1, amount=4)
    process = Movement(
        movement_pattern=PatternThatMustNotRun(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=3),
        movement_intent_model=FixedMovementIntent(
            behavioral_purpose=ENERGY_ACQUISITION,
        ),
        movement_target_model=NearestResourceTarget(),
    )

    event = process.propose_events(simulation.state)[0]

    assert (event.target_x, event.target_y) == (organism.x, organism.y)
    assert (event.dx, event.dy) == (0, 0)
    assert event.energy_cost == 0


def test_resource_seeker_reaches_visible_food_over_repeated_movement() -> None:
    """Test repeated target-directed movement converges on a resource cell."""
    architecture = make_integer_architecture(MAX_SPEED, SENSORY_RANGE)
    simulation = Simulation(
        initial_world_state=WorldState(width=5, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=UnrestrictedBehavior(),
    )
    organism = add_organism(
        simulation.state,
        trait_values={
            MAX_SPEED: 1,
            SENSORY_RANGE: 4,
        },
        x=0,
        y=1,
    )
    simulation.state.world.add_resources(x=2, y=1, amount=5)
    process = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_intent_model=FixedMovementIntent(
            behavioral_purpose=ENERGY_ACQUISITION,
        ),
        movement_target_model=NearestResourceTarget(),
    )

    for _ in range(2):
        event = process.propose_events(simulation.state)[0]
        process.apply_event(simulation.state, event)

    assert (organism.x, organism.y) == (2, 1)


def test_sensory_trait_is_required_only_by_trait_driven_targeting() -> None:
    """Test resource sensing adds sensory_range without making it universal."""
    untargeted = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
    )
    trait_targeted = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_target_model=NearestResourceTarget(),
    )
    fixed_targeted = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(amount=0),
        movement_target_model=NearestResourceTarget(
            sensory_range_model=FixedSensoryRange(radius=3),
        ),
    )

    assert untargeted.required_traits == frozenset({MAX_SPEED})
    assert trait_targeted.required_traits == frozenset({MAX_SPEED, SENSORY_RANGE})
    assert fixed_targeted.required_traits == frozenset({MAX_SPEED})
