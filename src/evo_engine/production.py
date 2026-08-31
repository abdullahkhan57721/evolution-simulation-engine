"""Domain-neutral contracts for producing entities from determined state.

Production is intentionally separate from state propagation. A propagation
model decides what state a prospective participant receives; a production
model turns already-determined state into a concrete simulation entity. This
keeps transfer semantics independent from entity construction semantics.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

ProductionStateT = TypeVar("ProductionStateT", contravariant=True)
ProductionSourceT = TypeVar("ProductionSourceT", contravariant=True)
ProductionContextT = TypeVar("ProductionContextT", contravariant=True)
ProducedEntityT = TypeVar("ProducedEntityT", covariant=True)


class EntityProductionModel(
    Protocol[
        ProductionStateT,
        ProductionSourceT,
        ProductionContextT,
        ProducedEntityT,
    ]
):
    """Produce a concrete entity from already-determined state."""

    def produce(
        self,
        state: ProductionStateT,
        *,
        source_entities: tuple[ProductionSourceT, ...],
        context: ProductionContextT,
        rng: random.Random,
    ) -> ProducedEntityT:
        """Return a fully materialized entity.

        Args:
            state: State already determined for the entity being produced.
            source_entities: Zero or more domain-specific source entities that
                production may consult. Production does not determine their
                transmissible contribution; propagation has already done so.
            context: Domain-specific production configuration or simulation
                context.
            rng: Random-number generator owned by the simulation.

        Returns:
            Fully materialized entity ready for domain-specific insertion.
        """
        ...
