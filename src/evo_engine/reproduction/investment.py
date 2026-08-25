"""Parental energy-investment policies for reproduction."""

from __future__ import annotations

from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.builtin_traits import OFFSPRING_ENERGY
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class ParentalInvestment(Protocol):
    """Define how much energy each reproductive parent invests."""

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return one energy investment for each parent.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeEnergyInvestment:
    """Use an integer genetic phenotype trait as each parent's energy investment.

    Attributes:
        trait_name: Name of the genetic phenotype trait specifying parental energy
            investment.
    """

    trait_name: str = OFFSPRING_ENERGY

    def __attrs_post_init__(self) -> None:
        """Validate the genetic phenotype trait name."""
        validators.validate_str(
            self.trait_name,
            name="trait_name",
        )

        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the genetic phenotype trait used for parental investment."""
        return frozenset({self.trait_name})

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return each parent's genetically expressed trait value as its investment.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.

        Raises:
            ValueError: If a configured genetic phenotype value is negative.
        """
        investments = tuple(
            parent.genetic_phenotype.int_value(self.trait_name) for parent in parents
        )

        for investment in investments:
            if investment < 0:
                raise ValueError(
                    f"genetic phenotype trait {self.trait_name!r} must be "
                    "non-negative for parental investment."
                )

        return investments


@attrs.frozen(slots=True, kw_only=True)
class FixedEnergyInvestment:
    """Make every parent invest the same fixed amount of energy.

    Attributes:
        amount: Energy invested by each parent.
    """

    amount: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return the configured fixed investment for each parent.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Energy investments aligned with the parent tuple.
        """
        return tuple(self.amount for _ in parents)


@attrs.frozen(slots=True, kw_only=True)
class MatingTypeInvestmentScale:
    """Define a rational parental-investment scale for one mating type.

    Attributes:
        mating_type: Nonempty mating-type label receiving the scale.
        numerator: Nonnegative scale numerator.
        denominator: Positive scale denominator.
    """

    mating_type: str = attrs.field(validator=attrs_validators.validate_str)
    numerator: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    denominator: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_gt(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate the mating-type label."""
        if not self.mating_type.strip():
            raise ValueError("mating_type must not be empty or whitespace-only.")

    def scale(self, investment: int) -> int:
        """Scale a nonnegative integer investment using half-up rounding.

        Args:
            investment: Unscaled nonnegative energy investment.

        Returns:
            Scaled nonnegative integer investment.
        """
        validated = validators.validate_int_ge(
            investment,
            bound=0,
            name="investment",
        )
        scaled_numerator = validated * self.numerator
        quotient, remainder = divmod(scaled_numerator, self.denominator)
        if remainder * 2 >= self.denominator:
            quotient += 1
        return quotient


@attrs.frozen(slots=True, kw_only=True)
class MatingTypeScaledInvestment:
    """Scale a base parental-investment policy by each parent's mating type.

    The wrapped policy first determines one base investment for each parent.
    Each amount is then multiplied by the scale associated with that parent's
    immutable ``mating_type``. Parent tuple order therefore does not define a
    reproductive role: asymmetry follows individual reproductive identity.

    Unlisted mating types retain their base investment through an implicit 1:1
    scale. This lets simulations introduce additional types without silently
    assigning them one of the configured asymmetric roles.

    Attributes:
        base_investment: Underlying policy producing aligned parent investments.
        scales: Unique mating-type-specific rational scale factors.
    """

    base_investment: ParentalInvestment
    scales: tuple[MatingTypeInvestmentScale, ...] = attrs.field(
        validator=attrs_validators.validate_tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate the wrapped policy and mating-type scale set."""
        if not callable(getattr(self.base_investment, "determine_investments", None)):
            raise TypeError(
                "base_investment must provide a callable determine_investments method."
            )

        seen_types: set[str] = set()
        for index, scale in enumerate(self.scales):
            if not isinstance(scale, MatingTypeInvestmentScale):
                raise TypeError(
                    f"scales[{index}] must be a MatingTypeInvestmentScale; "
                    f"received {scale!r}."
                )
            if scale.mating_type in seen_types:
                raise ValueError(
                    "scales must not contain duplicate mating types; received "
                    f"{scale.mating_type!r}."
                )
            seen_types.add(scale.mating_type)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic traits required by the wrapped investment policy."""
        return collect_required_traits(self.base_investment)

    def determine_investments(
        self,
        parents: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[int, ...]:
        """Return mating-type-scaled investments aligned with the parent tuple.

        Args:
            parents: One or two reproductive parents.
            simulation_state: Current simulation state.

        Returns:
            Scaled nonnegative integer energy investments.

        Raises:
            TypeError: If the wrapped policy does not return a tuple or returns
                a non-integer investment.
            ValueError: If the wrapped policy returns the wrong number of values
                or a negative investment.
        """
        base_values = validators.validate_tuple(
            self.base_investment.determine_investments(
                parents,
                simulation_state=simulation_state,
            ),
            name="base investments",
        )
        if len(base_values) != len(parents):
            raise ValueError(
                "base_investment must return exactly one investment per parent."
            )

        return tuple(
            self._scale_for(parent.mating_type).scale(
                validators.validate_int_ge(
                    base_value,
                    bound=0,
                    name=f"base investments[{index}]",
                )
            )
            for index, (parent, base_value) in enumerate(
                zip(parents, base_values, strict=True)
            )
        )

    def _scale_for(self, mating_type: str) -> MatingTypeInvestmentScale:
        """Return the configured scale or an implicit neutral scale."""
        for scale in self.scales:
            if scale.mating_type == mating_type:
                return scale
        return MatingTypeInvestmentScale(
            mating_type=mating_type,
            numerator=1,
            denominator=1,
        )
