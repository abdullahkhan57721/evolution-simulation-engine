"""Reusable fixed and organism-specific energetic coefficient sources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias, cast, runtime_checkable

import attrs

from evo_engine.energetics._common import validate_finite_number
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@runtime_checkable
class CoefficientModel(Protocol):
    """Determine an organism-specific nonnegative numerical coefficient."""

    def determine_coefficient(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int | float:
        """Return an organism-specific coefficient.

        Args:
            organism: Organism whose coefficient is being determined.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative finite numerical coefficient.
        """
        ...


CoefficientSource: TypeAlias = int | float | CoefficientModel


@attrs.frozen(slots=True, kw_only=True)
class GeneticPhenotypeCoefficient:
    """Read and scale a coefficient from an organism's genetic phenotype.

    Integer genetic traits are divided by ``denominator`` before use. This
    allows integer-locus genetics to represent fractional energetic
    coefficients without introducing floating-point alleles. For example, a
    trait value of 30 with denominator 100 produces coefficient 0.30.

    Attributes:
        trait_name: Genetic phenotype trait storing the integer coefficient.
        denominator: Positive integer scale divisor.
    """

    trait_name: str = attrs.field(
        validator=attrs_validators.validate_str,
    )
    denominator: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_gt(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate the configured trait name."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return the genetic phenotype trait required by this model."""
        return frozenset({self.trait_name})

    def determine_coefficient(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> float:
        """Return the scaled nonnegative genetic phenotype coefficient.

        Args:
            organism: Organism whose coefficient is being determined.
            simulation_state: Current simulation state.

        Returns:
            Nonnegative coefficient obtained by dividing the integer trait by
            ``denominator``.

        Raises:
            KeyError: If the configured trait is absent.
            TypeError: If the genetic phenotype value is not an integer.
            ValueError: If the genetic phenotype value is negative.
        """
        numerator = validators.validate_int_ge(
            organism.genetic_phenotype.int_value(self.trait_name),
            bound=0,
            name=f"genetic_phenotype[{self.trait_name!r}]",
        )
        return numerator / self.denominator


def validate_coefficient_source(
    value: object,
    *,
    name: str = "coefficient",
) -> None:
    """Validate a fixed coefficient or coefficient model.

    Args:
        value: Coefficient source to validate.
        name: Human-readable value name used in validation messages.

    Raises:
        TypeError: If value is neither a number nor coefficient model.
        ValueError: If a fixed coefficient is negative or non-finite.
    """
    if type(value) in (int, float):
        coefficient = validate_finite_number(
            value,
            name=name,
        )
        if coefficient < 0:
            raise ValueError(f"{name} must be nonnegative; received {coefficient!r}.")
        return

    if not callable(getattr(value, "determine_coefficient", None)):
        raise TypeError(
            f"{name} must be a finite nonnegative number or provide a callable "
            "determine_coefficient method."
        )


def determine_coefficient(
    coefficient_source: CoefficientSource,
    organism: Organism,
    *,
    simulation_state: SimulationState,
    name: str = "coefficient",
) -> int | float:
    """Return a validated coefficient from a fixed value or model.

    Args:
        coefficient_source: Fixed coefficient or organism-specific model.
        organism: Organism whose coefficient is being determined.
        simulation_state: Current simulation state.
        name: Human-readable coefficient name used in validation messages.

    Returns:
        Validated nonnegative finite numerical coefficient.

    Raises:
        TypeError: If the source or returned coefficient has an invalid type.
        ValueError: If a coefficient is negative or non-finite.
    """
    validate_coefficient_source(
        coefficient_source,
        name=name,
    )

    if type(coefficient_source) in (int, float):
        return cast(int | float, coefficient_source)

    coefficient_model = cast(CoefficientModel, coefficient_source)
    coefficient = validate_finite_number(
        coefficient_model.determine_coefficient(
            organism,
            simulation_state=simulation_state,
        ),
        name=f"{name} model return value",
    )
    if coefficient < 0:
        raise ValueError(
            f"{name} model return value must be nonnegative; received {coefficient!r}."
        )
    return coefficient


def coefficient_required_traits(
    coefficient_source: CoefficientSource,
) -> frozenset[str]:
    """Return genetic traits required by a coefficient source.

    Args:
        coefficient_source: Fixed coefficient or organism-specific model.

    Returns:
        Required trait names, or an empty set for fixed numerical coefficients.
    """
    return collect_required_traits(coefficient_source)
