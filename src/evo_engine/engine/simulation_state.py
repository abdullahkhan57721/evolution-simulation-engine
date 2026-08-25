"""Represent mutable simulation run state."""

from __future__ import annotations

import copy
import random

import attrs

from evo_engine.behavior import BehaviorSelectionModel
from evo_engine.engine.simulation_context import SimulationContext
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.telemetry import StepTelemetry
from evo_engine.validation import attrs_validators
from evo_engine.world.world_state import WorldState


@attrs.define(slots=True, kw_only=True, init=False)
class SimulationState:
    """Represent mutable state for one transactional simulation snapshot.

    ``SimulationContext`` contains immutable configuration shared across state
    copies. Mutable world, RNG, step index, and telemetry remain state. The
    constructor retains the previous ``genetic_architecture`` and
    ``behavior_selection_model`` arguments for source compatibility while also
    accepting an already-built context.

    Attributes:
        world: Current state of the simulated world.
        context: Immutable configuration shared across transactional copies.
        step_index: Index of the current simulation state.
        rng: Random number generator for the simulation.
        last_step_telemetry: Telemetry for the most recently committed step.
    """

    world: WorldState = attrs.field(
        validator=attrs.validators.instance_of(WorldState),
    )
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
        world: WorldState,
        context: SimulationContext | None = None,
        genetic_architecture: GeneticArchitecture | None = None,
        behavior_selection_model: BehaviorSelectionModel | None = None,
        step_index: int = 0,
        rng: random.Random | None = None,
        last_step_telemetry: StepTelemetry | None = None,
    ) -> None:
        """Initialize mutable state with shared simulation configuration.

        Args:
            world: Current state of the simulated world.
            context: Optional complete immutable simulation context.
            genetic_architecture: Backward-compatible architecture argument used
                to construct ``context`` when one is not supplied.
            behavior_selection_model: Optional backward-compatible behavior
                policy used when constructing ``context``.
            step_index: Current simulation step index.
            rng: Simulation random-number generator. Defaults to a new generator.
            last_step_telemetry: Most recently committed step telemetry.

        Raises:
            TypeError: If required configuration is missing or both a context
                and legacy context-construction arguments are supplied.
        """
        resolved_context = self._resolve_context(
            context=context,
            genetic_architecture=genetic_architecture,
            behavior_selection_model=behavior_selection_model,
        )
        if rng is None:
            rng = random.Random()

        object.__setattr__(self, "world", world)
        object.__setattr__(self, "context", resolved_context)
        object.__setattr__(self, "step_index", step_index)
        object.__setattr__(self, "rng", rng)
        object.__setattr__(self, "last_step_telemetry", last_step_telemetry)
        attrs.validate(self)

    @staticmethod
    def _resolve_context(
        *,
        context: SimulationContext | None,
        genetic_architecture: GeneticArchitecture | None,
        behavior_selection_model: BehaviorSelectionModel | None,
    ) -> SimulationContext:
        """Return one unambiguous immutable simulation context."""
        if context is not None:
            if genetic_architecture is not None or behavior_selection_model is not None:
                raise TypeError(
                    "context cannot be combined with genetic_architecture or "
                    "behavior_selection_model."
                )
            return context

        if genetic_architecture is None:
            raise TypeError(
                "genetic_architecture is required when context is not supplied."
            )
        if behavior_selection_model is None:
            return SimulationContext(genetic_architecture=genetic_architecture)
        return SimulationContext(
            genetic_architecture=genetic_architecture,
            behavior_selection_model=behavior_selection_model,
        )

    @property
    def genetic_architecture(self) -> GeneticArchitecture:
        """Return the shared genetic architecture from simulation context."""
        return self.context.genetic_architecture

    @property
    def behavior_selection_model(self) -> BehaviorSelectionModel:
        """Return the shared behavior-selection model from simulation context."""
        return self.context.behavior_selection_model

    def copy(self) -> SimulationState:
        """Return an independent transactional copy of the simulation state.

        Mutable world and RNG state are copied. Immutable ``context`` is shared
        by reference. Previous committed telemetry is intentionally not copied
        into the new working transaction.

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
