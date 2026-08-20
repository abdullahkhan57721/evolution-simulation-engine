"""Run a minimal aging-only simulation."""

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    StageCoordinator,
)
from evo_engine.genetics import GeneticArchitecture, Genome
from evo_engine.processes import Aging
from evo_engine.resolvers import AcceptAll
from evo_engine.world import Organism, WorldState


def create_simulation() -> Simulation:
    """Create a minimal simulation with one organism.

    Returns:
        Configured simulation.
    """
    genetic_architecture = GeneticArchitecture(
        loci=(),
        traits=(),
    )
    genome = Genome(
        chromosomes=(),
    )

    world = WorldState(
        width=10,
        height=10,
    )
    world.add_organism(
        Organism.from_genome(
            genetic_architecture=genetic_architecture,
            genome=genome,
            age=0,
            energy=100,
            x=5,
            y=5,
        )
    )

    return Simulation(
        initial_world_state=world,
        genetic_architecture=genetic_architecture,
        seed=42,
    )


def create_engine() -> SimulationEngine:
    """Create an engine containing only the Aging process.

    Returns:
        Configured simulation engine.
    """
    aging_stage = StageCoordinator(
        processes=(Aging(),),
        resolver=AcceptAll(),
    )

    return SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(aging_stage,),
        ),
        stopping_condition=MaxSteps(
            max_steps=10,
        ),
    )


def main() -> None:
    """Run the example and print the final organism age."""
    simulation = create_simulation()
    engine = create_engine()

    engine.run(simulation)

    organism = next(iter(simulation.state.world.organisms.values()))
    print(f"Final age: {organism.age}")


if __name__ == "__main__":
    main()
