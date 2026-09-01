"""Tests for domain-neutral context configuration on kernel state."""

from __future__ import annotations

from evo_engine.engine import Simulation, SimulationState
from tests.engine.helpers import CounterState


def test_simulation_does_not_install_domain_service_defaults() -> None:
    simulation = Simulation(initial_domain_state=CounterState())
    assert not hasattr(simulation, "selection_policy")
    assert not hasattr(simulation.state, "selection_policy")


def test_simulation_exposes_explicit_context_service_only_through_context() -> None:
    service = object()
    simulation = Simulation(
        initial_domain_state=CounterState(),
        selection_policy=service,
    )
    assert simulation.context.require("selection_policy") is service
    assert simulation.state.context.require("selection_policy") is service
    assert not hasattr(simulation, "selection_policy")
    assert not hasattr(simulation.state, "selection_policy")


def test_transactional_copy_shares_context_services() -> None:
    service = object()
    state = SimulationState(domain_state=CounterState(), selection_policy=service)
    copied = state.copy()
    assert copied.context is state.context
    assert copied.context.require("selection_policy") is service


def test_kernel_does_not_validate_opaque_domain_services() -> None:
    service = object()
    simulation = Simulation(
        initial_domain_state=CounterState(),
        selection_policy=service,
    )
    assert simulation.context.require("selection_policy") is service
