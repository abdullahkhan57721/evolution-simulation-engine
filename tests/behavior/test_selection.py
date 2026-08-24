"""Tests for organism-level behavior selection models."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    EXPLORATION,
    REPRODUCTION,
    SOMATIC_INVESTMENT,
    SURVIVAL,
    BehaviorSelectionModel,
    EnergyConservationBehavior,
    UnrestrictedBehavior,
    behavior_is_allowed,
)
from evo_engine.engine import Simulation
from evo_engine.world import Organism, WorldState
from tests.helpers import add_organism, make_empty_architecture


def _simulation_with_energy(
    energy: int,
    *,
    behavior_selection_model: BehaviorSelectionModel,
) -> tuple[Simulation, Organism]:
    architecture = make_empty_architecture()
    simulation = Simulation(
        initial_world_state=WorldState(
            width=3,
            height=3,
        ),
        genetic_architecture=architecture,
        behavior_selection_model=behavior_selection_model,
    )
    organism = add_organism(
        simulation.state,
        energy=energy,
    )
    return simulation, organism


def test_unrestricted_behavior_allows_every_purpose() -> None:
    """Test default behavior selection preserves unrestricted behavior."""
    simulation, organism = _simulation_with_energy(
        0,
        behavior_selection_model=UnrestrictedBehavior(),
    )

    for purpose in (
        ENERGY_ACQUISITION,
        SURVIVAL,
        SOMATIC_INVESTMENT,
        REPRODUCTION,
        EXPLORATION,
        "thermoregulation",
    ):
        assert behavior_is_allowed(
            organism,
            behavioral_purpose=purpose,
            simulation_state=simulation.state,
        )


def test_energy_conservation_allows_all_behavior_at_threshold() -> None:
    """Test conservation mode activates only below the configured threshold."""
    simulation, organism = _simulation_with_energy(
        10,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )

    assert behavior_is_allowed(
        organism,
        behavioral_purpose=REPRODUCTION,
        simulation_state=simulation.state,
    )
    assert behavior_is_allowed(
        organism,
        behavioral_purpose=SOMATIC_INVESTMENT,
        simulation_state=simulation.state,
    )


def test_energy_conservation_suppresses_nonessential_low_energy_behavior() -> None:
    """Test low energy preserves acquisition/survival and suppresses investment."""
    simulation, organism = _simulation_with_energy(
        9,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
        ),
    )

    assert behavior_is_allowed(
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=simulation.state,
    )
    assert behavior_is_allowed(
        organism,
        behavioral_purpose=SURVIVAL,
        simulation_state=simulation.state,
    )
    assert not behavior_is_allowed(
        organism,
        behavioral_purpose=SOMATIC_INVESTMENT,
        simulation_state=simulation.state,
    )
    assert not behavior_is_allowed(
        organism,
        behavioral_purpose=REPRODUCTION,
        simulation_state=simulation.state,
    )
    assert not behavior_is_allowed(
        organism,
        behavioral_purpose=EXPLORATION,
        simulation_state=simulation.state,
    )


def test_energy_conservation_supports_custom_allowed_purposes() -> None:
    """Test simulations may preserve custom purposes during conservation mode."""
    simulation, organism = _simulation_with_energy(
        1,
        behavior_selection_model=EnergyConservationBehavior(
            energy_threshold=10,
            allowed_low_energy_purposes=frozenset({"thermoregulation"}),
        ),
    )

    assert behavior_is_allowed(
        organism,
        behavioral_purpose="thermoregulation",
        simulation_state=simulation.state,
    )
    assert not behavior_is_allowed(
        organism,
        behavioral_purpose=ENERGY_ACQUISITION,
        simulation_state=simulation.state,
    )


@pytest.mark.parametrize(
    "energy_threshold",
    [
        -1,
        True,
        1.0,
        "1",
    ],
)
def test_energy_conservation_rejects_invalid_thresholds(
    energy_threshold: object,
) -> None:
    """Test conservation thresholds are nonnegative integers."""
    with pytest.raises((TypeError, ValueError)):
        EnergyConservationBehavior(
            energy_threshold=cast(int, energy_threshold),
        )


def test_energy_conservation_requires_frozenset_of_allowed_purposes() -> None:
    """Test low-energy purpose collections use the immutable public contract."""
    with pytest.raises(TypeError):
        EnergyConservationBehavior(
            energy_threshold=10,
            allowed_low_energy_purposes=cast(
                frozenset[str],
                {ENERGY_ACQUISITION},
            ),
        )


@pytest.mark.parametrize(
    "purpose",
    [
        "",
        " ",
        1,
    ],
)
def test_energy_conservation_rejects_invalid_allowed_purposes(
    purpose: object,
) -> None:
    """Test every configured low-energy purpose is a nonblank string."""
    with pytest.raises((TypeError, ValueError)):
        EnergyConservationBehavior(
            energy_threshold=10,
            allowed_low_energy_purposes=frozenset({cast(str, purpose)}),
        )


def test_behavior_selection_protocol_accepts_structural_implementation() -> None:
    """Test custom selectors need not inherit from engine classes."""

    class CustomSelection:
        def allows_behavior(
            self,
            organism,
            *,
            behavioral_purpose,
            simulation_state,
        ) -> bool:
            return behavioral_purpose == SURVIVAL

    assert isinstance(CustomSelection(), BehaviorSelectionModel)


def test_behavior_selection_helper_rejects_non_boolean_decision() -> None:
    """Test process boundaries enforce the selector's Boolean return contract."""

    class InvalidSelection:
        def allows_behavior(
            self,
            organism,
            *,
            behavioral_purpose,
            simulation_state,
        ):
            return 1

    simulation, organism = _simulation_with_energy(
        10,
        behavior_selection_model=cast(BehaviorSelectionModel, InvalidSelection()),
    )

    with pytest.raises(TypeError, match="must return a Boolean"):
        behavior_is_allowed(
            organism,
            behavioral_purpose=ENERGY_ACQUISITION,
            simulation_state=simulation.state,
        )
