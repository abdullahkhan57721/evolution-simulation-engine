"""Resource Consumption simulation process."""

from __future__ import annotations

from typing import ClassVar

import attrs

from evo_engine.behavior import ENERGY_ACQUISITION, behavior_is_allowed
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.feeding import (
    AssimilationModel,
    FullAssimilation,
    IntakeCapacityModel,
    determine_assimilated_energy,
    determine_intake_capacity,
)
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import attrs_validators


@attrs.frozen(slots=True, kw_only=True)
class ResourceConsumption:
    """Consume local environmental resources and assimilate usable energy.

    ``requested_amount`` represents behavioral demand. An optional
    ``intake_capacity_model`` can impose a lower physiological ceiling before
    resource competition is resolved. After allocation, ``assimilation_model``
    determines how much usable energy the actually consumed resource yields.

    Resource allocation and physiology therefore remain separate concerns:
    resolvers decide how much food an organism receives, while this process
    converts the resolved allocation into organism energy during application.

    Attributes:
        requested_amount: Resource units requested by each eligible organism
            before any physiological intake cap is applied.
        intake_capacity_model: Optional model limiting resource intake per
            organism and timestep. ``None`` preserves uncapped historical
            request behavior.
        assimilation_model: Model converting actually consumed resource units
            into usable organism energy. Defaults to one energy unit per
            consumed resource unit.
    """

    behavioral_purpose: ClassVar[str] = ENERGY_ACQUISITION

    requested_amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    intake_capacity_model: IntakeCapacityModel | None = None
    assimilation_model: AssimilationModel = attrs.field(
        factory=FullAssimilation,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured feeding-physiology collaborators."""
        if self.intake_capacity_model is not None and not callable(
            getattr(
                self.intake_capacity_model,
                "determine_capacity",
                None,
            )
        ):
            raise TypeError(
                "intake_capacity_model must provide a callable "
                "determine_capacity method."
            )

        if not callable(
            getattr(
                self.assimilation_model,
                "determine_energy_gain",
                None,
            )
        ):
            raise TypeError(
                "assimilation_model must provide a callable "
                "determine_energy_gain method."
            )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by configured feeding-physiology models."""
        return collect_required_traits(
            self.intake_capacity_model,
            self.assimilation_model,
        )

    @property
    def event_type(self) -> type[ResourceConsumption.Event]:
        """Return the Resource Consumption event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a requested or resolved resource-consumption amount.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the consuming organism.
            x: Horizontal coordinate of the consumed resource.
            y: Vertical coordinate of the consumed resource.
            amount: Resource units requested before resolution or actually
                allocated after resolution.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        amount: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[ResourceConsumption.Event]:
        """Propose behaviorally selected, physiologically capped food requests.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Proposed Resource Consumption events for organisms whose current
            behavior-selection model permits energy acquisition. Event amounts
            are capped by configured intake physiology before resource
            allocation is resolved.
        """
        events: list[ResourceConsumption.Event] = []

        for organism in simulation_state.world.organisms.values():
            if not behavior_is_allowed(
                organism,
                behavioral_purpose=self.behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            amount = self.requested_amount

            if self.intake_capacity_model is not None:
                intake_capacity = determine_intake_capacity(
                    self.intake_capacity_model,
                    organism,
                    simulation_state=simulation_state,
                )
                amount = min(
                    amount,
                    intake_capacity,
                )

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                    x=organism.x,
                    y=organism.y,
                    amount=amount,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: ResourceConsumption.Event,
    ) -> None:
        """Consume a resolved allocation and add its assimilated energy.

        The full resolved resource amount leaves the environmental pool. Only
        the amount returned by ``assimilation_model`` becomes organism energy;
        unassimilated material is currently outside the modeled resource pool.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Resource Consumption event to apply.
        """
        organism = simulation_state.world.organisms[resolved_event.organism_id]
        energy_gain = determine_assimilated_energy(
            self.assimilation_model,
            organism,
            consumed_amount=resolved_event.amount,
            simulation_state=simulation_state,
        )

        simulation_state.world.remove_resources(
            x=resolved_event.x,
            y=resolved_event.y,
            amount=resolved_event.amount,
        )
        organism.change_energy(energy_gain)
