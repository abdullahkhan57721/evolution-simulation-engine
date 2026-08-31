"""Domain-neutral contracts for propagating state between simulation participants.

Propagation is intentionally broader than biological inheritance. A propagation
model receives zero or more source states, a recipient, immutable domain
context, and the simulation-owned random-number generator. The generic contract
places no restriction on source count or on the relationship between sources
and recipient.
"""

from __future__ import annotations

import random
from typing import Protocol, TypeVar

TransmissibleStateT = TypeVar("TransmissibleStateT", covariant=True)
PropagationStateT = TypeVar("PropagationStateT")
PropagationRecipientT = TypeVar("PropagationRecipientT", contravariant=True)
PropagationContextT = TypeVar("PropagationContextT", contravariant=True)


class TransmissibleStateCarrier(Protocol[TransmissibleStateT]):
    """Expose state that may propagate to another simulation participant."""

    @property
    def transmissible_state(self) -> TransmissibleStateT:
        """Return state available to propagation models."""
        ...


class PropagationModel(
    Protocol[PropagationStateT, PropagationRecipientT, PropagationContextT]
):
    """Construct propagated state from arbitrary source states for a recipient."""

    def propagate(
        self,
        source_states: tuple[PropagationStateT, ...],
        *,
        recipient: PropagationRecipientT,
        context: PropagationContextT,
        rng: random.Random,
    ) -> PropagationStateT:
        """Return state propagated to a recipient.

        Args:
            source_states: Zero or more states contributing to propagation.
            recipient: Domain-specific propagation recipient or recipient
                descriptor. Models may ignore it when propagation is
                recipient-independent.
            context: Domain-specific immutable propagation configuration.
            rng: Random-number generator owned by the simulation.

        Returns:
            State produced for the recipient.
        """
        ...
