"""Recombination models for exchange within paired chromosome associations."""

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
from evo_engine.genetics.chromosome_association import ChromosomeAssociation
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.validation import validators

PROBABILITY_SCALE = 1_000_000


class RecombinationModel(Protocol):
    """Define exchange within an already-selected chromosome association."""

    def recombine(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Return an association after any configured recombination.

        Pairing is a separate biological responsibility. Recombination operates
        only on chromosome copies that a pairing policy has already selected to
        interact and must preserve their copy cardinality.
        """
        ...


def _validate_recombination_inputs(
    association: ChromosomeAssociation,
    *,
    genetic_architecture: GeneticArchitecture,
    rng: random.Random,
) -> str:
    """Validate inputs shared by current recombination implementations."""
    if not isinstance(association, ChromosomeAssociation):
        raise TypeError(
            f"association must be a ChromosomeAssociation; received {association!r}."
        )
    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError(
            "genetic_architecture must be an instance of GeneticArchitecture."
        )
    if not isinstance(rng, random.Random):
        raise TypeError("rng must be an instance of random.Random.")

    chromosome_name = _validate_current_crossover_structure(association.chromosomes)
    for chromosome in association.chromosomes:
        _validate_chromosome_alleles(
            chromosome,
            genetic_architecture=genetic_architecture,
        )
    return chromosome_name


def _validate_current_crossover_structure(
    chromosomes: tuple[Chromosome, ...],
) -> str:
    """Validate the same-name structure required by current crossover models."""
    validators.validate_tuple(chromosomes, name="chromosomes")
    if not chromosomes:
        raise ValueError("chromosome association must not be empty.")

    first = chromosomes[0]
    if not isinstance(first, Chromosome):
        raise TypeError(
            f"chromosomes[0] must be an instance of Chromosome; received {first!r}."
        )
    chromosome_name = first.name

    for index, chromosome in enumerate(chromosomes[1:], start=1):
        if not isinstance(chromosome, Chromosome):
            raise TypeError(
                f"chromosomes[{index}] must be an instance of Chromosome; "
                f"received {chromosome!r}."
            )
        if chromosome.name != chromosome_name:
            raise ValueError(
                "current recombination models require one chromosome type per "
                f"association; received {chromosome_name!r} and {chromosome.name!r}."
            )
    return chromosome_name


def _validate_chromosome_alleles(
    chromosome: Chromosome,
    *,
    genetic_architecture: GeneticArchitecture,
) -> None:
    """Validate one chromosome's allele-to-locus relationships."""
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
    """Leave a selected chromosome association unchanged."""

    def recombine(
        self,
        association: ChromosomeAssociation,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> ChromosomeAssociation:
        """Return the supplied association unchanged."""
        _validate_recombination_inputs(
            association,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        return association


@attrs.frozen(slots=True, kw_only=True)
class SingleCrossoverRecombination:
    """Perform at most one crossover within a singleton or chromosome pair.

    Pairing occurs before this model runs. This implementation supports a
    singleton association unchanged or a two-copy same-name association with at
    most one crossover. Higher-cardinality associations are unsupported by this
    concrete recombination model; that limitation is distinct from whether the
    parent genome itself is structurally valid.

    Locus coordinates supply the baseline linkage geometry. ``linkage_map`` can
    additionally alter local breakpoint intensity. The default uniform map
    preserves the previous coordinate-based crossover behavior.
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
        """Return the association after an optional single crossover."""
        chromosome_name = _validate_recombination_inputs(
            association,
            genetic_architecture=genetic_architecture,
            rng=rng,
        )
        chromosomes = association.chromosomes

        if len(chromosomes) == 1:
            return association
        if len(chromosomes) != 2:
            raise ValueError(
                "SingleCrossoverRecombination requires a singleton or two-copy "
                "chromosome association."
            )

        first_homolog, second_homolog = chromosomes
        first_locus_names = {allele.locus_name for allele in first_homolog.alleles}
        second_locus_names = {allele.locus_name for allele in second_homolog.alleles}
        if first_locus_names != second_locus_names:
            raise ValueError(
                "paired chromosomes must contain the same loci for crossover."
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
            return rng.randrange(first_position, last_position)

        return sample_linkage_breakpoint(
            self.linkage_map,
            linkage_group=chromosome_name,
            first_position=first_position,
            last_position=last_position,
            rng=rng,
        )
