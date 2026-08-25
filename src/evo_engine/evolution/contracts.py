"""Domain-neutral contracts for evolutionary systems.

The contracts in this module intentionally avoid biological vocabulary. They
capture the minimum reusable semantics needed by evolutionary systems: entities
carry heritable state, inherited state may be expressed into operative state,
variation may alter transmitted information, and transmission constructs new
heritable state from one or more contributors.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

EntityHeritableStateT = TypeVar("EntityHeritableStateT", covariant=True)
ExpressionInputT = TypeVar("ExpressionInputT", contravariant=True)
ExpressionOutputT = TypeVar("ExpressionOutputT", covariant=True)
VariationValueT = TypeVar("VariationValueT")
TransmissionStateT = TypeVar("TransmissionStateT")
TransmissionContextT = TypeVar("TransmissionContextT", contravariant=True)


class EvolutionaryEntity(Protocol[EntityHeritableStateT]):
    """Expose the heritable state carried by an evolving entity."""

    @property
    def heritable_state(self) -> EntityHeritableStateT:
        """Return the entity state that may be transmitted to descendants."""
        ...


class HeritableStateExpression(Protocol[ExpressionInputT, ExpressionOutputT]):
    """Map heritable information to expressed operative characteristics."""

    def express(self, heritable_state: ExpressionInputT) -> ExpressionOutputT:
        """Return expressed state derived from heritable state.

        Args:
            heritable_state: Information carried by the evolving entity.

        Returns:
            Expressed characteristics derived from that information.
        """
        ...


class VariationOperator(Protocol[VariationValueT]):
    """Apply stochastic or deterministic variation to transmissible state."""

    def vary(
        self,
        value: VariationValueT,
        *,
        rng: random.Random,
    ) -> VariationValueT:
        """Return a varied or unchanged value.

        Args:
            value: Existing transmissible value.
            rng: Random-number generator owned by the simulation.

        Returns:
            Varied or unchanged value.
        """
        ...


class TransmissionModel(Protocol[TransmissionStateT, TransmissionContextT]):
    """Construct descendant heritable state from contributing parent states."""

    @property
    def contributor_count(self) -> int:
        """Return the number of required contributing parent states."""
        ...

    def transmit(
        self,
        parent_states: tuple[TransmissionStateT, ...],
        *,
        context: TransmissionContextT,
        rng: random.Random,
    ) -> TransmissionStateT:
        """Return descendant heritable state.

        Args:
            parent_states: Heritable states contributing to the descendant.
            context: Domain-specific immutable transmission configuration.
            rng: Random-number generator owned by the simulation.

        Returns:
            Descendant heritable state.
        """
        ...
