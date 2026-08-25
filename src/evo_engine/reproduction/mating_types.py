"""Mating-type compatibility and offspring-assignment policies."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Protocol

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


class OffspringMatingTypeModel(Protocol):
    """Determine the immutable mating type assigned to a resolved offspring."""

    def determine_mating_type(
        self,
        parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> str:
        """Return the mating-type label assigned at birth.

        Args:
            parents: Resolved reproductive parents.
            simulation_state: Current simulation state.
            rng: Simulation random-number generator.

        Returns:
            Nonempty mating-type label.
        """
        ...


@attrs.frozen(slots=True, kw_only=True)
class FixedMatingType:
    """Assign every offspring the same mating type.

    Attributes:
        mating_type: Nonempty label assigned to each offspring.
    """

    mating_type: str = attrs.field(validator=attrs_validators.validate_str)

    def __attrs_post_init__(self) -> None:
        """Validate the fixed mating-type label."""
        _validate_mating_type(self.mating_type, name="mating_type")

    def determine_mating_type(
        self,
        parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> str:
        """Return the configured fixed mating-type label."""
        return self.mating_type


@attrs.frozen(slots=True, kw_only=True)
class RandomMatingType:
    """Assign one of several arbitrary mating types with equal probability.

    Attributes:
        mating_types: Nonempty tuple of unique mating-type labels.
    """

    mating_types: tuple[str, ...] = attrs.field(
        validator=attrs_validators.validate_tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate candidate mating types."""
        if not self.mating_types:
            raise ValueError("mating_types must not be empty.")

        seen: set[str] = set()
        for index, mating_type in enumerate(self.mating_types):
            validated = _validate_mating_type(
                mating_type,
                name=f"mating_types[{index}]",
            )
            if validated in seen:
                raise ValueError("mating_types must not contain duplicate labels.")
            seen.add(validated)

    def determine_mating_type(
        self,
        parents: Sequence[Organism],
        *,
        simulation_state: SimulationState,
        rng: random.Random,
    ) -> str:
        """Randomly choose one configured mating type for a resolved offspring."""
        return rng.choice(self.mating_types)


@attrs.frozen(slots=True, kw_only=True)
class DifferentMatingTypes:
    """Require candidate parents to have different mating-type labels.

    The rule is agnostic to the number or names of mating types: any two
    different labels are compatible. More restrictive compatibility matrices
    can be supplied as other mating-compatibility policies without changing the
    organism representation.
    """

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether candidate parents have different mating types."""
        return first_parent.mating_type != second_parent.mating_type


def determine_offspring_mating_type(
    model: OffspringMatingTypeModel,
    parents: Sequence[Organism],
    *,
    simulation_state: SimulationState,
    rng: random.Random,
) -> str:
    """Return and validate a mating-type label produced by an assignment model.

    Args:
        model: Offspring mating-type assignment model.
        parents: Resolved reproductive parents.
        simulation_state: Current simulation state.
        rng: Simulation random-number generator.

    Returns:
        Validated nonempty mating-type label.

    Raises:
        TypeError: If the model does not expose the required method or returns
            a non-string value.
        ValueError: If the returned label is empty or whitespace-only.
    """
    method = getattr(model, "determine_mating_type", None)
    if not callable(method):
        raise TypeError(
            "model must provide a callable determine_mating_type method."
        )

    mating_type = method(
        parents,
        simulation_state=simulation_state,
        rng=rng,
    )
    return _validate_mating_type(mating_type, name="offspring mating type")


def _validate_mating_type(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated
