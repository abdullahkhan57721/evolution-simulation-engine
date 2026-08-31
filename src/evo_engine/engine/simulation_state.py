"""Represent mutable domain-neutral simulation run state."""

from __future__ import annotations

import copy
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


@attrs.define(slots=True, kw_only=True)
class SimulationState:
    """Represent one transactional snapshot of an arbitrary simulated system.

    ``world`` is domain-neutral simulation terminology: it may hold any
    domain-defined copyable model state, not necessarily a physical or biological
    world. Domain packages define the concrete state and operations carried there.

    ``context`` contains immutable configuration services shared by reference
    across copies. Configuration is accessed explicitly through
    ``state.context.require(...)`` rather than dynamic state attributes.

    Attributes:
        world: Current domain-defined model state.
        context: Immutable configuration shared across transactional copies.
        step_index: Index of the current committed simulation state.
        rng: Random number generator owned by the simulation.
        last_step_telemetry: Telemetry for the most recently committed step.
    """

    world: Any = attrs.field(validator=_validate_world)
    context: SimulationContext = attrs.field(
        factory=SimulationContext,
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

    def copy(self) -> SimulationState:
        """Return an independent transactional copy of the simulation state.

        Domain state and RNG state are copied. Immutable ``context`` is shared by
        reference. Previous committed telemetry is intentionally excluded from
        the new working transaction.

        Returns:
            Independent working simulation state.
        """
        return SimulationState(
            world=self.world.copy(),
            context=self.context,
            step_index=self.step_index,
            rng=copy.deepcopy(self.rng),
            last_step_telemetry=None,
        )
