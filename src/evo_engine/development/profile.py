"""Represent organism-specific developmental targets."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

import attrs

from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class DevelopmentalProfile(Mapping[str, Any]):
    """Represent immutable organism-specific developmental target values.

    A phenotype stores values expressed deterministically from a genome under
    a genetic architecture. A developmental profile stores the realized
    individual targets produced from those values after developmental and
    environmental variation is applied.

    Attributes:
        target_values: Ordered ``(trait_name, target_value)`` pairs.
    """

    target_values: tuple[tuple[str, Any], ...]

    def __attrs_post_init__(self) -> None:
        """Validate developmental target entries."""
        validators.validate_tuple(
            self.target_values,
            name="target_values",
        )

        target_names: set[str] = set()

        for index, entry in enumerate(self.target_values):
            if type(entry) is not tuple:
                raise TypeError(
                    f"target_values[{index}] must be a tuple; received {entry!r}."
                )

            if len(entry) != 2:
                raise ValueError(
                    f"target_values[{index}] must contain exactly two items."
                )

            target_name, _ = entry
            validators.validate_str(
                target_name,
                name=f"target_values[{index}][0]",
            )

            if not target_name.strip():
                raise ValueError(
                    f"target_values[{index}][0] must not be empty or whitespace."
                )

            if target_name in target_names:
                raise ValueError(
                    "target_values must not contain duplicate target names; "
                    f"received {target_name!r}."
                )

            target_names.add(target_name)

    def __getitem__(self, target_name: str) -> Any:
        """Return a developmental target by name.

        Args:
            target_name: Name of the developmental target.

        Returns:
            Developmental target value.

        Raises:
            KeyError: If the profile has no target with the name.
        """
        for name, value in self.target_values:
            if name == target_name:
                return value

        raise KeyError(f"developmental profile has no target named {target_name!r}.")

    def int_value(self, target_name: str) -> int:
        """Return a developmental target as an integer.

        Args:
            target_name: Name of the developmental target.

        Returns:
            Integer developmental target.

        Raises:
            KeyError: If the target is absent.
            TypeError: If the target value is not an integer.
        """
        return validators.validate_int(
            self[target_name],
            name=f"developmental_profile[{target_name!r}]",
        )

    def __iter__(self) -> Iterator[str]:
        """Iterate over target names in profile order."""
        return (target_name for target_name, _ in self.target_values)

    def __len__(self) -> int:
        """Return the number of developmental targets."""
        return len(self.target_values)
