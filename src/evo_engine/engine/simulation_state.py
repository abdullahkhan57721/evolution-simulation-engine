"""Represent mutable domain-neutral simulation run state."""

from __future__ import annotations

import random
from typing import Any

import attrs

from evo_engine.context import SimulationContext
from evo_engine.telemetry import StepTelemetry
from evo_engine.validation import attrs_validators


def _validate_world(
    instance: object, attribute: attrs.Attribute, value: object
) -> None:
    """Require transactional model state to provide a copy operation."""
    del instance
    if not callable(getattr(value, "copy", None)):
        raise TypeError(
            f"{attribute.name} must provide a callable copy method for transactions."
        )


@attrs.define(slots=True, kw_only=True, init=False)
class SimulationState:
    """Represent one transactional snapshot of an arbitrary simulated system.

    ``world`` is domain-neutral simulation terminology: it may hold any
    domain-defined copyable model state, not necessarily a physical or biological
    world. Domain packages define the concrete state and operations carried there.

    ``context`` contains immutable configuration services shared by reference
    across copies. Configuration is consumed explicitly through
    ``state.context.require(...)`` rather than dynamic state attributes.

    Named ``context_values`` are construction sugar only: they are normalized
    into a ``SimulationContext`` and never become attributes on the state.
    """

    world: Any = attrs.field(validator=_validate_world)
    context: SimulationContext = attrs.field(
        validator=attrs.validators.instance_of(SimulationContext),
        on_setattr=attrs.setters.frozen,
    )
    step_index: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    rng: random.Random = attrs.field(
        factory=random.Random,
        validator=attrs.validators.instance_of(random.Random),
        repr=False,
    )
    last_step_telemetry: StepTelemetry | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(StepTelemetry)
        ),
    )

    def __init__(
        self,
        *,
        world: object,
        context: SimulationContext | None = None,
        step_index: int = 0,
        rng: random.Random | None = None,
        last_step_telemetry: StepTelemetry | None = None,
        **context_values: object,
    ) -> None:
        """Initialize mutable state and normalize optional named context values.

        Args:
            world: Current domain-defined model state. Must provide ``copy``.
            context: Optional complete immutable simulation context.
            step_index: Current simulation step index.
            rng: Simulation random-number generator. Defaults to a new generator.
            last_step_telemetry: Most recently committed step telemetry.
            **context_values: Optional named configuration services. These may be
                supplied only when ``context`` is omitted.
        """
        if context is not None and context_values:
            raise TypeError("context cannot be combined with separate context values.")
        if context is None:
            context = SimulationContext.from_mapping(context_values)
        if rng is None:
            rng = random.Random()

        object.__setattr__(self, "world", world)
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "step_index", step_index)
        object.__setattr__(self, "rng", rng)
        object.__setattr__(self, "last_step_telemetry", last_step_telemetry)
        attrs.validate(self)

    def copy(self) -> SimulationState:
        """Return an independent transactional copy of the simulation state."""
        # setstate() replaces the complete generator state, so skip the seed work
        # performed by Random.__init__ before that state would be discarded.
        copied_rng = random.Random.__new__(random.Random)
        copied_rng.setstate(self.rng.getstate())
        return SimulationState(
            world=self.world.copy(),
            context=self.context,
            step_index=self.step_index,
            rng=copied_rng,
            last_step_telemetry=None,
        )
