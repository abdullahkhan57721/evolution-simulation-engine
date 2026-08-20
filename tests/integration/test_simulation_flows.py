"""Integration tests for multi-component simulation flows."""

from __future__ import annotations

from evo_engine.energetics import FixedMetabolicCost
from evo_engine.engine import SequentialStepCoordinator, Simulation, StageCoordinator
from evo_engine.genetics import ClonalInheritance
from evo_engine.processes import (
    Metabolism,
    Reproduction,
    ResourceConsumption,
    Starvation,
)
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    SingleParent,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.resource_allocation import EqualShare
from evo_engine.world import WorldState
from tests.helpers import (
    add_organism,
    make_empty_architecture,
    make_integer_architecture,
    make_organism,
)


def test_resource_competition_resolves_before_application() -> None:
    """Test simultaneous local requests share pre-application resources."""
    architecture = make_empty_architecture()
    world = WorldState(
        width=3,
        height=3,
    )
    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )
    first = add_organism(
        simulation.state,
        energy=0,
        x=1,
        y=1,
    )
    second = add_organism(
        simulation.state,
        energy=0,
        x=1,
        y=1,
    )
    simulation.state.world.add_resources(
        x=1,
        y=1,
        amount=5,
    )

    StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=5,
            ),
        ),
        resolver=EqualShare(),
    ).coordinate(simulation.state)

    assert first.energy == 3
    assert second.energy == 2
    assert (1, 1) not in simulation.state.world.resources


def test_metabolism_then_starvation_across_sequential_stages() -> None:
    """Test later stages observe mutations from earlier stages in a step."""
    architecture = make_integer_architecture("adult_body_mass")
    world = WorldState(
        width=3,
        height=3,
    )
    organism = make_organism(
        genetic_architecture=architecture,
        trait_values={"adult_body_mass": 4},
        energy=2,
    )
    world.add_organism(organism)
    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )

    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(
                    Metabolism(
                        cost_model=FixedMetabolicCost(
                            amount=2,
                        ),
                    ),
                ),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(Starvation(),),
                resolver=AcceptAll(),
            ),
        )
    )

    simulation.state = coordinator.coordinate(simulation.state)

    assert not simulation.state.world.organisms
    assert next(iter(simulation.state.world.carcasses.values())).resource_units == 4


def test_reproduction_materializes_only_resolved_births() -> None:
    """Test reproduction integrates with the stage materialization phase."""
    architecture = make_integer_architecture(
        "offspring_energy",
    )
    world = WorldState(
        width=3,
        height=3,
    )
    parent = make_organism(
        genetic_architecture=architecture,
        trait_values={"offspring_energy": 5},
        energy=20,
    )
    world.add_organism(parent)
    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
        seed=2,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(
            amount=5,
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(
            body_mass=1,
        ),
    )

    StageCoordinator(
        processes=(process,),
        resolver=AcceptAll(),
    ).coordinate(simulation.state)

    assert len(simulation.state.world.organisms) == 2
    assert simulation.state.world.organisms[0].energy == 15
    assert simulation.state.world.organisms[1].energy == 5
