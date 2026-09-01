"""Run the complete reference ecological and evolutionary simulation."""

from evo_engine.genetics import GROWTH_RATE
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def main() -> None:
    """Run the reference ecology and print final state and observation summaries."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            max_steps=50,
            seed=42,
        )
    )
    world = ecology.simulation.state.domain_state
    initial_population = len(world.organisms)

    ecology.engine.run(ecology.simulation)

    world = ecology.simulation.state.domain_state
    latest = ecology.recorder.latest

    print(f"Completed steps: {ecology.simulation.state.step_index}")
    print(f"Initial population: {initial_population}")
    print(f"Final population: {len(world.organisms)}")
    print(f"Carcasses: {len(world.carcasses)}")
    print(f"Resource deposits: {len(world.resources)}")
    print(f"Total environmental resources: {sum(world.resources.values())}")
    print(f"Recorded observations: {len(ecology.recorder.observations)}")

    if latest is not None:
        print(f"Final mean energy: {latest.energy.mean}")
        print(f"Final mean growth rate: {latest.trait(GROWTH_RATE).summary.mean}")


if __name__ == "__main__":
    main()
