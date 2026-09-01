"""Tests proving configuration compilation is independent of biology."""

from __future__ import annotations

from typing import assert_type

import attrs
import pytest

from evo_engine.configuration import Dependency, SimulationSpec
from evo_engine.context import ContextKey, SimulationContext
from evo_engine.engine import MaxSteps, SimulationState


@attrs.define(slots=True)
class _CounterState:
    value: int = 0

    def copy(self) -> _CounterState:
        return _CounterState(value=self.value)


@attrs.frozen(slots=True)
class _NoOpCoordinator:
    def coordinate(self, simulation_state: SimulationState) -> SimulationState:
        return simulation_state


@attrs.frozen(slots=True)
class _GenericRequirement:
    dependency: Dependency

    @property
    def required_dependencies(self) -> frozenset[Dependency]:
        return frozenset({self.dependency})

    def coordinate(self, simulation_state: SimulationState) -> SimulationState:
        return simulation_state


def test_generic_spec_compiles_nonbiological_state() -> None:
    service = object()
    context = SimulationContext.from_mapping({"selection_policy": service})
    spec = SimulationSpec(
        initial_world_state=_CounterState(value=2),
        step_coordinator=_NoOpCoordinator(),
        stopping_condition=MaxSteps(max_steps=0),
        context=context,
    )
    compiled = spec.compile()
    assert compiled.simulation.state.world.value == 2
    assert compiled.simulation.context.require("selection_policy") is service
    assert compiled.dependency_report.missing == frozenset()


def test_generic_preflight_rejects_missing_dependency() -> None:
    dependency = Dependency(category="resource", name="compute")
    spec = SimulationSpec(
        initial_world_state=_CounterState(),
        step_coordinator=_GenericRequirement(dependency=dependency),
        stopping_condition=MaxSteps(max_steps=0),
    )
    with pytest.raises(ValueError, match="resource:compute"):
        spec.compile()


def test_generic_preflight_accepts_explicit_domain_capability() -> None:
    dependency = Dependency(category="resource", name="compute")
    compiled = SimulationSpec(
        initial_world_state=_CounterState(),
        step_coordinator=_GenericRequirement(dependency=dependency),
        stopping_condition=MaxSteps(max_steps=0),
        provided_dependencies=frozenset({dependency}),
    ).compile()
    assert compiled.dependency_report.provided == frozenset({dependency})


def test_typed_context_key_validates_service_type() -> None:
    key = ContextKey[int](name="population_size", value_type=int)
    context = SimulationContext.from_mapping({"population_size": 12})
    population_size = context.require(key)
    assert_type(population_size, int)
    assert population_size == 12
    assert_type(context.get(key), int | None)

    wrong_context = SimulationContext.from_mapping({"population_size": "twelve"})
    with pytest.raises(TypeError, match="population_size"):
        wrong_context.require(key)
