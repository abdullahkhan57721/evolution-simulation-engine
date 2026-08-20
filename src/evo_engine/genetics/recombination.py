"""Recombination models for meiotic chromosome exchange."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.validation import validators

PROBABILITY_SCALE = 1_000_000


class RecombinationModel(Protocol):
    """Define how homologous chromosomes recombine before segregation."""

    def recombine(
        self,
        homologs: tuple[Chromosome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Return chromosome copies available for meiotic segregation.

        Args:
            homologs: Homologous chromosome copies from one parent.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Chromosome copies after any configured recombination.
        """
        ...


def _validate_recombination_inputs(
    homologs: tuple[Chromosome, ...],
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> str:
    """Validate inputs shared by recombination implementations."""
    validators.validate_tuple(homologs, name="homologs")

    if not homologs:
        raise ValueError("homologs must contain at least one chromosome.")

    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError(
            "genetic_architecture must be an instance of GeneticArchitecture."
        )

    if not isinstance(rng, random.Random):
        raise TypeError("rng must be an instance of random.Random.")

    chromosome_name = _validate_homolog_structure(homologs)

    for chromosome in homologs:
        _validate_chromosome_alleles(
            chromosome,
            genetic_architecture=genetic_architecture,
        )

    return chromosome_name


def _validate_homolog_structure(
    homologs: tuple[Chromosome, ...],
) -> str:
    """Return the shared chromosome name after validating homolog structure."""
    first = homologs[0]
    if not isinstance(first, Chromosome):
        raise TypeError(
            f"homologs[0] must be an instance of Chromosome; received {first!r}."
        )

    chromosome_name = first.name

    for index, chromosome in enumerate(homologs[1:], start=1):
        if not isinstance(chromosome, Chromosome):
            raise TypeError(
                f"homologs[{index}] must be an instance of Chromosome; "
                f"received {chromosome!r}."
            )

        if chromosome.name != chromosome_name:
            raise ValueError(
                "all homologs must have the same chromosome name; "
                f"received {chromosome_name!r} and {chromosome.name!r}."
            )

    return chromosome_name


def _validate_chromosome_alleles(
    chromosome: Chromosome,
    *,
    genetic_architecture: GeneticArchitecture,
) -> None:
    """Validate one homolog's allele-to-locus relationships."""
    for allele in chromosome.alleles:
        try:
            locus = genetic_architecture.locus(allele.locus_name)
        except KeyError as error:
            raise ValueError(
                f"chromosome {chromosome.name!r} contains an allele for "
                f"unknown locus {allele.locus_name!r}."
            ) from error

        if locus.chromosome_name != chromosome.name:
            raise ValueError(
                f"locus {locus.name!r} belongs to chromosome "
                f"{locus.chromosome_name!r}, not {chromosome.name!r}."
            )

        locus.validate_allele(allele)


@attrs.frozen(slots=True, kw_only=True)
class NoRecombination:
    """Leave homologous chromosome copies unchanged before segregation."""

    def recombine(
        self,
        homologs: tuple[Chromosome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Return homologous chromosome copies unchanged.

        Args:
            homologs: Homologous chromosome copies from one parent.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Unchanged homologous chromosome copies.
        """
        _validate_recombination_inputs(
            homologs,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        return homologs


@attrs.frozen(slots=True, kw_only=True)
class SingleCrossoverRecombination:
    """Perform at most one crossover between a pair of homologs.

    A crossover point is sampled uniformly over the integer coordinate span
    between the first and last shared loci. This makes more widely separated
    loci more likely to be separated by crossover than nearby loci.

    Attributes:
        probability_ppm: Probability of crossover in parts per million.
    """

    probability_ppm: int

    def __attrs_post_init__(self) -> None:
        """Validate recombination configuration."""
        validators.validate_int_in_range(
            self.probability_ppm,
            lower=0,
            upper=PROBABILITY_SCALE,
            name="probability_ppm",
        )

    def recombine(
        self,
        homologs: tuple[Chromosome, ...],
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[Chromosome, ...]:
        """Return homologs after an optional single crossover.

        Haploid chromosome groups pass through unchanged. Diploid groups may
        undergo one crossover. Groups with more than two homologs are rejected
        because this model does not define polyploid pairing behavior.

        Args:
            homologs: Homologous chromosome copies from one parent.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Original or recombined chromosome copies.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If homolog structure is incompatible with this model.
        """
        chromosome_name = _validate_recombination_inputs(
            homologs,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )

        if len(homologs) == 1:
            return homologs

        if len(homologs) != 2:
            raise ValueError(
                "SingleCrossoverRecombination requires one or two homologs "
                "per chromosome name."
            )

        first_homolog, second_homolog = homologs

        first_locus_names = {allele.locus_name for allele in first_homolog.alleles}
        second_locus_names = {allele.locus_name for allele in second_homolog.alleles}

        if first_locus_names != second_locus_names:
            raise ValueError(
                "paired homologs must contain the same loci for crossover."
            )

        # Locus positions provide the physical ordering needed to preserve
        # linkage. The crossover point splits both homologs at the same place.
        ordered_loci = tuple(
            sorted(
                (
                    genetic_architecture.locus(locus_name)
                    for locus_name in first_locus_names
                ),
                key=lambda locus: locus.position,
            )
        )

        if len(ordered_loci) < 2:
            return homologs

        crossover_roll = rng.randrange(PROBABILITY_SCALE)

        if crossover_roll >= self.probability_ppm:
            return homologs

        first_position = ordered_loci[0].position
        last_position = ordered_loci[-1].position

        # Sample along the positional span rather than uniformly between
        # locus indices, so widely separated loci have more opportunity to be
        # separated by crossover.
        crossover_position = rng.randrange(
            first_position,
            last_position,
        )

        first_recombinant_alleles = []
        second_recombinant_alleles = []

        for locus in ordered_loci:
            first_allele = first_homolog.allele_at(locus.name)
            second_allele = second_homolog.allele_at(locus.name)

            if locus.position <= crossover_position:
                first_recombinant_alleles.append(first_allele)
                second_recombinant_alleles.append(second_allele)
            else:
                first_recombinant_alleles.append(second_allele)
                second_recombinant_alleles.append(first_allele)

        return (
            Chromosome(
                name=chromosome_name,
                alleles=tuple(first_recombinant_alleles),
            ),
            Chromosome(
                name=chromosome_name,
                alleles=tuple(second_recombinant_alleles),
            ),
        )
