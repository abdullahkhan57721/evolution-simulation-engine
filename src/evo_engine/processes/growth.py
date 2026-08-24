"""Growth simulation process."""

from __future__ import annotations

from typing import ClassVar

import attrs

from evo_engine.behavior import SOMATIC_INVESTMENT, behavior_is_allowed
from evo_engine.energetics.expenditure import (
    EnergyExpenditurePolicy,
    SpendToZero,
    energy_expenditure_is_allowed,
)
from evo_engine.energetics.growth import GrowthCostModel
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.growth.models import GrowthModel
from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class Growth:
    """Grow organisms toward immutable developmental body-mass targets.

    The configured growth model determines potential body-mass gain. This
    process caps that gain at the organism's realized developmental target,
    prices the capped gain with the configured energetic model, and proposes
    growth only when the full cost is permitted by the configured energy
    expenditure policy.

    Attributes:
        growth_model: Model used to determine potential body-mass gain.
        growth_cost_model: Model used to calculate energetic growth cost.
        energy_expenditure_policy: Policy deciding whether the priced growth
            expenditure may be paid.
        trait_name: Developmental target that defines adult body mass.
    """

    behavioral_purpose: ClassVar[str] = SOMATIC_INVESTMENT

    growth_model: GrowthModel
    growth_cost_model: GrowthCostModel
    energy_expenditure_policy: EnergyExpenditurePolicy = attrs.field(
        factory=SpendToZero,
    )
    trait_name: str = attrs.field(
        default=ADULT_BODY_MASS,
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate Growth configuration."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

        if not callable(
            getattr(
                self.energy_expenditure_policy,
                "can_spend",
                None,
            )
        ):
            raise TypeError(
                "energy_expenditure_policy must provide a callable can_spend method."
            )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by Growth and its configured models."""
        return frozenset({self.trait_name}) | collect_required_traits(
            self.growth_model,
            self.growth_cost_model,
            self.energy_expenditure_policy,
        )

    @property
    def event_type(self) -> type[Growth.Event]:
        """Return the Growth event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent an energetically permitted proposed Growth event.

        Attributes:
            step_index: Simulation step associated with the event.
            organism_id: ID of the growing organism.
            body_mass_gain: Body-mass units added by the event.
            energy_cost: Energy consumed by the event.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        organism_id: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        body_mass_gain: int = attrs.field(
            validator=attrs_validators.validate_int_ge(1),
        )
        energy_cost: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Growth.Event]:
        """Propose behaviorally selected, energetically permitted growth events.

        Potential gain is capped before energetic pricing, so organisms never
        pay for model overshoot beyond their adult target. Growth is initially
        all-or-nothing: if the full capped gain is not permitted, no event is
        proposed rather than partially growing the organism.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Behaviorally selected, energetically permitted proposed Growth
            events.

        Raises:
            KeyError: If an organism lacks the configured developmental target.
            TypeError: If a behavior, growth, cost, or expenditure model
                violates its return contract.
            ValueError: If a target, purpose, gain, or energy cost violates its
                validation contract.
        """
        events: list[Growth.Event] = []

        for organism in simulation_state.world.organisms.values():
            if not behavior_is_allowed(
                organism,
                behavioral_purpose=self.behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            target_body_mass = organism.developmental_profile.int_value(self.trait_name)
            validators.validate_int_ge(
                target_body_mass,
                bound=1,
                name=f"developmental target {self.trait_name!r}",
            )

            if organism.body_mass >= target_body_mass:
                continue

            potential_gain = self.growth_model.determine_body_mass_gain(
                organism,
                target_body_mass=target_body_mass,
                simulation_state=simulation_state,
            )
            validators.validate_int_ge(
                potential_gain,
                bound=0,
                name="potential body-mass gain",
            )

            body_mass_gain = min(
                potential_gain,
                target_body_mass - organism.body_mass,
            )
            if body_mass_gain == 0:
                continue

            energy_cost = self.growth_cost_model.calculate_cost(
                organism,
                body_mass_gain=body_mass_gain,
                simulation_state=simulation_state,
            )
            validators.validate_int_ge(
                energy_cost,
                bound=0,
                name="growth energy cost",
            )

            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                organism,
                energy_cost=energy_cost,
                simulation_state=simulation_state,
            ):
                continue

            events.append(
                self.Event(
                    step_index=simulation_state.step_index,
                    organism_id=organism.id,
                    body_mass_gain=body_mass_gain,
                    energy_cost=energy_cost,
                )
            )

        return events

    def apply_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Growth.Event,
    ) -> None:
        """Apply an energetically permitted resolved Growth event.

        The expenditure policy is checked again at application time because
        other same-stage events may have consumed energy after proposal. A
        stale event that is no longer permitted raises rather than creating
        body mass while violating the configured reserve strategy.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Growth event to apply.

        Raises:
            RuntimeError: If the organism can no longer pay the event under the
                configured expenditure policy.
        """
        organism = simulation_state.world.organisms[resolved_event.organism_id]

        if not energy_expenditure_is_allowed(
            self.energy_expenditure_policy,
            organism,
            energy_cost=resolved_event.energy_cost,
            simulation_state=simulation_state,
        ):
            raise RuntimeError(
                "Resolved Growth event is no longer affordable under the "
                f"configured energy expenditure policy for organism {organism.id}: "
                f"requires {resolved_event.energy_cost} energy, has "
                f"{organism.energy}."
            )

        organism.body_mass += resolved_event.body_mass_gain
        organism.energy -= resolved_event.energy_cost
