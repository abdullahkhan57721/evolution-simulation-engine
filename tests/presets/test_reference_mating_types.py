"""Integration tests for reference-ecology mating types."""

from __future__ import annotations

from collections import Counter

from evo_engine.engine import SequentialStepCoordinator
from evo_engine.presets import (
    ReferenceEcologyConfig,
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.processes import Reproduction
from evo_engine.reproduction import RandomMatingType


def _reference_reproduction(config: ReferenceEcologyConfig) -> Reproduction:
    engine = build_reference_engine(config)
    coordinator = engine.step_coordinator
    assert isinstance(coordinator, SequentialStepCoordinator)

    for stage in coordinator.stages:
        for process in stage.processes:
            if isinstance(process, Reproduction):
                return process
    raise AssertionError("Reference lifecycle did not contain Reproduction.")


def test_reference_founders_have_balanced_mating_types() -> None:
    """Test founders alternate mating types without initialization randomness."""
    simulation = build_reference_simulation(
        ReferenceEcologyConfig(initial_population=7)
    )
    counts = Counter(
        organism.mating_type
        for organism in simulation.state.domain_state.organisms.values()
    )

    assert counts == {"type_a": 4, "type_b": 3}


def test_reference_pairing_requires_different_mating_types() -> None:
    """Test the wired parent-selection policy excludes same-type pairs."""
    config = ReferenceEcologyConfig(initial_population=6)
    simulation = build_reference_simulation(config)
    process = _reference_reproduction(config)
    organisms = tuple(simulation.state.domain_state.organisms.values())

    groups = process.parent_selection.propose_parent_groups(
        organisms,
        simulation_state=simulation.state,
        reference_model=process.reference_model,
    )

    assert groups
    for group in groups:
        first_id, second_id = group.parent_ids
        assert (
            simulation.state.domain_state.organisms[first_id].mating_type
            != simulation.state.domain_state.organisms[second_id].mating_type
        )


def test_reference_offspring_assignment_uses_reference_type_set() -> None:
    """Test reference reproduction assigns offspring among the founder types."""
    process = _reference_reproduction(ReferenceEcologyConfig())

    assert isinstance(process.offspring_mating_type_model, RandomMatingType)
    assert process.offspring_mating_type_model.mating_types == ("type_a", "type_b")
