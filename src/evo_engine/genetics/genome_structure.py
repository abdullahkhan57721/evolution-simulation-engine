"""Chromosome-copy structure for biological genomes."""

from __future__ import annotations

from collections import Counter

import attrs

from evo_engine.genetics.genome import Genome
from evo_engine.validation import validators


@attrs.frozen(slots=True, kw_only=True)
class ChromosomeStructure:
    """Declare valid copy counts for one biological chromosome type.

    Copy-count expectations are chromosome-specific rather than one universal
    organism-level ploidy scalar. Including zero in ``allowed_copy_counts``
    permits a chromosome type to be absent in structurally valid genomes.

    Attributes:
        name: Chromosome type name used by ``Chromosome.name``.
        allowed_copy_counts: Nonempty ordered tuple of allowed copy counts.
    """

    name: str
    allowed_copy_counts: tuple[int, ...]

    def __attrs_post_init__(self) -> None:
        """Validate chromosome identity and allowed copy counts."""
        validators.validate_str(self.name, name="name")
        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace.")

        validators.validate_tuple(
            self.allowed_copy_counts,
            name="allowed_copy_counts",
        )
        if not self.allowed_copy_counts:
            raise ValueError("allowed_copy_counts must contain at least one count.")

        seen: set[int] = set()
        for index, count in enumerate(self.allowed_copy_counts):
            if isinstance(count, bool) or not isinstance(count, int):
                raise TypeError(
                    f"allowed_copy_counts[{index}] must be an int; received {count!r}."
                )
            if count < 0:
                raise ValueError(
                    f"allowed_copy_counts[{index}] must be non-negative; "
                    f"received {count}."
                )
            if count in seen:
                raise ValueError(
                    "allowed_copy_counts must not contain duplicates; "
                    f"duplicate count {count}."
                )
            seen.add(count)


@attrs.frozen(slots=True, kw_only=True)
class GenomeStructure:
    """Declare chromosome types and valid chromosome-copy structures.

    ``Genome`` remains a permissive inherited-state container. This model gives
    those stored chromosome copies biological structural meaning and is composed
    by ``GeneticArchitecture``.

    Attributes:
        chromosomes: Per-chromosome structural declarations.
    """

    chromosomes: tuple[ChromosomeStructure, ...] = ()

    def __attrs_post_init__(self) -> None:
        """Validate chromosome declarations."""
        validators.validate_tuple(self.chromosomes, name="chromosomes")

        names: set[str] = set()
        for index, chromosome in enumerate(self.chromosomes):
            if not isinstance(chromosome, ChromosomeStructure):
                raise TypeError(
                    f"chromosomes[{index}] must be a ChromosomeStructure; "
                    f"received {chromosome!r}."
                )
            if chromosome.name in names:
                raise ValueError(
                    "genome structure chromosome names must be unique; "
                    f"duplicate name {chromosome.name!r}."
                )
            names.add(chromosome.name)

    @property
    def chromosome_names(self) -> tuple[str, ...]:
        """Return declared chromosome names in configuration order."""
        return tuple(chromosome.name for chromosome in self.chromosomes)

    def chromosome(self, name: str) -> ChromosomeStructure:
        """Return one chromosome structural declaration by name.

        Args:
            name: Chromosome type name.

        Returns:
            Matching chromosome structure.

        Raises:
            KeyError: If no chromosome type with that name is declared.
        """
        for chromosome in self.chromosomes:
            if chromosome.name == name:
                return chromosome
        raise KeyError(f"unknown chromosome type {name!r}.")

    def validate_genome(self, genome: Genome) -> None:
        """Validate a genome against chromosome-specific copy expectations.

        Args:
            genome: Genome whose chromosome-copy structure should be validated.

        Raises:
            TypeError: If ``genome`` is not a ``Genome``.
            ValueError: If a chromosome type is undeclared or its copy count is
                not permitted by this structure.
        """
        if not isinstance(genome, Genome):
            raise TypeError(
                "genome must be an instance of Genome; "
                f"received {genome!r}."
            )

        declared = {chromosome.name: chromosome for chromosome in self.chromosomes}
        actual_counts = Counter(chromosome.name for chromosome in genome.chromosomes)

        for chromosome_name in actual_counts:
            if chromosome_name not in declared:
                raise ValueError(
                    f"genome contains undeclared chromosome type {chromosome_name!r}."
                )

        for chromosome_name, structure in declared.items():
            actual_count = actual_counts.get(chromosome_name, 0)
            if actual_count not in structure.allowed_copy_counts:
                raise ValueError(
                    f"chromosome {chromosome_name!r} has {actual_count} copies; "
                    "allowed copy counts are "
                    f"{structure.allowed_copy_counts}."
                )
