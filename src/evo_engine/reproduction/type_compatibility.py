"""Explicit mating-type compatibility policies."""

from __future__ import annotations

import attrs

from evo_engine.engine.simulation_state import SimulationState
from evo_engine.validation import validators
from evo_engine.world.organism import Organism


def _nonblank(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


def _canonical_pair(first: str, second: str) -> tuple[str, str]:
    return (first, second) if first <= second else (second, first)


@attrs.frozen(slots=True, kw_only=True)
class MatingTypeCompatibilityMatrix:
    """Allow only explicitly configured unordered mating-type combinations.

    Unlike ``DifferentMatingTypes``, this policy can represent arbitrary
    compatibility networks, including same-type compatibility, incompatibility
    among particular unlike types, and systems with more than two types.

    Attributes:
        compatible_pairs: Unique unordered pairs of mating-type labels.
    """

    compatible_pairs: tuple[tuple[str, str], ...]

    def __attrs_post_init__(self) -> None:
        """Validate and canonicalize configured compatibility pairs."""
        validators.validate_tuple(self.compatible_pairs, name="compatible_pairs")
        canonical_pairs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for index, pair in enumerate(self.compatible_pairs):
            if type(pair) is not tuple:
                raise TypeError(f"compatible_pairs[{index}] must be a tuple.")
            if len(pair) != 2:
                raise ValueError(
                    f"compatible_pairs[{index}] must contain exactly two labels."
                )
            first = _nonblank(pair[0], name=f"compatible_pairs[{index}][0]")
            second = _nonblank(pair[1], name=f"compatible_pairs[{index}][1]")
            canonical = _canonical_pair(first, second)
            if canonical in seen:
                raise ValueError("compatible_pairs must not contain duplicate pairs.")
            seen.add(canonical)
            canonical_pairs.append(canonical)
        object.__setattr__(self, "compatible_pairs", tuple(canonical_pairs))

    @property
    def required_traits(self) -> frozenset[str]:
        """Return no genetic phenotype trait requirements."""
        return frozenset()

    def __call__(
        self,
        first_parent: Organism,
        second_parent: Organism,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the parents' mating types form an allowed pair."""
        return _canonical_pair(
            first_parent.mating_type,
            second_parent.mating_type,
        ) in self.compatible_pairs
