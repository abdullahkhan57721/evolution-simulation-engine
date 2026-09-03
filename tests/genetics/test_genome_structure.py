"""Tests for explicit chromosome-copy structure."""

from __future__ import annotations

import pytest

from evo_engine.genetics import (
    Chromosome,
    ChromosomeCopyExpectation,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    NoMutation,
)


def test_genome_structure_accepts_chromosome_specific_copy_counts() -> None:
    """Test mixed chromosome copy regimes without a global ploidy scalar."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="haploid",
                    allowed_copy_counts=(1,),
                ),
                ChromosomeCopyExpectation(
                    chromosome_name="diploid",
                    allowed_copy_counts=(2,),
                ),
            )
        ),
        loci=(),
        traits=(),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(name="haploid"),
            Chromosome(name="diploid"),
            Chromosome(name="diploid"),
        )
    )

    architecture.validate_genome(genome)


def test_genome_structure_rejects_invalid_copy_count() -> None:
    """Test chromosome-specific dosage validation."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(2, 4),
                ),
            )
        ),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError, match="allowed copy counts"):
        architecture.validate_genome(
            Genome(chromosomes=(Chromosome(name="1"),))
        )


def test_genome_structure_rejects_undeclared_chromosome_type() -> None:
    """Test chromosome identity belongs to explicit genome structure."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(chromosome_expectations=()),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError, match="undeclared chromosome"):
        architecture.validate_genome(
            Genome(chromosomes=(Chromosome(name="unexpected"),))
        )


def test_genetic_architecture_requires_locus_chromosome_declaration() -> None:
    """Test loci cannot implicitly create chromosome types."""
    locus = Locus(
        name="value",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError, match="undeclared chromosome"):
        GeneticArchitecture(
            genome_structure=GenomeStructure(chromosome_expectations=()),
            loci=(locus,),
            traits=(),
        )


def test_copy_expectation_allows_multiple_explicit_structural_states() -> None:
    """Test one chromosome type can permit several intentional copy states."""
    expectation = ChromosomeCopyExpectation(
        chromosome_name="X",
        allowed_copy_counts=(1, 2),
    )

    assert expectation.allows(1)
    assert expectation.allows(2)
    assert not expectation.allows(0)
