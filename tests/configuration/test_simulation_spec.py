"""Tests for dependency-aware SimulationSpec compilation."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.configuration import (
    CHARACTERISTIC,
    ENVIRONMENTAL_FIELD,
    Dependency,
    SimulationSpec,
)
from evo_engine.development import LinearEnvironmentalDevelopment
from evo_engine.engine import MaxSteps, SimulationState
from evo_engine.genetics import GeneticPhenotype
from evo_engine.world import Organism, WorldState
from tests.helpers import (
    developmental_profile,
    make_diploid_genome,
    make_empty_architecture,
    make_integer_architecture,
)


@attrs.frozen(slots=True, kw_only=True)
class _RequirementCoordinator:
    characteristic_name: str | None = None
    component: object | None = None

    @property
    def required_characteristics(self) -> frozenset[str]:
        if self.characteristic_name is None:
            return frozenset()
        return frozenset({self.characteristic_name})

    def coordinate(self, simulation_state: SimulationState) -> SimulationState:
        return simulation_state


def _spec(
    *,
    world: WorldState | None = None,
    architecture=None,
    coordinator: object | None = None,
) -> SimulationSpec:
    if world is None:
        world = WorldState(width=2, height=2)
    if architecture is None:
        architecture = make_empty_architecture()
    if coordinator is None:
        coordinator = _RequirementCoordinator()
    return SimulationSpec(
        initial_world_state=world,
        genetic_architecture=architecture,
        step_coordinator=coordinator,
        stopping_condition=MaxSteps(max_steps=1),
    )


def test_compile_rejects_missing_characteristic_before_runtime() -> None:
    """Test unresolved characteristic dependencies fail during compilation."""
    spec = _spec(
        coordinator=_RequirementCoordinator(characteristic_name="speed"),
    )

    with pytest.raises(ValueError, match="characteristic:speed"):
        spec.compile()


def test_compile_accepts_characteristic_backed_by_genetic_architecture() -> None:
    """Test architecture traits provide developmental characteristic capability."""
    architecture = make_integer_architecture("speed")
    spec = _spec(
        architecture=architecture,
        coordinator=_RequirementCoordinator(characteristic_name="speed"),
    )

    compiled = spec.compile()

    assert Dependency(category=CHARACTERISTIC, name="speed") in (
        compiled.dependency_report.provided
    )


def test_compile_rejects_missing_environmental_field_before_runtime() -> None:
    """Test nested environment-aware models declare world dependencies."""
    developmental_model = LinearEnvironmentalDevelopment(
        environmental_field_name="temperature",
        reference_environment=20,
        slope=1,
    )
    spec = _spec(
        coordinator=_RequirementCoordinator(component=developmental_model),
    )

    with pytest.raises(ValueError, match="environmental_field:temperature"):
        spec.compile()


def test_dependency_report_includes_provided_environmental_field() -> None:
    """Test world fields satisfy nested environmental dependencies."""
    from evo_engine.world import EnvironmentalField

    world = WorldState(
        width=2,
        height=2,
        environmental_fields=(EnvironmentalField(name="temperature", default_value=20),),
    )
    developmental_model = LinearEnvironmentalDevelopment(
        environmental_field_name="temperature",
        reference_environment=20,
        slope=1,
    )
    compiled = _spec(
        world=world,
        coordinator=_RequirementCoordinator(component=developmental_model),
    ).compile()

    assert Dependency(category=ENVIRONMENTAL_FIELD, name="temperature") in (
        compiled.dependency_report.provided
    )


def test_compile_rejects_inconsistent_initial_genetic_cache() -> None:
    """Test initial genome/phenotype consistency is checked at configuration."""
    architecture = make_integer_architecture("size")
    genome = make_diploid_genome(architecture, {"size": 3})
    organism = Organism(
        genome=genome,
        genetic_phenotype=GeneticPhenotype(trait_values=(("size", 4),)),
        developmental_profile=developmental_profile(size=4),
    )
    world = WorldState(width=2, height=2)
    world.add_organism(organism)

    with pytest.raises(ValueError, match="genetic phenotype is inconsistent"):
        _spec(world=world, architecture=architecture).compile()
