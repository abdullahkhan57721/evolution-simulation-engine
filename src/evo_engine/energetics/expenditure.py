"""Policies that determine whether organisms may spend energy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class EnergyExpenditurePolicy(Protocol):
    """Decide whether an organism may pay a proposed energy cost."""

    def can_spend(
        self,
        organism: Organism,
        *,
        energy_cost: int,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism may pay a proposed energy cost.

        Args:
            organism: Organism considering the expenditure.
            energy_cost: Non-negative energy cost of the proposed action.
            simulation_state: Current simulation state.

        Returns:
            Whether the expenditure is permitted.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class SpendToZero:
    """Allow expenditures that do not exceed current organism energy."""

    def can_spend(
        self,
        organism: Organism,
        *,
        energy_cost: int,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether current energy fully covers the proposed cost.

        Args:
            organism: Organism considering the expenditure.
            energy_cost: Energy cost of the proposed action.
            simulation_state: Current simulation state.

        Returns:
            ``True`` when the cost can be paid, including when payment leaves
            exactly zero energy.
        """
        return organism.energy >= energy_cost


@attrs.frozen(slots=True, kw_only=True)
class KeepFixedReserve:
    """Prevent positive expenditures from reducing energy below a fixed reserve.

    Zero-cost actions are always permitted because they do not further deplete
    an organism that may already be below the configured reserve.

    Attributes:
        minimum_energy: Minimum organism energy that must remain after a
            positive expenditure.
    """

    minimum_energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def can_spend(
        self,
        organism: Organism,
        *,
        energy_cost: int,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether payment preserves the configured energy reserve.

        Args:
            organism: Organism considering the expenditure.
            energy_cost: Energy cost of the proposed action.
            simulation_state: Current simulation state.

        Returns:
            ``True`` for zero-cost actions or when a positive payment leaves at
            least ``minimum_energy``.
        """
        return (
            energy_cost == 0
            or organism.energy - energy_cost >= self.minimum_energy
        )


def energy_expenditure_is_allowed(
    energy_expenditure_policy: EnergyExpenditurePolicy,
    organism: Organism,
    *,
    energy_cost: int,
    simulation_state: SimulationState,
) -> bool:
    """Return a validated energy-expenditure decision.

    Args:
        energy_expenditure_policy: Policy deciding whether the cost may be paid.
        organism: Organism considering the expenditure.
        energy_cost: Proposed non-negative energy cost.
        simulation_state: Current simulation state.

    Returns:
        Validated policy decision.

    Raises:
        TypeError: If ``energy_cost`` is not an integer or the policy does not
            return a Boolean.
        ValueError: If ``energy_cost`` is negative.
    """
    validated_cost = validators.validate_int_ge(
        energy_cost,
        bound=0,
        name="energy_cost",
    )
    decision = energy_expenditure_policy.can_spend(
        organism,
        energy_cost=validated_cost,
        simulation_state=simulation_state,
    )

    if type(decision) is not bool:
        raise TypeError("energy_expenditure_policy.can_spend must return a Boolean.")

    return decision
