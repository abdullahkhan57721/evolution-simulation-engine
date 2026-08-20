"""Tests for chromosome, genome, and gamete representations."""

from __future__ import annotations

import pytest

from evo_engine.genetics import Allele, Chromosome, Gamete, Genome


def test_chromosome_preserves_phased_alleles() -> None:
    """Test allele order and lookup within one chromosome copy."""
    first = Allele(
        locus_name="a",
        value=1,
    )
    second = Allele(
        locus_name="b",
        value=2,
    )
    chromosome = Chromosome(
        name="1",
        alleles=(
            first,
            second,
        ),
    )

    assert chromosome.alleles == (first, second)
    assert chromosome.allele_at("b") is second


def test_chromosome_rejects_duplicate_locus() -> None:
    """Test one allele maximum per locus on one chromosome copy."""
    with pytest.raises(ValueError):
        Chromosome(
            name="1",
            alleles=(
                Allele(locus_name="a", value=1),
                Allele(locus_name="a", value=2),
            ),
        )


def test_chromosome_lookup_missing_locus_raises() -> None:
    """Test explicit failure for absent loci."""
    chromosome = Chromosome(
        name="1",
        alleles=(),
    )

    with pytest.raises(KeyError):
        chromosome.allele_at("missing")


def test_genome_groups_homologous_chromosomes() -> None:
    """Test retrieval of multiple chromosome copies by homolog name."""
    first = Chromosome(name="1")
    second = Chromosome(name="1")
    other = Chromosome(name="2")
    genome = Genome(
        chromosomes=(
            first,
            second,
            other,
        )
    )

    assert genome.chromosomes_named("1") == (
        first,
        second,
    )


def test_genome_alleles_at_collects_across_homologs_in_order() -> None:
    """Test genotype retrieval while preserving chromosome order."""
    first = Allele(locus_name="a", value=1)
    second = Allele(locus_name="a", value=2)
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(first,),
            ),
            Chromosome(
                name="1",
                alleles=(second,),
            ),
        )
    )

    assert genome.alleles_at("a") == (
        first,
        second,
    )


def test_empty_genome_is_valid() -> None:
    """Test the no-genetics genome representation."""
    assert Genome(chromosomes=()).chromosomes == ()


def test_gamete_groups_chromosomes_by_name() -> None:
    """Test gamete chromosome lookup."""
    chromosome = Chromosome(name="1")
    gamete = Gamete(
        chromosomes=(chromosome,),
    )

    assert gamete.chromosomes_named("1") == (chromosome,)


def test_genome_rejects_non_chromosomes() -> None:
    """Test genome chromosome-container type safety."""
    with pytest.raises(TypeError):
        Genome(
            chromosomes=("bad",),  # type: ignore[arg-type]
        )


def test_gamete_rejects_non_chromosomes() -> None:
    """Test gamete chromosome-container type safety."""
    with pytest.raises(TypeError):
        Gamete(
            chromosomes=("bad",),  # type: ignore[arg-type]
        )
