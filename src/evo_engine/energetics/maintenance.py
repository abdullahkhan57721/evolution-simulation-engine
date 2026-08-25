"""Energetic maintenance costs for realized physiological capabilities."""

from __future__ import annotations

import attrs

from evo_engine.energetics._common import round_nonnegative_cost
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators
from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class TraitMaintenanceTerm:
    """Define one linear maintenance burden above a developmental baseline.

    A term contributes
    ``max(0, developmental_value - baseline) * cost_numerator / cost_denominator``
    raw energy units. Multiple terms for the same trait are allowed, enabling
    piecewise-linear costs with increasing marginal burden.

    Attributes:
        trait_name: Developmental trait whose realized value creates the burden.
        cost_numerator: Nonnegative numerator of energy cost per trait unit.
        cost_denominator: Positive denominator of energy cost per trait unit.
        baseline: Trait value below which this term contributes no cost.
    """

    trait_name: str = attrs.field(validator=attrs_validators.validate_str)
    cost_numerator: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    cost_denominator: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_gt(0),
    )
    baseline: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    def raw_cost(self, organism: Organism) -> float:
        """Return this term's unrounded maintenance cost for an organism.

        Args:
            organism: Organism whose realized developmental trait is evaluated.

        Returns:
            Nonnegative unrounded energy cost.
        """
        trait_value = organism.developmental_profile.int_value(self.trait_name)
        excess = max(0, trait_value - self.baseline)
        return excess * self.cost_numerator / self.cost_denominator


@attrs.frozen(slots=True, kw_only=True)
class LinearTraitMaintenanceCost:
    """Charge ongoing energy for realized physiological performance traits.

    All configured terms are summed before integer rounding, so several modest
    physiological burdens can combine into a meaningful maintenance cost. The
    model reads the organism's developmental profile rather than its raw genetic
    phenotype. This makes energetic cost follow the physiology actually realized
    by development and leaves future plasticity or G×E effects in the development
    layer where they belong.

    Attributes:
        terms: Linear maintenance terms summed for each organism.
        minimum_cost: Minimum integer maintenance cost after rounding.
    """

    terms: tuple[TraitMaintenanceTerm, ...] = attrs.field(
        validator=attrs_validators.validate_tuple,
    )
    minimum_cost: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate maintenance-term configuration."""
        if not self.terms:
            raise ValueError("terms must not be empty.")
        for index, term in enumerate(self.terms):
            if not isinstance(term, TraitMaintenanceTerm):
                raise TypeError(
                    f"terms[{index}] must be a TraitMaintenanceTerm; received {term!r}."
                )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return developmental/genetic traits required by maintenance terms."""
        return frozenset(term.trait_name for term in self.terms)

    def calculate_cost(
        self,
        organism: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return the organism's rounded physiological maintenance cost.

        Args:
            organism: Organism whose realized physiology is evaluated.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative integer energy cost.
        """
        raw_cost = sum(term.raw_cost(organism) for term in self.terms)
        return round_nonnegative_cost(
            raw_cost,
            minimum_cost=self.minimum_cost,
        )
