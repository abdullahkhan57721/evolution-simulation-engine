"""Tests for genetic expression and architecture validation."""

from __future__ import annotations

import pytest

from evo_engine.genetics import (
    AdditiveIntegerExpression,
    Chromosome,
    ChromosomeStructure,
    CompleteDominanceExpression,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    NoMutation,
    Trait,
)


def _diploid_structure() -> GenomeStructure:
    return GenomeStructure(
        chromosomes=(
            ChromosomeStructure(name="1", allowed_copy_counts=(2,)),
        )
    )


def test_mean_integer_expression_averages_all_allele_copies() -> None:
    expression = MeanIntegerExpression()
    assert expression.express((2, 4, 9)) == 5


def test_additive_integer_expression_sums_all_allele_copies() -> None:
    expression = AdditiveIntegerExpression()
    assert expression.express((2, 4, 9)) == 15


def test_complete_dominance_uses_configured_rank_not_copy_count() -> None:
    expression = CompleteDominanceExpression(
        dominance_order=("A", "B", "C"),
    )
    assert expression.express(("C", "B", "C")) == "B"


def test_genetic_architecture_expresses_multilocus_traits() -> None:
    first = Locus(
        name="first",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    second = Locus(
        name="second",
        chromosome_name="1",
        position=200,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        genome_structure=_diploid_structure(),
        loci=(first, second),
        traits=(
            Trait(
                name="score",
                locus_names=("first", "second"),
                expression=AdditiveIntegerExpression(),
            ),
        ),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(first.create_allele(1), second.create_allele(2)),
            ),
            Chromosome(
                name="1",
                alleles=(first.create_allele(3), second.create_allele(4)),
            ),
        )
    )

    phenotype = architecture.express(genome)

    assert phenotype.trait("score") == 10


def test_genetic_architecture_rejects_duplicate_locus_names() -> None:
    first = Locus(
        name="duplicate",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    second = Locus(
        name="duplicate",
        chromosome_name="1",
        position=200,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError, match="unique names"):
        GeneticArchitecture(
            genome_structure=_diploid_structure(),
            loci=(first, second),
            traits=(),
        )


def test_genetic_architecture_rejects_duplicate_locus_positions() -> None:
    first = Locus(
        name="first",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    second = Locus(
        name="second",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError, match="unique positions"):
        GeneticArchitecture(
            genome_structure=_diploid_structure(),
            loci=(first, second),
            traits=(),
        )


def test_genetic_architecture_rejects_locus_on_undeclared_chromosome() -> None:
    locus = Locus(
        name="value",
        chromosome_name="2",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError, match="undeclared chromosome type"):
        GeneticArchitecture(
            genome_structure=_diploid_structure(),
            loci=(locus,),
            traits=(),
        )


def test_genetic_architecture_rejects_trait_with_unknown_locus() -> None:
    with pytest.raises(ValueError, match="unknown loci"):
        GeneticArchitecture(
            genome_structure=GenomeStructure(),
            loci=(),
            traits=(
                Trait(
                    name="missing",
                    locus_names=("unknown",),
                    expression=MeanIntegerExpression(),
                ),
            ),
        )


def test_validate_genome_rejects_allele_on_wrong_chromosome() -> None:
    locus = Locus(
        name="value",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(0, 1)),
                ChromosomeStructure(name="2", allowed_copy_counts=(1,)),
            )
        ),
        loci=(locus,),
        traits=(),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(name="2", alleles=(locus.create_allele(3),)),
        )
    )

    with pytest.raises(ValueError, match="belongs to chromosome"):
        architecture.validate_genome(genome)


def test_validate_genome_requires_loci_used_by_traits() -> None:
    locus = Locus(
        name="value",
        chromosome_name="1",
        position=100,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(0, 1)),
            )
        ),
        loci=(locus,),
        traits=(
            Trait(
                name="value",
                locus_names=("value",),
                expression=MeanIntegerExpression(),
            ),
        ),
    )

    with pytest.raises(ValueError, match="missing locus"):
        architecture.express(Genome(chromosomes=()))
