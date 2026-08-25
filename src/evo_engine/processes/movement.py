"""Movement simulation process."""

from __future__ import annotations

import attrs

from evo_engine.behavior import (
    EXPLORATION,
    FixedMovementIntent,
    MovementIntentModel,
    MovementTarget,
    MovementTargetModel,
    NoMovementTarget,
    behavior_is_allowed,
    determine_movement_purpose,
    determine_movement_target,
    validate_behavioral_purpose,
)
from evo_engine.characteristics import (
    GeneticPhenotypeCharacteristics,
    integer_characteristic,
)
from evo_engine.energetics import (
    EnergyExpenditurePolicy,
    SpendToZero,
    energy_expenditure_is_allowed,
)
from evo_engine.energetics.locomotion import LocomotionCostModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import MAX_SPEED
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.spatial.boundary_conditions import BoundaryCondition
from evo_engine.spatial.movement_patterns import MovementPattern
from evo_engine.spatial.targeted_movement import (
    StraightLineTowardTarget,
    TargetedMovementModel,
)
from evo_engine.validation import attrs_validators, validators


def _validate_event_behavioral_purpose(
    instance: object,
    attribute: attrs.Attribute,
    value: object,
) -> None:
    """Validate a Movement event's recorded behavioral purpose."""
    validate_behavioral_purpose(
        value,
        name=attribute.name,
    )


