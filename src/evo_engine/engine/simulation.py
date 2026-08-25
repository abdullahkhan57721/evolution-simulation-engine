"""Represent one domain-neutral simulation and its mutable state."""

from __future__ import annotations

import random
from typing import Any

from evo_engine.engine.simulation_context import SimulationContext
from evo_engine.engine.simulation_state import SimulationState


class Simulation:
    """Represent one simulation independently of any modeled domain.

    The kernel knows only about transactional model state, immutable context,
    deterministic RNG ownership, and simulation-step state. Domain packages are
    responsible for defining entities, evolutionary semantics, and configuration
    services stored in ``SimulationContext``.
    """

    def __init__(
        self,
        initial_world_state: object,
        seed: int | None = None,
        context: SimulationContext | None = None,
        **context_values: object,
    ) -> None:
        """Initialize a simulation from arbitrary copyable model state.

        Args:
            initial_world_state: Initial domain-defined state. Must provide a
                callable ``copy`` method for transactional isolation.
            seed: Seed for the simulation random-number generator.
            context: Optional immutable shared simulation context.
            **context_values: Named domain configuration services used to build
                the context when ``context`` is omitted.

        Raises:
            TypeError: If the state is not copyable, the seed is invalid, or a
                context is combined with separate context values.
        """
        copy_world = getattr(initial_world_state, "copy", None)
        if not callable(copy_world):
            raise TypeError("initial_world_state must provide a callable copy method.")
        if type(seed) is bool or (seed is not None and type(seed) is not int):
            raise TypeError("seed must be an integer or None, not a Boolean.")
        if context is not None and context_values:
            raise TypeError("context cannot be combined with separate context values.")
        if context is None:
            context = SimulationContext.from_mapping(context_values)

        # Caller-owned state is configuration input, never authoritative mutable
        # simulation state.
        world = copy_world()
        self.state = SimulationState(
            world=world,
            context=context,
            rng=random.Random(seed),
        )

    @property
    def context(self) -> SimulationContext:
        """Return immutable configuration shared by all state snapshots."""
        return self.state.context

    def __getattr__(self, name: str) -> Any:
        """Resolve domain configuration from the generic context service map."""
        try:
            return self.context.require(name)
        except KeyError as error:
            raise AttributeError(name) from error
