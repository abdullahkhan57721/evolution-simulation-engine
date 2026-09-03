"""Tests for genotype-to-phenotype expression and architecture."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from evo_engine.genetics import (
    AdditiveIntegerExpression,
    Allele,
    ChoiceAlleleDomain,
    Chromosome,
    ChromosomeStructure,
    CompleteDominanceExpression,
    GeneticArchitecture,
    GeneticPhenotype,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeanIntegerExpression,
    NoMutation,
    Trait,
)
from tests.helpers import (
    make_diploid_genome,
    make_integer_architecture,
)


def _diploid_structure() -> GenomeStructure:
    """Return the explicit one-chromosome diploid structure used here."""
    return GenomeStructure(
        chromosomes=(ChromosomeStructure(name="1", allowed_copy_counts=(2,)),)
    )


def test_mean_integer_expression_rounds_half_away_from_zero() -> None:
    """Test explicit integer rounding semantics for quantitative traits."""
    expression = MeanIntegerExpression()

    positive = expression.express(
        alleles_by_locus=MappingProxyType(
            {
                "a": (
                    Allele(locus_name="a", value=1),
                    Allele(locus_name="a", value=2),
                ),
            }
        )
    )
    negative = expression.express(
        alleles_by_locus=MappingProxyType(
            {
                "a": (
                    Allele(locus_name="a", value=-1),
                    Allele(locus_name="a", value=-2),
                ),
            }
        )
    )

    assert positive == 2
    assert negative == -2


def test_additive_expression_sums_multiple_loci() -> None:
    """Test polygenic additive expression."""
    expression = AdditiveIntegerExpression()

    value = expression.express(
        alleles_by_locus={
            "a": (
                Allele(locus_name="a", value=2),
                Allele(locus_name="a", value=3),
            ),
            "b": (Allele(locus_name="b", value=4),),
        }
    )

    assert value == 9


def test_complete_dominance_returns_most_dominant_present_allele() -> None:
    """Test complete-dominance phenotype expression."""
    expression = CompleteDominanceExpression(
        dominance_order=("A", "a"),
    )

    result = expression.express(
        alleles_by_locus={
            "color": (
                Allele(locus_name="color", value="a"),
                Allele(locus_name="color", value="A"),
            )
        }
    )

    assert result == "A"


def test_complete_dominance_rejects_unknown_allele() -> None:
    """Test dominance models fail on undeclared allele values."""
    expression = CompleteDominanceExpression(
        dominance_order=("A", "a"),
    )

    with pytest.raises(ValueError):
        expression.express(
            alleles_by_locus={"color": (Allele(locus_name="color", value="B"),)}
        )


def test_trait_can_express_from_multiple_loci() -> None:
    """Test that Trait is not restricted to one-locus phenotypes."""
    loci = (
        Locus(
            name="a",
            chromosome_name="1",
            position=0,
            domain=IntegerAlleleDomain(),
            mutation=NoMutation(),
        ),
        Locus(
            name="b",
            chromosome_name="1",
            position=10,
            domain=IntegerAlleleDomain(),
            mutation=NoMutation(),
        ),
    )
    trait = Trait(
        name="combined",
        locus_names=("a", "b"),
        expression=AdditiveIntegerExpression(),
    )
    architecture = GeneticArchitecture(
        genome_structure=_diploid_structure(),
        loci=loci,
        traits=(trait,),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(
                    loci[0].create_allele(1),
                    loci[1].create_allele(2),
                ),
            ),
            Chromosome(
                name="1",
                alleles=(
                    loci[0].create_allele(3),
                    loci[1].create_allele(4),
                ),
            ),
        )
    )

    assert trait.express(genome) == 10
    assert architecture.express(genome)["combined"] == 10


def test_architecture_rejects_duplicate_locus_names() -> None:
    """Test unique locus identity within an architecture."""
    first = Locus(
        name="a",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    second = Locus(
        name="a",
        chromosome_name="1",
        position=10,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError):
        GeneticArchitecture(
            genome_structure=_diploid_structure(),
            loci=(first, second),
            traits=(),
        )


def test_architecture_rejects_duplicate_position_on_same_chromosome() -> None:
    """Test unique locus positions within each chromosome definition."""
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
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )

    with pytest.raises(ValueError):
        GeneticArchitecture(
            genome_structure=_diploid_structure(),
            loci=(first, second),
            traits=(),
        )


def test_architecture_rejects_trait_reference_to_unknown_locus() -> None:
    """Test trait-locus reference integrity."""
    trait = Trait(
        name="trait",
        locus_names=("missing",),
        expression=MeanIntegerExpression(),
    )

    with pytest.raises(ValueError):
        GeneticArchitecture(
            genome_structure=GenomeStructure(),
            loci=(),
            traits=(trait,),
        )


def test_architecture_rejects_allele_on_wrong_chromosome() -> None:
    """Test genome allele location against configured locus location."""
    locus = Locus(
        name="a",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(),
        mutation=NoMutation(),
    )
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(0,)),
                ChromosomeStructure(name="2", allowed_copy_counts=(1,)),
            )
        ),
        loci=(locus,),
        traits=(),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="2",
                alleles=(locus.create_allele(1),),
            ),
        )
    )

    with pytest.raises(ValueError):
        architecture.validate_genome(genome)


def test_architecture_requires_loci_needed_for_expression() -> None:
    """Test that phenotype expression cannot silently omit required loci."""
    architecture = make_integer_architecture("adult_body_mass")

    with pytest.raises(ValueError):
        architecture.express(Genome(chromosomes=()))


def test_architecture_expresses_all_traits_in_configured_order() -> None:
    """Test deterministic phenotype ordering."""
    architecture = make_integer_architecture(
        "adult_body_mass",
        "max_speed",
    )
    genome = make_diploid_genome(
        architecture,
        {
            "adult_body_mass": 10,
            "max_speed": 3,
        },
    )

    phenotype = architecture.express(genome)

    assert phenotype.trait_values == (
        ("adult_body_mass", 10),
        ("max_speed", 3),
    )


def test_genetic_phenotype_behaves_as_immutable_mapping() -> None:
    """Test phenotype lookup, iteration, and integer convenience access."""
    phenotype = GeneticPhenotype(
        trait_values=(
            ("adult_body_mass", 10),
            ("color", "A"),
        )
    )

    assert phenotype["adult_body_mass"] == 10
    assert list(phenotype) == [
        "adult_body_mass",
        "color",
    ]
    assert len(phenotype) == 2
    assert phenotype.int_value("adult_body_mass") == 10

    with pytest.raises(TypeError):
        phenotype.int_value("color")


def test_categorical_trait_can_use_dominance_expression() -> None:
    """Test architecture support for categorical dominant/recessive traits."""
    locus = Locus(
        name="color_locus",
        chromosome_name="1",
        position=0,
        domain=ChoiceAlleleDomain(
            values=("A", "a"),
        ),
        mutation=NoMutation(),
    )
    trait = Trait(
        name="color",
        locus_names=("color_locus",),
        expression=CompleteDominanceExpression(
            dominance_order=("A", "a"),
        ),
    )
    architecture = GeneticArchitecture(
        genome_structure=_diploid_structure(),
        loci=(locus,),
        traits=(trait,),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(locus.create_allele("A"),),
            ),
            Chromosome(
                name="1",
                alleles=(locus.create_allele("a"),),
            ),
        )
    )

    assert architecture.express(genome)["color"] == "A"
