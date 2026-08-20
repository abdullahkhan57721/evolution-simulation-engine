"""Tests for recombination and gamete formation."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Chromosome,
    GeneticArchitecture,
    Genome,
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
    """Return a two-locus architecture on one chromosome."""
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


def test_no_recombination_returns_same_homolog_tuple() -> None:
    """Test explicit preservation when recombination is disabled."""
    architecture, genome = make_heterozygous_genome()
    homologs = genome.chromosomes_named("1")

    result = NoRecombination().recombine(
        homologs,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result is homologs


def test_single_crossover_probability_zero_preserves_homologs() -> None:
    """Test crossover probability boundary at zero."""
    architecture, genome = make_heterozygous_genome()
    homologs = genome.chromosomes_named("1")

    result = SingleCrossoverRecombination(
        probability_ppm=0,
    ).recombine(
        homologs,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result == homologs


def test_single_crossover_probability_one_swaps_distal_alleles() -> None:
    """Test one crossover preserves phase on each side of the crossover."""
    architecture, genome = make_heterozygous_genome()
    homologs = genome.chromosomes_named("1")

    result = SingleCrossoverRecombination(
        probability_ppm=1_000_000,
    ).recombine(
        homologs,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(
        tuple(allele.value for allele in chromosome.alleles) for chromosome in result
    )

    assert values == (
        (1, 20),
        (2, 10),
    )


def test_single_crossover_rejects_more_than_two_homologs() -> None:
    """Test that the current crossover model is explicitly diploid."""
    architecture, genome = make_heterozygous_genome()
    homologs = genome.chromosomes_named("1")

    with pytest.raises(ValueError):
        SingleCrossoverRecombination(
            probability_ppm=1_000_000,
        ).recombine(
            homologs + (homologs[0],),
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_meiotic_gamete_contains_one_copy_per_chromosome_name() -> None:
    """Test Mendelian segregation by chromosome type."""
    architecture, genome = make_heterozygous_genome()

    gamete = MeioticGameteFormation().form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(gamete.chromosomes_named("1")) == 1
    assert len(gamete.chromosomes) == 1


def test_meiotic_gamete_with_recombination_can_transmit_recombinant() -> None:
    """Test crossover integrates with segregation."""
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
