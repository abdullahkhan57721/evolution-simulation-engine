"""Models for realizing developmental targets from genetic phenotypes."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

import attrs

from evo_engine.development.profile import DevelopmentalProfile
from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.requirements import validate_required_traits
from evo_engine.validation import attrs_validators, validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState

ValueT = TypeVar("ValueT")


class TraitDevelopmentModel(Protocol[ValueT]):
    """Define how one genetically expressed trait is developmentally realized."""

    def develop(
        self,
        value: ValueT,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> ValueT:
        """Return an individual developmental realization of a trait value.

        Args:
            value: Genetically expressed trait value.
            rng: Simulation random-number generator.
            simulation_state: Optional state available to environment-aware
                developmental models.

        Returns:
            Realized developmental target value.
        """
        ...


class DevelopmentModel(Protocol):
    """Define how a genetic phenotype becomes a developmental profile.

    Implementations may change trait values, but must preserve the complete
    ordered trait-name sequence from the supplied ``GeneticPhenotype``.
    """

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by the model."""
        ...

    def develop(
        self,
        genetic_phenotype: GeneticPhenotype,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> DevelopmentalProfile:
        """Return organism-specific developmental targets.

        Args:
            genetic_phenotype: Genetically expressed phenotype.
            rng: Simulation random-number generator.
            simulation_state: Optional state for environment-aware models.

        Returns:
            Realized developmental profile with the same complete ordered
                trait set as ``genetic_phenotype``.
        """
        ...


def realize_developmental_profile(
    development_model: DevelopmentModel,
    genetic_phenotype: GeneticPhenotype,
    *,
    rng: random.Random,
    simulation_state: SimulationState | None = None,
) -> DevelopmentalProfile:
    """Realize and validate developmental targets for a genetic phenotype.

    This is the engine boundary for the ``DevelopmentModel`` invariant. A
    development model may alter target values, but it may not add, remove, or
    reorder traits relative to the genetic phenotype.

    Args:
        development_model: Model used to realize developmental targets.
        genetic_phenotype: Genetically expressed trait values.
        rng: Simulation random-number generator.
        simulation_state: Optional state for environment-aware models.

    Returns:
        Validated developmental profile preserving the complete ordered trait
        set from ``genetic_phenotype``.

    Raises:
        TypeError: If the model returns a non-DevelopmentalProfile value.
        ValueError: If the returned profile changes the genetic phenotype's
            trait names or order.
    """
    developmental_profile = development_model.develop(
        genetic_phenotype,
        rng=rng,
        simulation_state=simulation_state,
    )

    if not isinstance(developmental_profile, DevelopmentalProfile):
        raise TypeError(
            "development_model.develop must return a DevelopmentalProfile; "
            f"received {developmental_profile!r}."
        )

    developmental_profile.validate_against(genetic_phenotype)
    return developmental_profile


@attrs.frozen(slots=True, kw_only=True)
class DeterministicTraitDevelopment:
    """Return a genetically expressed trait value unchanged."""

    def develop(
        self,
        value: ValueT,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> ValueT:
        """Return the supplied trait value unchanged.

        Args:
            value: Genetically expressed trait value.
            rng: Simulation random-number generator.
            simulation_state: Optional simulation state.

        Returns:
            Unchanged trait value.
        """
        return value


@attrs.frozen(slots=True, kw_only=True)
class GaussianIntegerDevelopment:
    """Realize an integer target with Gaussian developmental variation.

    The Gaussian is centered on the genetically expressed value. The sampled
    result is rounded to the nearest integer and then clamped to optional
    inclusive bounds. This models nonheritable developmental variation; it
    does not modify the organism's genome or genetic phenotype.

    Attributes:
        standard_deviation: Gaussian standard deviation in trait-value units.
        minimum: Optional inclusive lower bound on the realized target.
        maximum: Optional inclusive upper bound on the realized target.
    """

    standard_deviation: int | float = attrs.field(
        validator=attrs_validators.validate_number_gt(0),
    )
    minimum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )
    maximum: int | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs_validators.validate_int),
    )

    def __attrs_post_init__(self) -> None:
        """Validate optional developmental bounds."""
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must be less than or equal to maximum.")

    def develop(
        self,
        value: int,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> int:
        """Return a Gaussian realization centered on an integer trait value.

        Args:
            value: Genetically expressed integer trait value.
            rng: Simulation random-number generator.
            simulation_state: Optional simulation state.

        Returns:
            Realized integer developmental target.

        Raises:
            TypeError: If value is not an integer or rng is invalid.
        """
        validated_value = validators.validate_int(
            value,
            name="value",
        )

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        realized_value = round(
            rng.gauss(
                validated_value,
                self.standard_deviation,
            )
        )

        if self.minimum is not None:
            realized_value = max(
                realized_value,
                self.minimum,
            )

        if self.maximum is not None:
            realized_value = min(
                realized_value,
                self.maximum,
            )

        return realized_value


@attrs.frozen(slots=True, kw_only=True)
class DeterministicDevelopment:
    """Copy every genetically expressed trait into the developmental profile."""

    @property
    def required_traits(self) -> frozenset[str]:
        """Return no additional trait requirements."""
        return frozenset()

    def develop(
        self,
        genetic_phenotype: GeneticPhenotype,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> DevelopmentalProfile:
        """Return developmental targets identical to the genetic phenotype.

        Args:
            genetic_phenotype: Genetically expressed phenotype.
            rng: Simulation random-number generator.
            simulation_state: Optional simulation state.

        Returns:
            Developmental profile containing unchanged trait values.
        """
        if not isinstance(genetic_phenotype, GeneticPhenotype):
            raise TypeError(
                "genetic_phenotype must be an instance of GeneticPhenotype."
            )

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        return DevelopmentalProfile(
            target_values=genetic_phenotype.trait_values,
        )


@attrs.frozen(slots=True, kw_only=True)
class IndependentDevelopment:
    """Develop configured traits independently and copy all others unchanged.

    Attributes:
        trait_models: ``(trait_name, model)`` pairs for traits that receive a
            specific developmental model. Traits not listed here are copied
            deterministically from the genetic phenotype.
    """

    trait_models: tuple[tuple[str, TraitDevelopmentModel[Any]], ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate configured trait-development models."""
        validators.validate_tuple(
            self.trait_models,
            name="trait_models",
        )

        trait_names: set[str] = set()

        for index, entry in enumerate(self.trait_models):
            if type(entry) is not tuple:
                raise TypeError(f"trait_models[{index}] must be a tuple.")

            if len(entry) != 2:
                raise ValueError(
                    f"trait_models[{index}] must contain exactly two items."
                )

            trait_name, model = entry
            validators.validate_str(
                trait_name,
                name=f"trait_models[{index}][0]",
            )

            if not trait_name.strip():
                raise ValueError(
                    f"trait_models[{index}][0] must not be empty or whitespace."
                )

            if trait_name in trait_names:
                raise ValueError(
                    "trait_models must not contain duplicate trait names; "
                    f"received {trait_name!r}."
                )

            if not callable(getattr(model, "develop", None)):
                raise TypeError(
                    f"trait_models[{index}][1] must provide a callable develop method."
                )

            trait_names.add(trait_name)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits explicitly configured for development."""
        return validate_required_traits(
            frozenset(trait_name for trait_name, _ in self.trait_models)
        )

    def develop(
        self,
        genetic_phenotype: GeneticPhenotype,
        *,
        rng: random.Random,
        simulation_state: SimulationState | None = None,
    ) -> DevelopmentalProfile:
        """Return independently realized developmental targets.

        Args:
            genetic_phenotype: Genetically expressed phenotype.
            rng: Simulation random-number generator.
            simulation_state: Optional state for environment-aware models.

        Returns:
            Developmental profile preserving genetic phenotype trait order.

        Raises:
            KeyError: If a configured trait is absent from the genetic phenotype.
        """
        if not isinstance(genetic_phenotype, GeneticPhenotype):
            raise TypeError(
                "genetic_phenotype must be an instance of GeneticPhenotype."
            )

        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        models_by_trait = dict(self.trait_models)

        # Fail early on misspelled or unavailable configured trait names.
        for trait_name in models_by_trait:
            if trait_name not in genetic_phenotype:
                raise KeyError(
                    f"genetic phenotype has no trait named {trait_name!r}, which is "
                    "required by the development model."
                )

        target_values = tuple(
            (
                trait_name,
                self._develop_trait(
                    trait_name,
                    value,
                    models_by_trait=models_by_trait,
                    rng=rng,
                    simulation_state=simulation_state,
                ),
            )
            for trait_name, value in genetic_phenotype.trait_values
        )

        return DevelopmentalProfile(
            target_values=target_values,
        )

    @staticmethod
    def _develop_trait(
        trait_name: str,
        value: Any,
        *,
        models_by_trait: dict[str, TraitDevelopmentModel[Any]],
        rng: random.Random,
        simulation_state: SimulationState | None,
    ) -> Any:
        """Return one configured or deterministic developmental target."""
        model = models_by_trait.get(trait_name)

        if model is None:
            return value

        return model.develop(
            value,
            rng=rng,
            simulation_state=simulation_state,
        )
