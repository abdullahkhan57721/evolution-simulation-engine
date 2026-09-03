"""Tests for chromosome pairing, recombination, segregation, and gametes."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Chromosome,
    ChromosomeAssociation,
    ChromosomeCopyExpectation,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeioticGameteFormation,
    MendelianSegregation,
    NoMutation,
    NoRecombination,
    SameNameBivalentPairing,
    SingleCrossoverRecombination,
)


def make_two_locus_architecture() -> tuple[
    GeneticArchitecture,
    Locus[int],
    Locus[int],
]:
    """Return a diploid two-locus architecture on one chromosome."""
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
                chromosome_expectations=(
                    ChromosomeCopyExpectation(
                        chromosome_name="1",
                        allowed_copy_counts=(2,),
                    ),
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


def test_chromosome_association_rejects_same_copy_twice() -> None:
    """Test an association cannot duplicate one physical chromosome copy."""
    chromosome = Chromosome(name="1")

    with pytest.raises(ValueError, match="unique chromosome-copy objects"):
        ChromosomeAssociation(chromosomes=(chromosome, chromosome))


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

    assert result is association


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
    assert len(result.chromosomes) == len(association.chromosomes)


def test_single_crossover_rejects_multivalent_association() -> None:
    """Test pairwise crossover rejects unsupported multivalent exchange."""
    architecture, genome = make_heterozygous_genome()
    homologs = genome.chromosomes_named("1")
    third_copy = Chromosome(name="1", alleles=homologs[0].alleles)
    association = ChromosomeAssociation(chromosomes=homologs + (third_copy,))

    with pytest.raises(ValueError, match="singleton or bivalent"):
        SingleCrossoverRecombination(
            probability_ppm=1_000_000,
        ).recombine(
            association,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_same_name_pairing_forms_one_bivalent_for_diploid_group() -> None:
    """Test current same-name homolog grouping is an explicit pairing policy."""
    architecture, genome = make_heterozygous_genome()

    associations = SameNameBivalentPairing().pair(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(associations) == 1
    assert associations[0].chromosomes == genome.chromosomes


def test_valid_four_copy_genome_can_be_unsupported_by_simple_pairing() -> None:
    """Test structural genome validity is distinct from policy support."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(4,),
                ),
            )
        ),
        loci=(),
        traits=(),
    )
    genome = Genome(chromosomes=tuple(Chromosome(name="1") for _ in range(4)))

    architecture.validate_genome(genome)
    with pytest.raises(ValueError, match="at most two copies"):
        SameNameBivalentPairing().pair(
            genome,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_mendelian_segregation_transmits_one_from_each_bivalent() -> None:
    """Test segregation controls transmitted copy count across associations."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(4,),
                ),
            )
        ),
        loci=(),
        traits=(),
    )
    chromosomes = tuple(Chromosome(name="1") for _ in range(4))
    associations = (
        ChromosomeAssociation(chromosomes=chromosomes[:2]),
        ChromosomeAssociation(chromosomes=chromosomes[2:]),
    )

    transmitted = MendelianSegregation().segregate(
        associations,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(transmitted) == 2
    assert transmitted[0] in associations[0].chromosomes
    assert transmitted[1] in associations[1].chromosomes


def test_meiotic_gamete_supports_mixed_chromosome_copy_structure() -> None:
    """Test one genome may combine singleton and diploid chromosome groups."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="A",
                    allowed_copy_counts=(1,),
                ),
                ChromosomeCopyExpectation(
                    chromosome_name="B",
                    allowed_copy_counts=(2,),
                ),
            )
        ),
        loci=(),
        traits=(),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(name="A"),
            Chromosome(name="B"),
            Chromosome(name="B"),
        )
    )

    gamete = MeioticGameteFormation().form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert len(gamete.chromosomes_named("A")) == 1
    assert len(gamete.chromosomes_named("B")) == 1
    assert len(gamete.chromosomes) == 2


def test_meiotic_gamete_with_recombination_can_transmit_recombinant() -> None:
    """Test crossover integrates with explicit pairing and segregation."""
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
