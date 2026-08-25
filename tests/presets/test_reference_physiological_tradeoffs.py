"""Integration tests for reference-ecology physiological tradeoffs."""

from __future__ import annotations

import attrs

from evo_engine.energetics import AdditiveMetabolicCost
from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferencePhysiologicalTradeoffs,
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.processes import Metabolism


def _metabolism(config: ReferenceEcologyConfig) -> Metabolism:
    engine = build_reference_engine(config)
    for stage in engine.step_coordinator.stages:
        for process in stage.processes:
            if isinstance(process, Metabolism):
                return process
    raise AssertionError("Reference lifecycle did not contain Metabolism.")


def _founder_cost(config: ReferenceEcologyConfig) -> int:
    simulation = build_reference_simulation(config)
    founder = next(iter(simulation.state.world.organisms.values()))
    return _metabolism(config).cost_model.calculate_cost(founder, simulation.state)


def test_reference_metabolism_composes_basal_and_physiological_costs() -> None:
    """Test the reference preset explicitly composes maintenance with metabolism."""
    metabolism = _metabolism(ReferenceEcologyConfig())

    assert isinstance(metabolism.cost_model, AdditiveMetabolicCost)
    assert len(metabolism.cost_model.cost_models) == 2


def test_reference_founder_physiology_has_modest_maintenance_cost() -> None:
    """Test default performance capabilities add one maintenance energy unit."""
    config = ReferenceEcologyConfig()
    no_tradeoffs = ReferencePhysiologicalTradeoffs(
        max_speed_cost=0,
        sensory_range_cost=0,
        sensory_accuracy_cost=0,
        max_intake_rate_cost=0,
        assimilation_efficiency_cost=0,
        attack_strength_cost=0,
        defense_cost=0,
    )
    basal_only_config = attrs.evolve(
        config,
        physiological_tradeoffs=no_tradeoffs,
    )

    assert _founder_cost(config) == _founder_cost(basal_only_config) + 1


def test_high_reference_performance_has_higher_maintenance_cost() -> None:
    """Test near-maximal realized capabilities cannot improve for free."""
    config = ReferenceEcologyConfig()
    high_performance_traits = attrs.evolve(
        config.traits,
        max_speed=4,
        sensory_range=20,
        sensory_accuracy=100,
        max_intake_rate=50,
        assimilation_efficiency=100,
        attack_strength=50,
        defense=50,
    )
    high_performance_config = attrs.evolve(
        config,
        traits=high_performance_traits,
    )

    assert _founder_cost(high_performance_config) > _founder_cost(config)
    assert _founder_cost(high_performance_config) == _founder_cost(config) + 6
