"""Tests for recombination and meiotic gamete formation."""

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


def make_two_locus_architecture() -> GeneticArchitecture:
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


def make_two_locus_genome(architecture: GeneticArchitecture) -> Genome:
    left = architecture.locus("left")
    right = architecture.locus("right")
    return Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(left.create_allele(1), right.create_allele(2)),
            ),
            Chromosome(
                name="1",
                alleles=(left.create_allele(8), right.create_allele(9)),
            ),
        )
    )


def test_no_recombination_preserves_selected_association() -> None:
    architecture = make_two_locus_architecture()
    genome = make_two_locus_genome(architecture)
    association = ChromosomeAssociation(chromosomes=genome.chromosomes)

    result = NoRecombination().recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert result is association


def test_single_crossover_recombines_a_selected_pair() -> None:
    architecture = make_two_locus_architecture()
    genome = make_two_locus_genome(architecture)
    association = ChromosomeAssociation(chromosomes=genome.chromosomes)

    result = SingleCrossoverRecombination(probability_ppm=1_000_000).recombine(
        association,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(result.chromosomes) == 2
    observed = {
        tuple(allele.value for allele in chromosome.alleles)
        for chromosome in result.chromosomes
    }
    assert observed == {(1, 9), (8, 2)}


def test_single_crossover_rejects_association_larger_than_two() -> None:
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(3,)),
            )
        ),
        loci=(),
        traits=(),
    )
    association = ChromosomeAssociation(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(3))
    )

    with pytest.raises(ValueError, match="singleton or two-copy"):
        SingleCrossoverRecombination(probability_ppm=1_000_000).recombine(
            association,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_meiotic_gamete_preserves_current_diploid_mendelian_behavior() -> None:
    architecture = make_two_locus_architecture()
    genome = make_two_locus_genome(architecture)

    gamete = MeioticGameteFormation().form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(gamete.chromosomes) == 1
    assert gamete.chromosomes[0] in genome.chromosomes


def test_meiotic_gamete_uses_configured_recombination_before_segregation() -> None:
    architecture = make_two_locus_architecture()
    genome = make_two_locus_genome(architecture)
    formation = MeioticGameteFormation(
        recombination=SingleCrossoverRecombination(probability_ppm=1_000_000)
    )

    gamete = formation.form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(gamete.chromosomes) == 1
    values = tuple(allele.value for allele in gamete.chromosomes[0].alleles)
    assert values in {(1, 9), (8, 2)}
