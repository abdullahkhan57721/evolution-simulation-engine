"""Integration tests for reference mating-type reproductive investment."""

from __future__ import annotations

from evo_engine.engine import SequentialStepCoordinator
from evo_engine.genetics import OFFSPRING_ENERGY
from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceMatingTypeInvestmentScales,
    build_reference_engine,
    build_reference_simulation,
)
from evo_engine.processes import Reproduction
from evo_engine.reproduction import MatingTypeScaledInvestment


def _reference_reproduction(config: ReferenceEcologyConfig) -> Reproduction:
    engine = build_reference_engine(config)
    coordinator = engine.step_coordinator
    assert isinstance(coordinator, SequentialStepCoordinator)

    for stage in coordinator.stages:
        for process in stage.processes:
            if isinstance(process, Reproduction):
                return process
    raise AssertionError("Reference lifecycle did not contain Reproduction.")


def test_reference_reproduction_uses_asymmetric_mating_type_investment() -> None:
    """Test default mating types split the historical pair cost six to two."""
    config = ReferenceEcologyConfig(initial_population=2)
    simulation = build_reference_simulation(config)
    process = _reference_reproduction(config)
    parents = tuple(simulation.state.domain_state.organisms.values())

    assert tuple(parent.mating_type for parent in parents) == ("type_a", "type_b")
    assert isinstance(process.reproductive_energy_investment, MatingTypeScaledInvestment)
    assert process.reproductive_energy_investment.required_traits == frozenset({OFFSPRING_ENERGY})
    assert process.reproductive_energy_investment.determine_investments(
        parents,
        simulation_state=simulation.state,
    ) == (6, 2)
    assert process.reproductive_energy_investment.determine_investments(
        tuple(reversed(parents)),
        simulation_state=simulation.state,
    ) == (2, 6)


def test_reference_investment_scales_are_configurable() -> None:
    """Test reference mating-type asymmetry can be disabled by configuration."""
    config = ReferenceEcologyConfig(
        initial_population=2,
        mating_type_investment_scales=ReferenceMatingTypeInvestmentScales(
            denominator=1,
            type_a_numerator=1,
            type_b_numerator=1,
        ),
    )
    simulation = build_reference_simulation(config)
    process = _reference_reproduction(config)
    parents = tuple(simulation.state.domain_state.organisms.values())

    assert process.reproductive_energy_investment.determine_investments(
        parents,
        simulation_state=simulation.state,
    ) == (4, 4)
