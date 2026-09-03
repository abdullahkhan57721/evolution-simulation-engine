"""Biological chromosome-copy expectations for genomes."""

from __future__ import annotations

import attrs

from evo_engine.genetics.genome import Genome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class ChromosomeCopyExpectation:
    """Define valid copy counts for one chromosome type.

    Attributes:
        chromosome_name: Chromosome type governed by this expectation.
        allowed_copy_counts: Allowed numbers of copies in a valid genome.
    """

    chromosome_name: str
    allowed_copy_counts: tuple[int, ...]

    def __attrs_post_init__(self) -> None:
        """Validate chromosome identity and allowed copy counts."""
        validators.validate_str(self.chromosome_name, name="chromosome_name")
        if not self.chromosome_name.strip():
            raise ValueError("chromosome_name must not be empty or whitespace.")

        validators.validate_tuple(
            self.allowed_copy_counts,
            name="allowed_copy_counts",
        )
        if not self.allowed_copy_counts:
            raise ValueError("allowed_copy_counts must contain at least one count.")

        seen_counts: set[int] = set()
        for index, copy_count in enumerate(self.allowed_copy_counts):
            validators.validate_int_ge(
                copy_count,
                bound=0,
                name=f"allowed_copy_counts[{index}]",
            )
            if copy_count in seen_counts:
                raise ValueError(
                    "allowed_copy_counts must contain unique counts; "
                    f"duplicate {copy_count}."
                )
            seen_counts.add(copy_count)

    def allows(self, copy_count: int) -> bool:
        """Return whether a chromosome copy count is structurally valid.

        Args:
            copy_count: Number of copies to test.

        Returns:
            True when the count is explicitly allowed.
        """
        validators.validate_int_ge(copy_count, bound=0, name="copy_count")
        return copy_count in self.allowed_copy_counts


@attrs.frozen(slots=True, kw_only=True)
class GenomeStructure:
    """Define chromosome-specific copy structure for valid genomes.

    Genome structure belongs to biological architecture rather than to the
    ``Genome`` data container. A chromosome type may permit one or several
    explicit copy counts; different chromosome types may have different rules.

    Attributes:
        chromosome_expectations: Ordered chromosome-copy expectations.
    """

    chromosome_expectations: tuple[ChromosomeCopyExpectation, ...]

    def __attrs_post_init__(self) -> None:
        """Validate chromosome expectations and identity uniqueness."""
        validators.validate_tuple(
            self.chromosome_expectations,
            name="chromosome_expectations",
        )

        chromosome_names: set[str] = set()
        for index, expectation in enumerate(self.chromosome_expectations):
            if not isinstance(expectation, ChromosomeCopyExpectation):
                raise TypeError(
                    "chromosome_expectations"
                    f"[{index}] must be an instance of ChromosomeCopyExpectation; "
                    f"received {expectation!r}."
                )
            if expectation.chromosome_name in chromosome_names:
                raise ValueError(
                    "chromosome_expectations must have unique chromosome names; "
                    f"duplicate {expectation.chromosome_name!r}."
                )
            chromosome_names.add(expectation.chromosome_name)

    @property
    def chromosome_names(self) -> frozenset[str]:
        """Return chromosome types declared by this genome structure."""
        return frozenset(
            expectation.chromosome_name
            for expectation in self.chromosome_expectations
        )

    def expectation(self, chromosome_name: str) -> ChromosomeCopyExpectation:
        """Return the copy expectation for a chromosome type.

        Args:
            chromosome_name: Chromosome type to retrieve.

        Returns:
            Matching chromosome-copy expectation.

        Raises:
            KeyError: If the chromosome type is not declared.
        """
        validators.validate_str(chromosome_name, name="chromosome_name")
        if not chromosome_name.strip():
            raise ValueError("chromosome_name must not be empty or whitespace.")

        for expectation in self.chromosome_expectations:
            if expectation.chromosome_name == chromosome_name:
                return expectation

        raise KeyError(
            f"genome structure has no chromosome named {chromosome_name!r}."
        )

    def validate_genome(self, genome: Genome) -> None:
        """Validate chromosome identities and copy counts in a genome.

        Args:
            genome: Genome whose chromosome-copy structure is validated.

        Raises:
            TypeError: If genome is not a ``Genome``.
            ValueError: If chromosome identity or copy count is invalid.
        """
        if not isinstance(genome, Genome):
            raise TypeError("genome must be an instance of Genome.")

        declared_names = self.chromosome_names
        unknown_names = tuple(
            dict.fromkeys(
                chromosome.name
                for chromosome in genome.chromosomes
                if chromosome.name not in declared_names
            )
        )
        if unknown_names:
            raise ValueError(
                "genome contains undeclared chromosome type(s): "
                f"{unknown_names!r}."
            )

        for expectation in self.chromosome_expectations:
            copy_count = sum(
                chromosome.name == expectation.chromosome_name
                for chromosome in genome.chromosomes
            )
            if not expectation.allows(copy_count):
                raise ValueError(
                    f"chromosome {expectation.chromosome_name!r} has {copy_count} "
                    "copies; allowed copy counts are "
                    f"{expectation.allowed_copy_counts!r}."
                )
