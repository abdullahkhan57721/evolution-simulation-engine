"""Tests for offspring development at the selected birth location."""

from __future__ import annotations

import random

from evo_engine.development import IndependentDevelopment, LinearEnvironmentalDevelopment
from evo_engine.engine import SimulationState
from evo_engine.genetics import ClonalInheritance
from evo_engine.processes import Reproduction
from evo_engine.reproduction import (
    AlwaysEligible,
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    RandomParentLocation,
    SingleParent,
)
from evo_engine.world import EnvironmentalField, WorldState
from tests.helpers import add_organism, make_integer_architecture


def test_offspring_development_samples_selected_birth_location() -> None:
    """Test local developmental exposure is the offspring's actual birth site."""
    architecture = make_integer_architecture("size")
    world = WorldState(
        width=2,
        height=2,
        environmental_fields=(
            EnvironmentalField(name="temperature", default_value=20),
        ),
    )
    state = SimulationState(
        world=world,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )
    state.world.set_environmental_value("temperature", x=1, y=1, value=30)
    parent = add_organism(
        state,
        trait_values={"size": 10},
        energy=10,
        x=1,
        y=1,
    )
    process = Reproduction(
        eligibility=AlwaysEligible(),
        parent_selection=SingleParent(),
        inheritance_model=ClonalInheritance(),
        parental_investment=FixedEnergyInvestment(amount=1),
        offspring_placement=RandomParentLocation(),
        development_model=IndependentDevelopment(
            trait_models=(
                (
                    "size",
                    LinearEnvironmentalDevelopment(
                        environmental_field_name="temperature",
                        reference_environment=20,
                        slope=1,
                    ),
                ),
            )
        ),
        offspring_body_mass_model=FixedBodyMassAtBirth(body_mass=1),
    )

    event = process.materialize_event(state, process.propose_events(state)[0])

    assert event.parent_ids == (parent.id,)
    assert (event.x, event.y) == (1, 1)
    assert event.offspring_developmental_profile["size"] == 20
