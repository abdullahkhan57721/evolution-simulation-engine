"""Tests for recombination and gamete formation."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Chromosome,
    ChromosomeAssociation,
    ChromosomeStructure,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeioticGameteFormation,
    NoMutation,
    NoRecombination,
    SingleCrossoverRecombination,
)


def make_two_locus_architecture() -> tuple[
    GeneticArchitecture,
    Locus[int],
    Locus[int],
]:
    """Return a two-locus explicitly diploid architecture on one chromosome."""
    first = Locus(
        name="a",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    second = Locus(
        name="b",
        chromosome_name="1",
        position=10,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    return (
        GeneticArchitecture(
            genome_structure=GenomeStructure(
                chromosomes=(
                    ChromosomeStructure(name="1", allowed_copy_counts=(2,)),
                )
            ),
            loci=(first, second),
            traits=(),
        ),
        first,
        second,
    )


def make_heterozygous_genome() -> tuple[GeneticArchitecture, Genome]:
    """Return a diploid genome with distinguishable homologs."""
    architecture, first, second = make_two_locus_architecture()
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(
                    first.create_allele(1),
                    second.create_allele(10),
                ),
            ),
            Chromosome(
                name="1",
                alleles=(
                    first.create_allele(2),
                    second.create_allele(20),
                ),
            ),
        )
    )
    return architecture, genome


def test_no_recombination_returns_same_association() -> None:
    """Test explicit preservation when recombination is disabled."""
    architecture, genome = make_heterozygous_genome()
    association = ChromosomeAssociation(chromosomes=genome.chromosomes_named("1"))

    result = NoRecombination().recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result is association


def test_single_crossover_probability_zero_preserves_association() -> None:
    """Test crossover probability boundary at zero."""
    architecture, genome = make_heterozygous_genome()
    association = ChromosomeAssociation(chromosomes=genome.chromosomes_named("1"))

    result = SingleCrossoverRecombination(
        probability_ppm=0,
    ).recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result == association


def test_single_crossover_probability_one_swaps_distal_alleles() -> None:
    """Test one crossover preserves phase on each side of the crossover."""
    architecture, genome = make_heterozygous_genome()
    association = ChromosomeAssociation(chromosomes=genome.chromosomes_named("1"))

    result = SingleCrossoverRecombination(
        probability_ppm=1_000_000,
    ).recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(
        tuple(allele.value for allele in chromosome.alleles)
        for chromosome in result.chromosomes
    )

    assert values == (
        (1, 20),
        (2, 10),
    )


def test_single_crossover_rejects_association_larger_than_two() -> None:
    """Test the current crossover model owns its pair-size limitation."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(ChromosomeStructure(name="1", allowed_copy_counts=(3,)),)
        ),
        loci=(),
        traits=(),
    )
    association = ChromosomeAssociation(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(3))
    )

    with pytest.raises(ValueError):
        SingleCrossoverRecombination(
            probability_ppm=1_000_000,
        ).recombine(
            association,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_meiotic_gamete_preserves_current_mendelian_segregation() -> None:
    """Test current simple diploid segregation remains one copy per bivalent."""
    architecture, genome = make_heterozygous_genome()

    gamete = MeioticGameteFormation().form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(gamete.chromosomes_named("1")) == 1
    assert len(gamete.chromosomes) == 1


def test_meiotic_gamete_with_recombination_can_transmit_recombinant() -> None:
    """Test crossover integrates with explicit segregation."""
    architecture, genome = make_heterozygous_genome()

    gamete = MeioticGameteFormation(
        recombination=SingleCrossoverRecombination(
            probability_ppm=1_000_000,
        )
    ).form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(allele.value for allele in gamete.chromosomes[0].alleles)

    assert values in {
        (1, 20),
        (2, 10),
    }
