"""Integration tests for behavior selection across simulation processes."""

from __future__ import annotations

from evo_engine.behavior import EnergyConservationBehavior
from evo_engine.energetics import LinearGrowthCost
from evo_engine.engine import SequentialStepCoordinator, Simulation, StageCoordinator
from evo_engine.genetics import ClonalInheritance
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.growth import FixedGrowthRate
from evo_engine.processes import Growth, Predation, Reproduction, ResourceConsumption
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.spatial.neighborhoods import SameCell
from evo_engine.world import WorldState
from tests.helpers import add_organism, make_empty_architecture, make_integer_architecture


def test_conservation_suppresses_growth_even_when_affordable() -> None:
    """Test behavioral suppression is distinct from energetic affordability."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    add_organism(
        simulation.state,
        trait_values={ADULT_BODY_MASS: 20},
        body_mass=10,
        energy=9,
    )
    process = Growth(
        growth_model=FixedGrowthRate(amount_per_timestep=1),
        growth_cost_model=LinearGrowthCost(energy_per_body_mass_unit=1),
    )

    assert process.propose_events(simulation.state) == []


def test_conservation_suppresses_reproduction_even_when_eligible_and_affordable() -> None:
    """Test low-energy behavior is checked before reproductive eligibility."""
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    add_organism(
        simulation.state,
        energy=9,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=1),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )

    assert process.propose_events(simulation.state) == []


def test_conservation_preserves_resource_consumption_at_low_energy() -> None:
    """Test low-energy organisms may still attempt direct energy acquisition."""
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    organism = add_organism(
        simulation.state,
        energy=1,
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(
        x=1,
        y=1,
        amount=4,
    )
    process = ResourceConsumption(requested_amount=4)

    events = process.propose_events(simulation.state)

    assert events == [
        ResourceConsumption.Event(
            step_index=0,
            organism_id=organism.id,
            x=1,
            y=1,
            amount=4,
        )
    ]


def test_conservation_preserves_predation_at_low_energy() -> None:
    """Test depleted predators may still attempt energy-acquisition predation."""
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    predator = add_organism(
        simulation.state,
        energy=1,
        body_mass=10,
        x=1,
        y=1,
    )
    prey = add_organism(
        simulation.state,
        energy=100,
        body_mass=5,
        x=1,
        y=1,
    )
    process = Predation(
        neighborhood=SameCell(),
        consumption_percent=100,
    )

    events = process.propose_events(simulation.state)

    assert len(events) == 1
    assert events[0].predator_id == predator.id
    assert events[0].prey_id == prey.id


def test_energy_acquisition_can_leave_conservation_mode_within_same_step() -> None:
    """Test later stages re-evaluate behavior from current organism energy."""
    architecture = make_integer_architecture(ADULT_BODY_MASS)
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=architecture,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )
    organism = add_organism(
        simulation.state,
        trait_values={ADULT_BODY_MASS: 12},
        body_mass=10,
        energy=5,
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(
        x=1,
        y=1,
        amount=10,
    )
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(ResourceConsumption(requested_amount=10),),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(
                    Growth(
                        growth_model=FixedGrowthRate(amount_per_timestep=2),
                        growth_cost_model=LinearGrowthCost(
                            energy_per_body_mass_unit=1,
                        ),
                    ),
                ),
                resolver=AcceptAll(),
            ),
        )
    )

    simulation.state = coordinator.coordinate(simulation.state)

    updated = simulation.state.world.organisms[organism.id]
    assert updated.body_mass == 12
    assert updated.energy == 13
