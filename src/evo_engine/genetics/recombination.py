"""Recombination models for exchange within chromosome associations."""

from __future__ import annotations

import random
from typing import Protocol

import attrs

from evo_engine.evolution import (
    LinkageMap,
    UniformLinkageMap,
    sample_linkage_breakpoint,
)
from evo_engine.genetics.chromosome import Chromosome
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.pairing import ChromosomeAssociation
from evo_engine.validation import validators

PROBABILITY_SCALE = 1_000_000


class RecombinationModel(Protocol):
    """Define exchange within an already selected chromosome association."""

    def recombine(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Return an association after any configured recombination.

        Recombination operates only on copies that a pairing policy has already
        made eligible to interact and must preserve association copy cardinality.

        Args:
            association: Chromosome copies already selected to interact.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Chromosome association after any configured exchange.
        """
        ...


def _validate_recombination_inputs(
    association: ChromosomeAssociation,
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> tuple[Chromosome, ...]:
    """Validate inputs shared by recombination implementations."""
    if not isinstance(association, ChromosomeAssociation):
        raise TypeError("association must be an instance of ChromosomeAssociation.")

    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError(
            "genetic_architecture must be an instance of GeneticArchitecture."
        )

    if not isinstance(rng, random.Random):
        raise TypeError("rng must be an instance of random.Random.")

    for chromosome in association.chromosomes:
        _validate_chromosome_alleles(
            chromosome,
            genetic_architecture=genetic_architecture,
        )

    return association.chromosomes


def _validate_same_name_association(
    chromosomes: tuple[Chromosome, ...],
) -> str:
    """Return the shared chromosome name after validating name equality."""
    chromosome_name = chromosomes[0].name

    for chromosome in chromosomes[1:]:
        if chromosome.name != chromosome_name:
            raise ValueError(
                "SingleCrossoverRecombination requires associated chromosomes "
                "to share a chromosome name; received "
                f"{chromosome_name!r} and {chromosome.name!r}."
            )

    return chromosome_name


def _validate_chromosome_alleles(
    chromosome: Chromosome,
    *,
    genetic_architecture: GeneticArchitecture,
) -> None:
    """Validate one associated chromosome's allele-to-locus relationships."""
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
    """Leave an associated set of chromosome copies unchanged."""

    def recombine(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Return a chromosome association unchanged.

        Args:
            association: Chromosome copies already selected to interact.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Unchanged chromosome association.
        """
        _validate_recombination_inputs(
            association,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        return association


@attrs.frozen(slots=True, kw_only=True)
class SingleCrossoverRecombination:
    """Perform at most one crossover within a singleton or bivalent association.

    Locus coordinates supply the baseline linkage geometry: nearby loci have
    fewer possible breakpoint coordinates between them and therefore tend to
    remain associated. ``linkage_map`` can additionally lower breakpoint
    intensity in sticky regions, prevent crossing over entirely, or create
    hotspots. The default uniform map preserves the previous coordinate-based
    behavior.

    Pairing is deliberately outside this model. A higher-copy genome can reuse
    this pairwise crossover policy when a pairing model first organizes its
    chromosome copies into supported bivalent associations.

    Attributes:
        probability_ppm: Probability of attempting crossover in parts per
            million.
        linkage_map: Domain-neutral map controlling local breakpoint intensity.
    """

    probability_ppm: int
    linkage_map: LinkageMap = attrs.field(factory=UniformLinkageMap)

    def __attrs_post_init__(self) -> None:
        """Validate recombination configuration."""
        validators.validate_int_in_range(
            self.probability_ppm,
            lower=0,
            upper=PROBABILITY_SCALE,
            name="probability_ppm",
        )
        try:
            breakpoint_weight = self.linkage_map.breakpoint_weight
        except AttributeError as error:
            raise TypeError(
                "linkage_map must provide a callable breakpoint_weight method."
            ) from error
        if not callable(breakpoint_weight):
            raise TypeError(
                "linkage_map must provide a callable breakpoint_weight method."
            )

    def recombine(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Return an association after an optional single crossover.

        Singleton associations pass through unchanged. Bivalents whose
        chromosomes share a chromosome name may undergo one crossover. Larger
        associations are rejected because this model does not define multivalent
        recombination.

        Args:
            association: Chromosome copies already selected to interact.
            genetic_architecture: Shared genetic architecture.
            rng: Simulation random-number generator.

        Returns:
            Original or recombined chromosome association.

        Raises:
            TypeError: If an input has an invalid type.
            ValueError: If association structure is incompatible with this model.
        """
        chromosomes = _validate_recombination_inputs(
            association,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )

        if len(chromosomes) == 1:
            return association

        if len(chromosomes) != 2:
            raise ValueError(
                "SingleCrossoverRecombination requires a singleton or bivalent "
                "chromosome association."
            )

        chromosome_name = _validate_same_name_association(chromosomes)
        first_homolog, second_homolog = chromosomes

        first_locus_names = {allele.locus_name for allele in first_homolog.alleles}
        second_locus_names = {allele.locus_name for allele in second_homolog.alleles}

        if first_locus_names != second_locus_names:
            raise ValueError(
                "paired homologs must contain the same loci for crossover."
            )

        ordered_loci = tuple(
            sorted(
                (
                    genetic_architecture.locus(locus_name)
                    for locus_name in first_locus_names
                ),
                key=lambda locus: locus.linkage_position,
            )
        )

        if len(ordered_loci) < 2:
            return association

        crossover_roll = rng.randrange(PROBABILITY_SCALE)

        if crossover_roll >= self.probability_ppm:
            return association

        first_position = ordered_loci[0].linkage_position
        last_position = ordered_loci[-1].linkage_position
        crossover_position = self._sample_crossover_position(
            chromosome_name=chromosome_name,
            first_position=first_position,
            last_position=last_position,
            rng=rng,
        )
        if crossover_position is None:
            return association

        first_recombinant_alleles = []
        second_recombinant_alleles = []

        for locus in ordered_loci:
            first_allele = first_homolog.allele_at(locus.name)
            second_allele = second_homolog.allele_at(locus.name)

            if locus.linkage_position <= crossover_position:
                first_recombinant_alleles.append(first_allele)
                second_recombinant_alleles.append(second_allele)
            else:
                first_recombinant_alleles.append(second_allele)
                second_recombinant_alleles.append(first_allele)

        return ChromosomeAssociation(
            chromosomes=(
                Chromosome(
                    name=chromosome_name,
                    alleles=tuple(first_recombinant_alleles),
                ),
                Chromosome(
                    name=chromosome_name,
                    alleles=tuple(second_recombinant_alleles),
                ),
            )
        )

    def _sample_crossover_position(
        self,
        *,
        chromosome_name: str,
        first_position: int,
        last_position: int,
        rng: random.Random,
    ) -> int | None:
        """Return a linkage-map-weighted crossover position."""
        if isinstance(self.linkage_map, UniformLinkageMap):
            if self.linkage_map.relative_rate == 0:
                return None
            # Preserve the historical RNG sequence and uniform physical-distance
            # semantics for the default map.
            return rng.randrange(first_position, last_position)

        return sample_linkage_breakpoint(
            self.linkage_map,
            linkage_group=chromosome_name,
            first_position=first_position,
            last_position=last_position,
            rng=rng,
        )
