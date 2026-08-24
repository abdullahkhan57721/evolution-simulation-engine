"""Individual eligibility policies for reproduction."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.energetics.thresholds import (
    EnergyThresholdSource,
    determine_energy_threshold,
    validate_energy_threshold_source,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import MATURITY_AGE
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class ReproductiveEligibility(Protocol):
    """Define whether an organism is individually eligible to reproduce."""

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism is individually eligible to reproduce.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether the organism is individually eligible to reproduce.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class AlwaysEligible:
    """Consider every organism individually eligible for reproduction."""

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return True for every organism.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            True.
        """
        return True


@attrs.frozen(slots=True, kw_only=True)
class MinimumEnergyEligibility:
    """Require current energy to meet a fixed or organism-specific threshold.

    Attributes:
        minimum_energy: Fixed value or model determining the minimum current
            energy required for reproductive eligibility.
    """

    minimum_energy: EnergyThresholdSource

    def __attrs_post_init__(self) -> None:
        """Validate the configured minimum-energy source."""
        validate_energy_threshold_source(
            self.minimum_energy,
            name="minimum_energy",
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by the configured threshold model."""
        return collect_required_traits(self.minimum_energy)

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism meets the minimum-energy requirement.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether the organism has at least its resolved minimum energy.
        """
        minimum_energy = determine_energy_threshold(
            self.minimum_energy,
            organism,
            simulation_state=simulation_state,
            name="minimum_energy",
        )
        return organism.energy >= minimum_energy


@attrs.frozen(slots=True, kw_only=True)
class MinimumAgeEligibility:
    """Require a fixed minimum age for reproductive eligibility.

    Attributes:
        minimum_age: Minimum current organism age required for reproduction.
    """

    minimum_age: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether an organism meets the fixed minimum age.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether current age is at least ``minimum_age``.
        """
        return organism.age >= self.minimum_age


@attrs.frozen(slots=True, kw_only=True)
class DevelopmentalMaturityEligibility:
    """Require age to reach an organism-specific developmental maturity target.

    Attributes:
        trait_name: Developmental-profile trait storing age at reproductive
            maturity.
    """

    trait_name: str = attrs.field(
        default=MATURITY_AGE,
        validator=attrs_validators.validate_str,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured maturity trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the developmental trait required for maturity."""
        return frozenset({self.trait_name})

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether current age has reached developmental maturity.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            Whether current age is at least the organism's maturity target.

        Raises:
            KeyError: If the maturity trait is absent.
            TypeError: If the maturity target is not an integer.
            ValueError: If the maturity target is negative.
        """
        maturity_age = validators.validate_int_ge(
            organism.developmental_profile.int_value(self.trait_name),
            bound=0,
            name=f"developmental_profile[{self.trait_name!r}]",
        )
        return organism.age >= maturity_age


@attrs.frozen(slots=True, kw_only=True)
class AllOfEligibility:
    """Require every configured reproductive eligibility policy to pass.

    Attributes:
        eligibilities: Nonempty tuple of eligibility policies evaluated in
            order with short-circuiting.
    """

    eligibilities: tuple[ReproductiveEligibility, ...] = attrs.field(
        validator=attrs.validators.instance_of(tuple),
    )

    def __attrs_post_init__(self) -> None:
        """Validate the composed eligibility policies."""
        if not self.eligibilities:
            raise ValueError("eligibilities must contain at least one policy.")

        for index, eligibility in enumerate(self.eligibilities):
            if not callable(getattr(eligibility, "is_eligible", None)):
                raise TypeError(
                    f"eligibilities[{index}] must provide a callable "
                    "is_eligible method."
                )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the union of traits required by nested eligibility policies."""
        return collect_required_traits(*self.eligibilities)

    def is_eligible(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every nested eligibility policy accepts the organism.

        Args:
            organism: Organism being evaluated.
            simulation_state: Current simulation state.

        Returns:
            ``True`` only when every nested policy returns ``True``.

        Raises:
            TypeError: If a nested policy returns a non-Boolean decision.
        """
        for index, eligibility in enumerate(self.eligibilities):
            decision = eligibility.is_eligible(
                organism,
                simulation_state=simulation_state,
            )

            if type(decision) is not bool:
                raise TypeError(
                    f"eligibilities[{index}].is_eligible must return a Boolean."
                )

            if not decision:
                return False

        return True