@attrs.frozen(slots=True, kw_only=True)
class Movement:
    """Represent the Movement simulation process.

    ``max_speed`` is interpreted as maximum Euclidean grid-distance per
    timestep. The configurable ``max_speed_source`` determines whether that
    operative capability comes from raw genetic expression, realized
    development, or another characteristic representation.

    Movement has no single generic behavioral purpose. The configured
    ``movement_intent_model`` determines why each organism is attempting to
    move, and behavior selection is consulted before target selection,
    displacement RNG, boundary resolution, or energetic pricing occurs.

    A ``movement_target_model`` may select an ecological target for an allowed
    movement attempt. Targeted attempts use ``targeted_movement_model``;
    attempts without a selected target fall back to ``movement_pattern``.

    Locomotion is voluntary energy expenditure. The configured
    ``energy_expenditure_policy`` decides whether the fully priced movement may
    be paid. The default ``SpendToZero`` allows an affordable movement to spend
    the organism to exactly zero energy, but does not allow a full movement
    whose cost exceeds available energy.

    Attributes:
        movement_pattern: Pattern used for untargeted movement displacements.
        boundary_condition: Rule used to resolve world-boundary crossings.
        locomotion_cost_model: Model used to calculate movement energy cost.
        max_speed_source: Operative characteristic source for ``max_speed``.
        energy_expenditure_policy: Policy deciding whether the organism may pay
            the locomotion cost.
        movement_intent_model: Model determining the behavioral purpose of each
            organism's movement attempt.
        movement_target_model: Model selecting an optional spatial target for
            each movement attempt.
        targeted_movement_model: Model choosing displacement toward a selected
            movement target.
    """

    movement_pattern: MovementPattern
    boundary_condition: BoundaryCondition
    locomotion_cost_model: LocomotionCostModel
    max_speed_source: object = attrs.field(factory=GeneticPhenotypeCharacteristics)
    energy_expenditure_policy: EnergyExpenditurePolicy = attrs.field(
        factory=SpendToZero,
    )
    movement_intent_model: MovementIntentModel = attrs.field(
        factory=FixedMovementIntent,
    )
    movement_target_model: MovementTargetModel = attrs.field(
        factory=NoMovementTarget,
    )
    targeted_movement_model: TargetedMovementModel = attrs.field(
        factory=StraightLineTowardTarget,
    )

    def __attrs_post_init__(self) -> None:
        """Validate Movement configuration."""
        if not callable(getattr(self.max_speed_source, "value_for", None)):
            raise TypeError(
                "max_speed_source must provide a callable value_for method."
            )

        required_methods = (
            (
                self.energy_expenditure_policy,
                "can_spend",
                "energy_expenditure_policy",
            ),
            (
                self.movement_intent_model,
                "determine_purpose",
                "movement_intent_model",
            ),
            (
                self.movement_target_model,
                "choose_target",
                "movement_target_model",
            ),
            (
                self.targeted_movement_model,
                "choose_displacement",
                "targeted_movement_model",
            ),
        )

        for model, method_name, field_name in required_methods:
            if not callable(getattr(model, method_name, None)):
                raise TypeError(
                    f"{field_name} must provide a callable {method_name} method."
                )

    @property
    def required_characteristics(self) -> frozenset[str]:
        """Return operative characteristics required directly by movement."""
        return frozenset({MAX_SPEED})

    @property
    def required_traits(self) -> frozenset[str]:
        """Return biological traits required by movement and its policies."""
        return self.required_characteristics | collect_required_traits(
            self.movement_pattern,
            self.boundary_condition,
            self.locomotion_cost_model,
            self.energy_expenditure_policy,
            self.movement_intent_model,
            self.movement_target_model,
            self.targeted_movement_model,
        )

    @property
    def event_type(self) -> type[Movement.Event]:
        """Return the Movement event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Movement event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the organism being moved.
            dx: Attempted horizontal displacement.
            dy: Attempted vertical displacement.
            new_x: Resolved horizontal destination.
            new_y: Resolved vertical destination.
            energy_cost: Energy charged for the attempted displacement.
            behavioral_purpose: Purpose that motivated this movement attempt.
            target_x: Selected target's horizontal coordinate, if any.
            target_y: Selected target's vertical coordinate, if any.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        dx: int = attrs.field(
            validator=attrs_validators.validate_int,
        )
        dy: int = attrs.field(
            validator=attrs_validators.validate_int,
        )
        new_x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        new_y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        energy_cost: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        behavioral_purpose: str = attrs.field(
            default=EXPLORATION,
            validator=_validate_event_behavioral_purpose,
        )
        target_x: int | None = attrs.field(
            default=None,
            validator=attrs.validators.optional(
                attrs_validators.validate_int_ge(0),
            ),
        )
        target_y: int | None = attrs.field(
            default=None,
            validator=attrs.validators.optional(
                attrs_validators.validate_int_ge(0),
            ),
        )

        def __attrs_post_init__(self) -> None:
            """Validate that optional target coordinates are recorded together."""
            if (self.target_x is None) != (self.target_y is None):
                raise ValueError(
                    "Movement.Event target_x and target_y must both be set or both be None."
                )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Movement.Event]:
        """Propose behaviorally selected and energetically permitted movement.

        Each organism's movement intent is determined first. If behavior
        selection suppresses that purpose, no target selection, movement RNG,
        boundary resolution, or locomotion pricing occurs for the organism.

        For selected attempts, operative ``max_speed`` limits displacement
        magnitude. An optional ecological target is selected next. Targeted
        attempts use the targeted-movement policy; untargeted attempts use the
        ordinary movement pattern. The locomotion model determines the cost,
        and the expenditure policy must permit payment before an event is
        recorded.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Movement events.

        Raises:
            TypeError: If a configured policy violates its return contract.
            ValueError: If an intent is blank, a target lies outside the world,
                a movement policy exceeds max speed, or a cost model returns a
                negative cost.
        """
        events: list[Movement.Event] = []
        world = simulation_state.world

        for organism in world.organisms.values():
            behavioral_purpose = determine_movement_purpose(
                self.movement_intent_model,
                organism,
                simulation_state=simulation_state,
            )

            if not behavior_is_allowed(
                organism,
                behavioral_purpose=behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            max_speed = integer_characteristic(
                self.max_speed_source,
                organism,
                MAX_SPEED,
                context=simulation_state,
                minimum=0,
            )

            target = determine_movement_target(
                self.movement_target_model,
                organism,
                behavioral_purpose=behavioral_purpose,
                simulation_state=simulation_state,
            )
            dx, dy = self._choose_displacement(
                simulation_state=simulation_state,
                organism_x=organism.x,
                organism_y=organism.y,
                max_speed=max_speed,
                target=target,
            )
            self._validate_displacement(
                dx=dx,
                dy=dy,
                max_speed=max_speed,
            )

            energy_cost = self.locomotion_cost_model.calculate_cost(
                organism,
                dx=dx,
                dy=dy,
                simulation_state=simulation_state,
            )
            validators.validate_int_ge(
                energy_cost,
                bound=0,
                name="locomotion energy cost",
            )

            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                organism,
                energy_cost=energy_cost,
                simulation_state=simulation_state,
            ):
                continue

            proposed_x = organism.x + dx
            proposed_y = organism.y + dy

            new_x, new_y = self.boundary_condition.resolve(
                current_x=organism.x,
                current_y=organism.y,
                proposed_x=proposed_x,
                proposed_y=proposed_y,
                width=world.width,
                height=world.height,
            )

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                    dx=dx,
                    dy=dy,
                    new_x=new_x,
                    new_y=new_y,
                    energy_cost=energy_cost,
                    behavioral_purpose=behavioral_purpose,
                    target_x=None if target is None else target.x,
                    target_y=None if target is None else target.y,
                )
            )

        return events

    def _choose_displacement(
        self,
        *,
        simulation_state: SimulationState,
        organism_x: int,
        organism_y: int,
        max_speed: int,
        target: MovementTarget | None,
    ) -> tuple[int, int]:
        """Choose targeted or fallback displacement for one movement attempt."""
        if target is None:
            return self.movement_pattern.choose_displacement(
                rng=simulation_state.rng,
                max_speed=max_speed,
            )

        return self.targeted_movement_model.choose_displacement(
            current_x=organism_x,
            current_y=organism_y,
            target_x=target.x,
            target_y=target.y,
            max_speed=max_speed,
        )

    @staticmethod
    def _validate_displacement(
        *,
        dx: int,
        dy: int,
        max_speed: int,
    ) -> None:
        """Validate displacement type and Euclidean max-speed compliance."""
        validators.validate_int(
            dx,
            name="dx",
        )
        validators.validate_int(
            dy,
            name="dy",
        )

        if dx * dx + dy * dy > max_speed * max_speed:
            raise ValueError(
                "movement policy returned a displacement whose Euclidean "
                "magnitude exceeds max_speed; "
                f"received dx={dx}, dy={dy}, max_speed={max_speed}."
            )

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Movement.Event,
    ) -> None:
        """Apply an energetically valid resolved Movement event.

        The expenditure policy is rechecked against current energy before any
        state mutation. This prevents a stale same-stage event from moving an
        organism and only afterward discovering that its locomotion cost is no
        longer permitted.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Movement event to apply.

        Raises:
            RuntimeError: If the organism can no longer pay the recorded cost
                under the configured expenditure policy.
        """
        world = simulation_state.world
        organism = world.organisms[resolved_event.organism_id]

        if not energy_expenditure_is_allowed(
            self.energy_expenditure_policy,
            organism,
            energy_cost=resolved_event.energy_cost,
            simulation_state=simulation_state,
        ):
            raise RuntimeError(
                f"Organism {organism.id} cannot pay its recorded locomotion "
                "energy cost under the configured expenditure policy."
            )

        world.move_organism(
            organism_id=resolved_event.organism_id,
            x=resolved_event.new_x,
            y=resolved_event.new_y,
        )
        organism.energy -= resolved_event.energy_cost
