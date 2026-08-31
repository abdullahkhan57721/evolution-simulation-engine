"""Tests for Simulation."""

from __future__ import annotations

import pytest

from evo_engine.development import DevelopmentalProfile
from evo_engine.engine import Simulation
from evo_engine.genetics import GeneticPhenotype, Genome
from evo_engine.world import Organism, WorldState
from tests.helpers import (
    make_diploid_genome,
    make_empty_architecture,
    make_empty_genome,
    make_integer_architecture,
    make_organism,
)


def test_simulation_copies_initial_world() -> None:
    """Test that callers retain an independent initial-world object."""
    architecture = make_empty_architecture()
    initial_world = WorldState(width=3, height=3)
    organism = make_organism(
        genetic_architecture=architecture,
        energy=20,
    )
    initial_world.add_organism(organism)

    simulation = Simulation(
        initial_world_state=initial_world,
        genetic_architecture=architecture,
        seed=3,
    )

    simulation.state.world.organisms[0].energy = 1

    assert initial_world.organisms[0].energy == 20


def test_simulation_exposes_shared_genetic_architecture() -> None:
    """Test arbitrary configured services remain accessible through context."""
    architecture = make_empty_architecture()

    simulation = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
    )

    assert simulation.genetic_architecture is architecture


def test_simulation_seed_makes_rng_reproducible() -> None:
    """Test deterministic run-level random-number initialization."""
    architecture = make_empty_architecture()

    first = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        seed=9,
    )
    second = Simulation(
        initial_world_state=WorldState(width=2, height=2),
        genetic_architecture=architecture,
        seed=9,
    )

    assert first.state.rng.random() == second.state.rng.random()


@pytest.mark.parametrize(
    "initial_world_state",
    [None, object(), "world"],
)
def test_simulation_rejects_noncopyable_state(initial_world_state: object) -> None:
    """Test that Simulation requires transactionally copyable model state."""
    with pytest.raises(TypeError):
        Simulation(
            initial_world_state=initial_world_state,
            genetic_architecture=make_empty_architecture(),
        )


def test_simulation_does_not_validate_biological_state_consistency() -> None:
    """Test cross-domain consistency checks remain outside the generic kernel."""
    architecture = make_integer_architecture("adult_body_mass")
    genome = make_diploid_genome(
        architecture,
        {"adult_body_mass": 5},
    )
    world = WorldState(width=2, height=2)
    organism = Organism(
        genome=genome,
        genetic_phenotype=GeneticPhenotype(
            trait_values=(("adult_body_mass", 99),),
        ),
        developmental_profile=DevelopmentalProfile(
            target_values=(("adult_body_mass", 99),),
        ),
    )
    world.add_organism(organism)

    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )

    assert (
        simulation.state.world.organisms[0].genetic_phenotype["adult_body_mass"] == 99
    )


def test_simulation_accepts_empty_genetics() -> None:
    """Test a domain may explicitly configure an empty genetics model."""
    architecture = make_empty_architecture()
    world = WorldState(width=2, height=2)
    world.add_organism(
        Organism(
            genome=Genome(chromosomes=()),
            genetic_phenotype=architecture.express(make_empty_genome()),
            developmental_profile=DevelopmentalProfile(target_values=()),
        )
    )

    simulation = Simulation(
        initial_world_state=world,
        genetic_architecture=architecture,
    )

    assert len(simulation.state.world.organisms) == 1
