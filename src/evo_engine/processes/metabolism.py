"""Metabolism simulation process."""

from __future__ import annotations

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.energetics.metabolism import MetabolicCostModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.reference import EntityReferenceModel
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState


@attrs.frozen(slots=True, kw_only=True)
class Metabolism:
    """Apply basal metabolic energy expenditure to active organisms.

    The process determines when metabolic expenditure occurs. The configured
    cost model determines how much energy each organism spends, keeping the
    biological scaling law independent of engine orchestration. Read access and
    reference derivation are delegated independently from metabolic semantics.

    Attributes:
        cost_model: Model used to calculate per-organism metabolic cost.
        access_model: Policy providing read-only access to active organisms.
        reference_model: Policy deriving stable references for active organisms.
    """

    cost_model: MetabolicCostModel
    access_model: EntityAccessModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismAccess,
    )
    reference_model: EntityReferenceModel[Organism, WorldState, int] = attrs.field(
        factory=WorldOrganismReference,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured entity policies."""
        for policy, method_name, policy_name in (
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.reference_model, "reference", "reference_model"),
        ):
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by the configured cost model."""
        return collect_required_traits(self.cost_model)

    @property
    def event_type(self) -> type[Metabolism.Event]:
        """Return the Metabolism event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a proposed Metabolism event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the organism paying the metabolic cost.
            energy_cost: Energy removed by metabolism.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        energy_cost: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Metabolism.Event]:
        """Propose one metabolic expenditure event per active organism.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Metabolism events.

        Raises:
            TypeError: If the cost model does not return an integer.
            ValueError: If the cost model returns a negative cost.
        """
        events: list[Metabolism.Event] = []
        world = simulation_state.world

        for organism in self.access_model.entities(state=world):
            energy_cost = self.cost_model.calculate_cost(
                organism,
                simulation_state,
            )
            validators.validate_int_ge(
                energy_cost,
                bound=0,
                name="metabolic energy cost",
            )

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=self.reference_model.reference(
                        organism,
                        state=world,
                    ),
                    energy_cost=energy_cost,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Metabolism.Event,
    ) -> None:
        """Apply a resolved Metabolism event.

        Energy is clamped to zero if the recorded cost exceeds available
        energy. Mortality remains a separate process such as Starvation.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Metabolism event to apply.
        """
        organism = self.access_model.get(
            resolved_event.organism_id,
            state=simulation_state.world,
        )

        organism.energy = max(
            0,
            organism.energy - resolved_event.energy_cost,
        )
