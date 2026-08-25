"""Represent mutable domain-neutral simulation run state."""

from __future__ import annotations

import copy
import random
from typing import Any

import attrs

from evo_engine.engine.simulation_context import SimulationContext
from evo_engine.telemetry import StepTelemetry
from evo_engine.validation import attrs_validators


def _validate_world(
    instance: object, attribute: attrs.Attribute, value: object
) -> None:
    """Require transactional model state to provide a copy operation."""
    if not callable(getattr(value, "copy", None)):
        raise TypeError(
            f"{attribute.name} must provide a callable copy method for transactions."
        )


@attrs.define(slots=True, kw_only=True, init=False)
class SimulationState:
    """Represent one transactional snapshot of an arbitrary simulated system.

    ``world`` is intentionally domain-neutral. The kernel requires only that it
    can be copied transactionally. Domain packages define the concrete state
    carried there and the operations that processes may perform on it.

    ``context`` contains immutable configuration services shared by reference
    across copies. The kernel assigns no biological or other domain semantics to
    those values.

    Attributes:
        world: Current domain-defined model state.
        context: Immutable configuration shared across transactional copies.
        step_index: Index of the current committed simulation state.
        rng: Random number generator owned by the simulation.
        last_step_telemetry: Telemetry for the most recently committed step.
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
        """Initialize mutable state and domain-neutral shared configuration.

        Arbitrary keyword arguments are normalized into context services when a
        prebuilt context is not supplied. This keeps the kernel agnostic to the
        meaning of domain configuration while allowing domain packages to use
        explicit, stable service names.

        Args:
            world: Current domain-defined model state. Must provide ``copy``.
            context: Optional complete immutable simulation context.
            step_index: Current simulation step index.
            rng: Simulation random-number generator. Defaults to a new generator.
            last_step_telemetry: Most recently committed step telemetry.
            **context_values: Named domain configuration services used only when
                ``context`` is omitted.

        Raises:
            TypeError: If a context and separate context values are both given.
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

    def __getattr__(self, name: str) -> Any:
        """Resolve domain configuration through the generic context service map.

        This compatibility surface lets existing domain code access a configured
        service as ``state.<service_name>`` without teaching the kernel what the
        service means. New domain code should prefer ``state.context.require``
        with stable namespaced service identifiers.
        """
        try:
            return self.context.require(name)
        except KeyError as error:
            raise AttributeError(name) from error

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
