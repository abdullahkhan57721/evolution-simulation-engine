"""Run the complete reference ecological and evolutionary simulation."""

from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def main() -> None:
    """Run the reference ecology and print a compact final-state summary."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            max_steps=50,
            seed=42,
        )
    )
    initial_population = len(ecology.simulation.state.world.organisms)

    ecology.engine.run(ecology.simulation)

    world = ecology.simulation.state.world
    print(f"Completed steps: {ecology.simulation.state.step_index}")
    print(f"Initial population: {initial_population}")
    print(f"Final population: {len(world.organisms)}")
    print(f"Carcasses: {len(world.carcasses)}")
    print(f"Resource deposits: {len(world.resources)}")
    print(f"Total environmental resources: {sum(world.resources.values())}")


if __name__ == "__main__":
    main()
