"""Tests for immutable SimulationContext integration."""

from __future__ import annotations

from typing import assert_type

import pytest

from evo_engine.engine import ContextKey, SimulationContext, SimulationState
from tests.engine.helpers import CounterState


def test_transactional_copy_shares_simulation_context() -> None:
    """Test immutable configuration is shared across state snapshots."""
    service = object()
    state = SimulationState(
        world=CounterState(),
        service=service,
    )

    copied = state.copy()

    assert copied.context is state.context
    assert copied.service is service


def test_simulation_state_accepts_explicit_context() -> None:
    """Test callers may construct state from a complete shared context."""
    service = object()
    context = SimulationContext.from_mapping({"service": service})

    state = SimulationState(
        world=CounterState(),
        context=context,
    )

    assert state.context is context
    assert state.service is service


def test_simulation_state_rejects_mixed_context_construction_styles() -> None:
    """Test explicit context cannot conflict with separate context arguments."""
    context = SimulationContext.from_mapping({"service": object()})

    with pytest.raises(TypeError, match="context cannot be combined"):
        SimulationState(
            world=CounterState(),
            context=context,
            other_service=object(),
        )


def test_typed_context_key_preserves_type_and_validates_runtime_value() -> None:
    """Test typed context keys provide static and runtime type safety."""
    key = ContextKey(name="capacity", value_type=int)
    context = SimulationContext.from_mapping({"capacity": 12})

    capacity = context.require(key)

    assert_type(capacity, int)
    assert capacity == 12
    assert_type(context.get(key), int | None)

    wrong_context = SimulationContext.from_mapping({"capacity": "twelve"})
    with pytest.raises(TypeError, match="capacity"):
        wrong_context.require(key)


def test_context_get_returns_default_for_missing_service() -> None:
    """Test optional context lookup does not assign semantics to absence."""
    context = SimulationContext()

    assert context.get("missing") is None
    assert context.get("missing", 7) == 7


@pytest.mark.parametrize("name", ["", "   "])
def test_context_key_rejects_blank_name(name: str) -> None:
    """Test context service identifiers are nonblank."""
    with pytest.raises(ValueError, match="blank"):
        ContextKey(name=name, value_type=int)
