"""Growth simulation process."""

from __future__ import annotations

from typing import ClassVar

import attrs

from evo_engine.behavior import SOMATIC_INVESTMENT
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
    growth only when the full cost is affordable.

    Attributes:
        growth_model: Model used to determine potential body-mass gain.
        growth_cost_model: Model used to calculate energetic growth cost.
        trait_name: Developmental target that defines adult body mass.
    """

    behavioral_purpose: ClassVar[str] = SOMATIC_INVESTMENT

    growth_model: GrowthModel
    growth_cost_model: GrowthCostModel
    trait_name: str = attrs.field(
        default=ADULT_BODY_MASS,
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate Growth configuration."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by Growth and its configured models."""
        return frozenset({self.trait_name}) | collect_required_traits(
            self.growth_model,
            self.growth_cost_model,
        )

    @property
    def event_type(self) -> type[Growth.Event]:
        """Return the Growth event type."""
        return self.Event

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent an affordable proposed Growth event.

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
        """Propose affordable growth toward developmental targets.

        Potential gain is capped before energetic pricing, so organisms never
        pay for model overshoot beyond their adult target. Growth is initially
        all-or-nothing: if the full capped gain is unaffordable, no event is
        proposed rather than partially growing the organism.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Affordable proposed Growth events.

        Raises:
            KeyError: If an organism lacks the configured developmental target.
            TypeError: If a growth model or cost model violates its integer
                return contract.
            ValueError: If a target, gain, or energy cost violates its
                nonnegative/positive contract.
        """
        events: list[Growth.Event] = []

        for organism in simulation_state.world.organisms.values():
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

            if energy_cost > organism.energy:
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
        """Apply an affordable resolved Growth event.

        Affordability is checked again at application time because other
        same-stage events may have consumed energy after proposal. A stale
        unaffordable event raises rather than creating body mass without paying
        its recorded energetic cost.

        Args:
            simulation_state: Current simulation state.
            resolved_event: Resolved Growth event to apply.

        Raises:
            RuntimeError: If the organism can no longer afford the event.
        """
        organism = simulation_state.world.organisms[resolved_event.organism_id]

        if organism.energy < resolved_event.energy_cost:
            raise RuntimeError(
                "Resolved Growth event is no longer affordable for organism "
                f"{organism.id}: requires {resolved_event.energy_cost} energy, "
                f"has {organism.energy}."
            )

        organism.body_mass += resolved_event.body_mass_gain
        organism.energy -= resolved_event.energy_cost
