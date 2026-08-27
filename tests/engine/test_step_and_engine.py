"""Tests for step coordination, stopping, and SimulationEngine."""

from __future__ import annotations

import pytest

from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    Simulation,
    SimulationEngine,
    StageCoordinator,
)
from evo_engine.processes import Aging
from evo_engine.resolvers import AcceptAll
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture, make_organism


def test_sequential_step_runs_stages_in_order_and_increments_index() -> None:
    """Test ordered stage execution and post-step index advancement."""
    architecture = make_empty_architecture()
    world = WorldState(width=2, height=2)
    world.add_organism(
        make_organism(
            genetic_architecture=architecture,
        )
    )

    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(Aging(),),
                resolver=AcceptAll(),
            ),
            StageCoordinator(
                processes=(Aging(),),
                resolver=AcceptAll(),
            ),
        )
    )

    next_state = coordinator.coordinate(simulation.state)

    assert next_state.step_index == 1
    assert next_state.world.organisms[0].age == 2
    assert simulation.state.step_index == 0
    assert simulation.state.world.organisms[0].age == 0


def test_failed_step_leaves_authoritative_state_unchanged() -> None:
    """Test transactional rollback when a stage raises."""
    architecture = make_empty_architecture()
    world = WorldState(width=2, height=2)
    world.add_organism(
        make_organism(
            genetic_architecture=architecture,
            age=1,
        )
    )
    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )

    class FailingStage:
        def coordinate(self, simulation_state) -> None:
            simulation_state.world.organisms[0].age = 99
            raise RuntimeError("stage failed")

    coordinator = SequentialStepCoordinator(
        stages=(FailingStage(),),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError):
        coordinator.coordinate(simulation.state)

    assert simulation.state.step_index == 0
    assert simulation.state.world.organisms[0].age == 1


@pytest.mark.parametrize(
    ("step_index", "max_steps", "expected"),
    [
        (0, 0, True),
        (0, 1, False),
        (1, 1, True),
        (2, 1, True),
    ],
)
def test_max_steps(
    step_index: int,
    max_steps: int,
    expected: bool,
) -> None:
    """Test the maximum-step stopping boundary."""
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=1, height=1),
        genetic_architecture=architecture,
    )
    simulation.state.step_index = step_index

    assert MaxSteps(max_steps=max_steps).should_stop(simulation.state) is expected


def test_simulation_engine_runs_until_stopping_condition() -> None:
    """Test end-to-end engine iteration."""
    architecture = make_empty_architecture()
    world = WorldState(width=2, height=2)
    world.add_organism(
        make_organism(
            genetic_architecture=architecture,
        )
    )
    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(Aging(),),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=3),
    )

    engine.run(simulation)

    assert simulation.state.step_index == 3
    assert simulation.state.world.organisms[0].age == 3


def test_simulation_engine_does_not_validate_domain_specific_requirements() -> None:
    """Test biological preflight validation is not a kernel responsibility."""
    from evo_engine.energetics import FixedLocomotionCost
    from evo_engine.genetics import MAX_SPEED
    from evo_engine.processes import Movement
    from evo_engine.spatial.boundary_conditions import Clamped
    from evo_engine.spatial.movement_patterns import UniformRandom

    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
    )
    movement = Movement(
        movement_pattern=UniformRandom(),
        boundary_condition=Clamped(),
        locomotion_cost_model=FixedLocomotionCost(
            amount=0,
        ),
    )
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(movement,),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=0),
    )

    assert movement.required_traits == frozenset({MAX_SPEED})

    engine.run(simulation)

    assert simulation.state.step_index == 0


def test_simulation_engine_accepts_satisfied_process_trait_requirements() -> None:
    """Test domain-valid process configuration remains executable by the kernel."""
    from evo_engine.energetics import FixedLocomotionCost
    from evo_engine.genetics import MAX_SPEED
    from evo_engine.processes import Movement
    from evo_engine.spatial.boundary_conditions import Clamped
    from evo_engine.spatial.movement_patterns import UniformRandom
    from tests.helpers import make_integer_architecture

    architecture = make_integer_architecture(MAX_SPEED)
    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
    )
    engine = SimulationEngine(
        step_coordinator=SequentialStepCoordinator(
            stages=(
                StageCoordinator(
                    processes=(
                        Movement(
                            movement_pattern=UniformRandom(),
                            boundary_condition=Clamped(),
                            locomotion_cost_model=FixedLocomotionCost(
                                amount=0,
                            ),
                        ),
                    ),
                    resolver=AcceptAll(),
                ),
            )
        ),
        stopping_condition=MaxSteps(max_steps=0),
    )

    engine.run(simulation)

    assert simulation.state.step_index == 0
