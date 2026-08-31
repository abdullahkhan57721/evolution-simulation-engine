"""General contracts specific to evolutionary systems.

These abstractions describe evolutionary semantics such as heritable state,
expression, and variation. Domain-neutral state propagation lives separately in
``evo_engine.propagation`` so the simulator can also represent non-hereditary,
non-parental, and non-biological state transfer.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

EntityHeritableStateT = TypeVar("EntityHeritableStateT", covariant=True)
ExpressionInputT = TypeVar("ExpressionInputT", contravariant=True)
ExpressionOutputT = TypeVar("ExpressionOutputT", covariant=True)
VariationValueT = TypeVar("VariationValueT")


class EvolutionaryEntity(Protocol[EntityHeritableStateT]):
    """Expose the heritable state carried by an evolving entity."""

    @property
    def heritable_state(self) -> EntityHeritableStateT:
        """Return the entity state that may be inherited by descendants."""
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
