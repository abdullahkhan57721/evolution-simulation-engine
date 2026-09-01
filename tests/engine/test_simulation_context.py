"""Tests for immutable SimulationContext integration."""

from __future__ import annotations

from typing import ClassVar, assert_type

import pytest

from evo_engine.context import ContextKey, SimulationContext
from evo_engine.engine import SimulationState
from tests.engine.helpers import CounterState


class CountingIntContextKey(ContextKey[int]):
    """Count runtime validations performed by one typed context key."""

    validations: ClassVar[int] = 0

    def validate(self, value: object) -> int:
        """Count and perform one runtime value validation."""
        CountingIntContextKey.validations += 1
        return super().validate(value)


def test_transactional_copy_shares_simulation_context() -> None:
    """Test immutable configuration is shared across state snapshots."""
    service = object()
    state = SimulationState(domain_state=CounterState(), service=service)
    copied = state.copy()
    assert copied.context is state.context
    assert copied.context.require("service") is service
    assert not hasattr(copied, "service")


def test_simulation_state_accepts_explicit_context() -> None:
    """Test callers may construct state from a complete shared context."""
    service = object()
    context = SimulationContext.from_mapping({"service": service})
    state = SimulationState(domain_state=CounterState(), context=context)
    assert state.context is context
    assert state.context.require("service") is service
    assert not hasattr(state, "service")


def test_simulation_state_rejects_mixed_context_construction_styles() -> None:
    """Test explicit context cannot conflict with separate context arguments."""
    context = SimulationContext.from_mapping({"service": object()})
    with pytest.raises(TypeError, match="context cannot be combined"):
        SimulationState(
            domain_state=CounterState(),
            context=context,
            other_service=object(),
        )


def test_typed_context_key_preserves_type_and_validates_runtime_value() -> None:
    """Test typed context keys provide static and runtime type safety."""
    key = ContextKey[int](name="capacity", value_type=int)
    context = SimulationContext.from_mapping({"capacity": 12})
    capacity = context.require(key)
    assert_type(capacity, int)
    assert capacity == 12
    assert_type(context.get(key), int | None)

    wrong_context = SimulationContext.from_mapping({"capacity": "twelve"})
    with pytest.raises(TypeError, match="capacity"):
        wrong_context.require(key)


def test_typed_context_key_caches_successful_runtime_validation() -> None:
    """Test repeated typed lookup reuses one validated immutable binding."""
    CountingIntContextKey.validations = 0
    key = CountingIntContextKey(name="capacity", value_type=int)
    context = SimulationContext.from_mapping({"capacity": 12})

    assert context.require(key) == 12
    assert context.require(key) == 12
    assert CountingIntContextKey.validations == 1


def test_typed_context_cache_preserves_distinct_key_validation() -> None:
    """Test a cached service does not bypass another key's runtime type check."""
    context = SimulationContext.from_mapping({"capacity": 12})
    int_key = ContextKey[int](name="capacity", value_type=int)
    str_key = ContextKey[str](name="capacity", value_type=str)

    assert context.require(int_key) == 12
    with pytest.raises(TypeError, match="capacity"):
        context.require(str_key)


def test_context_get_returns_default_for_missing_service() -> None:
    """Test optional context lookup does not assign semantics to absence."""
    context = SimulationContext()
    assert context.get("missing") is None
    assert context.get("missing", 7) == 7


@pytest.mark.parametrize("name", ["", "   "])
def test_context_key_rejects_blank_name(name: str) -> None:
    """Test context service identifiers are nonblank."""
    with pytest.raises(ValueError, match="blank"):
        ContextKey[int](name=name, value_type=int)
