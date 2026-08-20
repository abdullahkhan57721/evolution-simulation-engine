"""Newborn body-mass initialization policies."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.development.profile import DevelopmentalProfile
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class OffspringBodyMassModel(Protocol):
    """Define the current body mass assigned to a newborn organism."""

    def determine_body_mass(
        self,
        developmental_profile: DevelopmentalProfile,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the newborn's positive integer body mass.

        Args:
            developmental_profile: Offspring developmental target profile.
            parents: One or two resolved reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Positive integer body mass for the newborn.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AdultBodyMassAtBirth:
    """Initialize newborn current mass from a realized adult-body-mass target.

    This preserves the engine's previous fixed-size behavior until a Growth
    process is configured. A future developmental policy can instead start
    offspring below adult mass without changing Reproduction itself.

    Attributes:
        trait_name: Developmental target representing realized adult body mass.
    """

    trait_name: str = ADULT_BODY_MASS

    def __attrs_post_init__(self) -> None:
        """Validate the configured adult-mass trait name."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the adult-mass genetic/developmental dependency."""
        return frozenset({self.trait_name})

    def determine_body_mass(
        self,
        developmental_profile: DevelopmentalProfile,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the offspring's realized adult body-mass target.

        Args:
            developmental_profile: Offspring developmental target profile.
            parents: One or two resolved reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Positive integer newborn body mass.
        """
        body_mass = developmental_profile.int_value(self.trait_name)
        return validators.validate_int_ge(
            body_mass,
            bound=1,
            name=self.trait_name,
        )


@attrs.frozen(slots=True, kw_only=True)
class FixedBodyMassAtBirth:
    """Assign every newborn the same current body mass.

    Attributes:
        body_mass: Positive current mass assigned at birth.
    """

    body_mass: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )

    def determine_body_mass(
        self,
        developmental_profile: DevelopmentalProfile,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return the configured newborn body mass.

        Args:
            developmental_profile: Offspring developmental target profile.
            parents: One or two resolved reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Configured positive body mass.
        """
        return self.body_mass


@attrs.frozen(slots=True, kw_only=True)
class FractionOfAdultBodyMassAtBirth:
    """Initialize newborn mass as a fraction of its realized adult target.

    Attributes:
        numerator: Positive numerator of the adult-mass fraction.
        denominator: Positive denominator of the adult-mass fraction.
        minimum_body_mass: Positive lower bound on newborn current mass.
        trait_name: Developmental target representing realized adult mass.
    """

    numerator: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    denominator: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )
    minimum_body_mass: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    trait_name: str = ADULT_BODY_MASS

    def __attrs_post_init__(self) -> None:
        """Validate the configured adult-mass trait name and fraction."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace.")

        if self.numerator > self.denominator:
            raise ValueError("numerator must be less than or equal to denominator.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the adult-mass genetic/developmental dependency."""
        return frozenset({self.trait_name})

    def determine_body_mass(
        self,
        developmental_profile: DevelopmentalProfile,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return an integer fraction of realized adult body mass.

        Args:
            developmental_profile: Offspring developmental target profile.
            parents: One or two resolved reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Positive newborn current body mass.
        """
        adult_body_mass = developmental_profile.int_value(self.trait_name)
        validators.validate_int_ge(
            adult_body_mass,
            bound=1,
            name=self.trait_name,
        )

        body_mass = adult_body_mass * self.numerator // self.denominator

        return max(
            body_mass,
            self.minimum_body_mass,
        )
