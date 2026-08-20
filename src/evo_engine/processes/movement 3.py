"""Movement simulation process."""

from __future__ import annotations

import attrs

from evo_engine.energetics.locomotion import LocomotionCostModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import MAX_SPEED
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.spatial.boundary_conditions import BoundaryCondition
from evo_engine.spatial.movement_patterns import MovementPattern
from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class Movement:
    """Represent the Movement simulation process.

    ``max_speed`` is interpreted as maximum Euclidean grid-distance per
    timestep. The process validates that every configured movement pattern
    respects that genetically expressed capability before recording the event.

    Attributes:
        movement_pattern: Pattern used to choose movement displacements.
        boundary_condition: Rule used to resolve world-boundary crossings.
        locomotion_cost_model: Model used to calculate movement energy cost.
    """

    movement_pattern: MovementPattern
    boundary_condition: BoundaryCondition
    locomotion_cost_model: LocomotionCostModel

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by movement and its policies."""
        return frozenset({MAX_SPEED}) | collect_required_traits(
            self.movement_pattern,
            self.boundary_condition,
            self.locomotion_cost_model,
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

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Movement.Event]:
        """Propose Movement events for organisms in the world.

        Each organism's expressed ``max_speed`` limits the magnitude of its
        attempted displacement. The movement pattern chooses direction and
        distance within that capability; the boundary condition resolves the
        destination; and the locomotion model determines the energy cost.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Movement events.

        Raises:
            TypeError: If a movement pattern or cost model violates its
                integer-valued contract.
            ValueError: If a movement pattern exceeds an organism's max speed
                or a cost model returns a negative cost.
        """
        events: list[Movement.Event] = []

        world = simulation_state.world

        for organism in world.organisms.values():
            max_speed = organism.genetic_phenotype.int_value(MAX_SPEED)
            validators.validate_int_ge(
                max_speed,
                bound=0,
                name=MAX_SPEED,
            )

            dx, dy = self.movement_pattern.choose_displacement(
                rng=simulation_state.rng,
                max_speed=max_speed,
            )
            validators.validate_int(
                dx,
                name="dx",
            )
            validators.validate_int(
                dy,
                name="dy",
            )

            # The process enforces the semantic contract even for custom
            # movement patterns supplied by users.
            if dx * dx + dy * dy > max_speed * max_speed:
                raise ValueError(
                    "movement pattern returned a displacement whose "
                    "Euclidean magnitude exceeds max_speed; "
                    f"received dx={dx}, dy={dy}, max_speed={max_speed}."
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
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Movement.Event,
    ) -> None:
        """Apply a resolved Movement event.

        The destination and energy expenditure were both decided during
        proposal, so application only performs the recorded state changes.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Movement event to apply.
        """
        world = simulation_state.world
        organism = world.organisms[resolved_event.organism_id]

        world.move_organism(
            organism_id=resolved_event.organism_id,
            x=resolved_event.new_x,
            y=resolved_event.new_y,
        )
        organism.energy = max(
            0,
            organism.energy - resolved_event.energy_cost,
        )
