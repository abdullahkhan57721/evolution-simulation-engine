"""Allele representation for the genetics domain."""

from __future__ import annotations

from typing import Generic, TypeVar

import attrs

from evo_engine.validation import validators

ValueT = TypeVar("ValueT", covariant=True)


@attrs.frozen(slots=True, kw_only=True)
class Allele(Generic[ValueT]):
    """Represent one inherited value at a genetic locus.

    Attributes:
        locus_name: Name of the locus to which the allele belongs.
        value: Genetic value carried by the allele.
    """

    locus_name: str
    value: ValueT

    def __attrs_post_init__(self) -> None:
        """Validate allele identity fields."""
        validators.validate_str(self.locus_name, name="locus_name")

        if not self.locus_name.strip():
            raise ValueError("locus_name must not be empty or whitespace.")
