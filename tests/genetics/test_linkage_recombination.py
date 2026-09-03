"""Tests for linkage-map-controlled biological recombination."""

from __future__ import annotations

import random

from evo_engine.genetics import (
    Chromosome,
    ChromosomeAssociation,
    ChromosomeCopyExpectation,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    NoMutation,
    PiecewiseLinkageMap,
    RecombinationInterval,
    SingleCrossoverRecombination,
)


def test_piecewise_linkage_map_controls_crossover_location() -> None:
    """Test local recombination intensity controls which loci remain linked."""
    loci = tuple(
        Locus(
            name=name,
            chromosome_name="1",
            position=position,
            domain=IntegerAlleleDomain(),
            mutation=NoMutation(),
        )
        for name, position in (("a", 0), ("b", 10), ("c", 20))
    )
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(2,),
                ),
            )
        ),
        loci=loci,
        traits=(),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=tuple(
                    locus.create_allele(value)
                    for locus, value in zip(loci, (1, 2, 3), strict=True)
                ),
            ),
            Chromosome(
                name="1",
                alleles=tuple(
                    locus.create_allele(value)
                    for locus, value in zip(loci, (10, 20, 30), strict=True)
                ),
            ),
        )
    )
    recombination = SingleCrossoverRecombination(
        probability_ppm=1_000_000,
        linkage_map=PiecewiseLinkageMap(
            default_rate=0,
            intervals=(
                RecombinationInterval(
                    linkage_group="1",
                    start=15,
                    end=16,
                    relative_rate=1,
                ),
            ),
        ),
    )

    result = recombination.recombine(
        ChromosomeAssociation(chromosomes=genome.chromosomes_named("1")),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert tuple(allele.value for allele in result.chromosomes[0].alleles) == (
        1,
        2,
        30,
    )
    assert tuple(allele.value for allele in result.chromosomes[1].alleles) == (
        10,
        20,
        3,
    )
