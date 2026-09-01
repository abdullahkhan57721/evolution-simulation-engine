"""Regression tests for the stabilized domain-neutral kernel public API."""

from __future__ import annotations

import evo_engine.context as context
import evo_engine.engine as engine

_EXPECTED_ENGINE_API = {
    "EventMaterializer",
    "MaxSteps",
    "Observer",
    "Process",
    "Resolver",
    "SequentialStepCoordinator",
    "Simulation",
    "SimulationEngine",
    "SimulationEvent",
    "SimulationState",
    "StageCoordinator",
    "StepCoordinator",
    "StoppingCondition",
}


def test_engine_public_api_is_orchestration_only() -> None:
    """Test context types do not leak into the engine orchestration namespace."""
    assert set(engine.__all__) == _EXPECTED_ENGINE_API
    assert not hasattr(engine, "ContextKey")
    assert not hasattr(engine, "SimulationContext")


def test_context_public_api_is_small_and_explicit() -> None:
    """Test the context foundation exposes only its typed public contracts."""
    assert set(context.__all__) == {"ContextKey", "SimulationContext"}
