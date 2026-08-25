"""Biological adapters for source-agnostic operative characteristics."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import attrs

from evo_engine.validation import validators

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@attrs.frozen(slots=True)
class GeneticPhenotypeCharacteristics:
    """Read operative characteristics from raw genetic phenotype expression."""

    def value_for(
        self,
        entity: Organism,
        characteristic_name: str,
        *,
        context: SimulationState,
    ) -> Any:
        """Return a named genetic-phenotype value.

        Args:
            entity: Organism whose characteristic is requested.
            characteristic_name: Genetic phenotype trait name.
            context: Current simulation state. Accepted for the generic source
                contract; raw genetic expression does not depend on it.

        Returns:
            Raw genetically expressed characteristic value.
        """
        validators.validate_str(characteristic_name, name="characteristic_name")
        if not characteristic_name.strip():
            raise ValueError("characteristic_name must not be blank.")
        return entity.genetic_phenotype[characteristic_name]


@attrs.frozen(slots=True)
class DevelopmentalProfileCharacteristics:
    """Read operative characteristics from realized developmental targets."""

    def value_for(
        self,
        entity: Organism,
        characteristic_name: str,
        *,
        context: SimulationState,
    ) -> Any:
        """Return a named realized developmental value.

        Args:
            entity: Organism whose characteristic is requested.
            characteristic_name: Developmental characteristic name.
            context: Current simulation state. Accepted for the generic source
                contract; cached developmental targets do not depend on it.

        Returns:
            Realized developmental characteristic value.
        """
        validators.validate_str(characteristic_name, name="characteristic_name")
        if not characteristic_name.strip():
            raise ValueError("characteristic_name must not be blank.")
        return entity.developmental_profile[characteristic_name]


def integer_characteristic(
    source: object,
    entity: Organism,
    characteristic_name: str,
    *,
    context: SimulationState,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    """Return a validated integer characteristic from a configured source.

    Args:
        source: Object providing ``value_for``.
        entity: Organism whose characteristic is requested.
        characteristic_name: Characteristic identifier passed to the source.
        context: Current simulation state.
        minimum: Optional inclusive lower bound.
        maximum: Optional inclusive upper bound.

    Returns:
        Validated integer characteristic.

    Raises:
        TypeError: If the source does not provide ``value_for`` or returns a
            non-integer value.
        ValueError: If the value is outside configured bounds.
    """
    value_for = getattr(source, "value_for", None)
    if not callable(value_for):
        raise TypeError("source must provide a callable value_for method.")

    value = validators.validate_int(
        value_for(entity, characteristic_name, context=context),
        name=f"characteristic[{characteristic_name!r}]",
    )
    if minimum is not None and value < minimum:
        raise ValueError(
            f"characteristic[{characteristic_name!r}] must be at least {minimum}; "
            f"received {value}."
        )
    if maximum is not None and value > maximum:
        raise ValueError(
            f"characteristic[{characteristic_name!r}] must be at most {maximum}; "
            f"received {value}."
        )
    return value
