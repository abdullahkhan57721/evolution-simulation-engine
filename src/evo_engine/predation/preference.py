"""Predation preference policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

import attrs

from evo_engine.genetics import ATTACK_STRENGTH, DEFENSE
from evo_engine.validation import validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class PredationPreference(Protocol):
    """Score feasible predator-prey pairings for conflict resolution."""

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return an integer preference score; higher scores are preferred."""
        ...


@attrs.frozen(slots=True, kw_only=True)
class NeutralPredationPreference:
    """Assign the same preference score to every feasible pairing."""

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return a neutral zero preference score."""
        return 0


@attrs.frozen(slots=True, kw_only=True)
class GeneticAttackAdvantagePreference:
    """Prefer pairings with the largest expressed attack-defense advantage.

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
        """Return attack and defense traits required by the preference."""
        return frozenset({self.attack_trait_name, self.defense_trait_name})

    def __call__(
        self,
        predator: Organism,
        prey: Organism,
        simulation_state: SimulationState,
    ) -> int:
        """Return expressed predator attack minus expressed prey defense."""
        attack_strength = predator.genetic_phenotype.int_value(self.attack_trait_name)
        defense = prey.genetic_phenotype.int_value(self.defense_trait_name)
        return attack_strength - defense
