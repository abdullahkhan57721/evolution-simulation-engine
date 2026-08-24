"""Predation eligibility policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.genetics import ATTACK_STRENGTH, DEFENSE
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class PredationEligibility(Protocol):
    """Determine whether one organism can successfully predate another."""

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the predator-prey pairing is biologically feasible."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class LargerPredatorEligibility:
    """Allow predation only when current predator mass exceeds current prey mass."""

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the predator is currently larger than the prey."""
        return predator.body_mass > prey.body_mass


@attrs.frozen(slots=True, kw_only=True)
class GeneticAttackDefenseEligibility:
    """Compare expressed predator attack strength with expressed prey defense.

    Attributes:
        attack_trait_name: Predator genetic phenotype trait representing attack.
        defense_trait_name: Prey genetic phenotype trait representing defense.
    """

    attack_trait_name: str = ATTACK_STRENGTH
    defense_trait_name: str = DEFENSE

    def __attrs_post_init__(self) -> None:
        """Validate configured trait names."""
        for field_name in ("attack_trait_name", "defense_trait_name"):
            trait_name = validators.validate_str(
                getattr(self, field_name),
                name=field_name,
            )
            if not trait_name.strip():
                raise ValueError(f"{field_name} must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return attack and defense traits required by the policy."""
        return frozenset({self.attack_trait_name, self.defense_trait_name})

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether expressed attack strictly exceeds prey defense."""
        attack_strength = predator.genetic_phenotype.int_value(self.attack_trait_name)
        defense = prey.genetic_phenotype.int_value(self.defense_trait_name)
        return attack_strength > defense


@attrs.frozen(slots=True, kw_only=True)
class AllOfPredationEligibility:
    """Require every composed predation eligibility policy to permit the pairing.

    Attributes:
        eligibilities: Ordered predation eligibility policies to evaluate.
    """

    eligibilities: tuple[PredationEligibility, ...]

    def __attrs_post_init__(self) -> None:
        """Validate composed eligibility policies."""
        if not self.eligibilities:
            raise ValueError("eligibilities must contain at least one policy.")

        for eligibility in self.eligibilities:
            if not callable(eligibility):
                raise TypeError("each predation eligibility must be callable.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the union of nested predation trait requirements."""
        return collect_required_traits(*self.eligibilities)

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every nested policy permits predation."""
        return all(
            eligibility(
                predator,
                prey,
                simulation_state,
            )
            for eligibility in self.eligibilities
        )
