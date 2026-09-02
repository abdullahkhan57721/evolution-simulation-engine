"""General contracts specific to evolutionary systems.

These abstractions describe evolutionary semantics such as transmissible-state
expression and variation. Domain-neutral state propagation lives separately in
``evo_engine.propagation`` so the simulator can also represent non-hereditary,
non-parental, and non-biological state transfer.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

ExpressionInputT = TypeVar("ExpressionInputT", contravariant=True)
ExpressionOutputT = TypeVar("ExpressionOutputT", covariant=True)
VariationValueT = TypeVar("VariationValueT")


class TransmissibleStateExpression(Protocol[ExpressionInputT, ExpressionOutputT]):
    """Map transmissible information to expressed operative characteristics."""

    def express(
        self,
        transmissible_state: ExpressionInputT,
        /,
    ) -> ExpressionOutputT:
        """Return expressed state derived from transmissible state.

        Args:
            transmissible_state: Information carried by the evolving entity.

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
