"""Tests for linkage-map-aware biological recombination."""

from __future__ import annotations

import random

from evo_engine.genetics import (
    Chromosome,
    ChromosomeAssociation,
    ChromosomeStructure,
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


def _architecture() -> GeneticArchitecture:
    return GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(2,)),
            )
        ),
        loci=(
            Locus(
                name="left",
                chromosome_name="1",
                position=0,
                domain=IntegerAlleleDomain(),
                mutation=NoMutation(),
            ),
            Locus(
                name="middle",
                chromosome_name="1",
                position=100,
                domain=IntegerAlleleDomain(),
                mutation=NoMutation(),
            ),
            Locus(
                name="right",
                chromosome_name="1",
                position=200,
                domain=IntegerAlleleDomain(),
                mutation=NoMutation(),
            ),
        ),
        traits=(),
    )


def _association(architecture: GeneticArchitecture) -> ChromosomeAssociation:
    left = architecture.locus("left")
    middle = architecture.locus("middle")
    right = architecture.locus("right")
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(
                    left.create_allele(1),
                    middle.create_allele(2),
                    right.create_allele(3),
                ),
            ),
            Chromosome(
                name="1",
                alleles=(
                    left.create_allele(8),
                    middle.create_allele(9),
                    right.create_allele(10),
                ),
            ),
        )
    )
    return ChromosomeAssociation(chromosomes=genome.chromosomes)


def test_piecewise_zero_rate_can_prevent_crossover() -> None:
    architecture = _architecture()
    association = _association(architecture)
    recombination = SingleCrossoverRecombination(
        probability_ppm=1_000_000,
        linkage_map=PiecewiseLinkageMap(
            intervals=(
                RecombinationInterval(
                    linkage_group="1",
                    start=0,
                    end=200,
                    relative_rate=0,
                ),
            )
        ),
    )

    result = recombination.recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result is association


def test_piecewise_map_constrains_crossover_to_weighted_interval() -> None:
    architecture = _architecture()
    association = _association(architecture)
    recombination = SingleCrossoverRecombination(
        probability_ppm=1_000_000,
        linkage_map=PiecewiseLinkageMap(
            intervals=(
                RecombinationInterval(
                    linkage_group="1",
                    start=0,
                    end=100,
                    relative_rate=0,
                ),
                RecombinationInterval(
                    linkage_group="1",
                    start=100,
                    end=200,
                    relative_rate=1_000_000,
                ),
            )
        ),
    )

    result = recombination.recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(4),
    )

    observed = {
        tuple(allele.value for allele in chromosome.alleles)
        for chromosome in result.chromosomes
    }
    assert observed == {(1, 2, 10), (8, 9, 3)}
