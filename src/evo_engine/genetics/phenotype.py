"""Phenotype representation for expressed organism traits."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import attrs

from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class Phenotype(Mapping[str, Any]):
    """Represent an immutable mapping of expressed trait values.

    Attributes:
        trait_values: Ordered ``(trait_name, value)`` pairs.
    """

    trait_values: tuple[tuple[str, Any], ...]

    def __attrs_post_init__(self) -> None:
        """Validate phenotype trait-value entries."""
        validators.validate_tuple(
            self.trait_values,
            name="trait_values",
        )

        trait_names: set[str] = set()

        for index, entry in enumerate(self.trait_values):
            if type(entry) is not tuple:
                raise TypeError(
                    f"trait_values[{index}] must be a tuple; received {entry!r}."
                )

            if len(entry) != 2:
                raise ValueError(
                    f"trait_values[{index}] must contain exactly two items."
                )

            trait_name, _ = entry

            validators.validate_str(
                trait_name,
                name=f"trait_values[{index}][0]",
            )

            if not trait_name.strip():
                raise ValueError(
                    f"trait_values[{index}][0] must not be empty or whitespace."
                )

            if trait_name in trait_names:
                raise ValueError(
                    "trait_values must not contain duplicate trait names; "
                    f"received {trait_name!r}."
                )

            trait_names.add(trait_name)

    def __getitem__(self, trait_name: str) -> Any:
        """Return an expressed trait value by name.

        Args:
            trait_name: Name of the expressed trait.

        Returns:
            Expressed trait value.

        Raises:
            KeyError: If the phenotype has no trait with the name.
        """
        for name, value in self.trait_values:
            if name == trait_name:
                return value

        raise KeyError(f"phenotype has no trait named {trait_name!r}.")

    def int_value(self, trait_name: str) -> int:
        """Return an expressed trait value as an integer.

        Args:
            trait_name: Name of the expressed trait.

        Returns:
            Integer trait value.

        Raises:
            KeyError: If the phenotype has no trait with the name.
            TypeError: If the expressed value is not an integer.
        """
        return validators.validate_int(
            self[trait_name],
            name=f"phenotype[{trait_name!r}]",
        )

    def __iter__(self) -> Iterator[str]:
        """Iterate over trait names in phenotype order."""
        return (trait_name for trait_name, _ in self.trait_values)

    def __len__(self) -> int:
        """Return the number of expressed traits."""
        return len(self.trait_values)
