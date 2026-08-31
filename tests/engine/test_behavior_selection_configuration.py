"""Tests for domain configuration carried by the simulation kernel."""

from __future__ import annotations

from evo_engine.behavior import EnergyConservationBehavior
from evo_engine.engine import Simulation
from evo_engine.world import WorldState
from tests.helpers import make_empty_architecture


def test_simulation_does_not_install_domain_behavior_defaults() -> None:
    """Test the generic kernel does not invent biological behavior services."""
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
    )

    assert not hasattr(simulation.state, "behavior_selection_model")


def test_simulation_uses_configured_behavior_selection_model() -> None:
    """Test simulations retain an explicitly configured domain service."""
    model = EnergyConservationBehavior(
        energy_threshold=10,
    )
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
        behavior_selection_model=model,
    )

    assert simulation.state.behavior_selection_model is model


def test_transactional_state_copy_shares_behavior_selection_configuration() -> None:
    """Test state copies share immutable domain configuration services."""
    model = EnergyConservationBehavior(
        energy_threshold=10,
    )
    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        genetic_architecture=make_empty_architecture(),
        behavior_selection_model=model,
    )

    copied = simulation.state.copy()

    assert copied.behavior_selection_model is model


def test_simulation_does_not_validate_opaque_domain_services() -> None:
    """Test domain-specific validation is not a kernel responsibility."""
    service = object()

    simulation = Simulation(
        initial_world_state=WorldState(width=3, height=3),
        behavior_selection_model=service,
    )

    assert simulation.state.behavior_selection_model is service
