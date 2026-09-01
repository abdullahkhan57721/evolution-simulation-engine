"""Represent one domain-neutral simulation and its mutable state."""

from __future__ import annotations

import random

from evo_engine.context import SimulationContext
from evo_engine.engine.simulation_state import SimulationState


class Simulation:
    """Represent one simulation independently of any modeled domain.

    The kernel knows only about transactional domain state, immutable context,
    deterministic RNG ownership, and simulation-step state. Domain packages are
    responsible for defining entities, modeled semantics, and configuration
    services stored in ``SimulationContext``.

    Named context values accepted during construction are normalized into the
    immutable context. They are never exposed as dynamic ``Simulation`` or
    ``SimulationState`` attributes.
    """

    def __init__(
        self,
        initial_domain_state: object,
        seed: int | None = None,
        context: SimulationContext | None = None,
        **context_values: object,
    ) -> None:
        """Initialize a simulation from arbitrary copyable domain state.

        Args:
            initial_domain_state: Initial domain-defined state. Must provide a
                callable ``copy`` method for transactional isolation.
            seed: Seed for the simulation random-number generator.
            context: Optional immutable shared simulation context.
            **context_values: Optional named configuration services. These may be
                supplied only when ``context`` is omitted.
        """
        copy_domain_state = getattr(initial_domain_state, "copy", None)
        if not callable(copy_domain_state):
            raise TypeError(
                "initial_domain_state must provide a callable copy method."
            )
        if type(seed) is bool or (seed is not None and type(seed) is not int):
            raise TypeError("seed must be an integer or None, not a Boolean.")
        if context is not None and context_values:
            raise TypeError("context cannot be combined with separate context values.")
        if context is None:
            context = SimulationContext.from_mapping(context_values)

        domain_state = copy_domain_state()
        self.state = SimulationState(
            domain_state=domain_state,
            context=context,
            rng=random.Random(seed),
        )

    @property
    def context(self) -> SimulationContext:
        """Return immutable configuration shared by all state snapshots."""
        return self.state.context
