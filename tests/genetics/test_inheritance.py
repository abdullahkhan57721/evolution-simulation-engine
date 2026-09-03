"""Tests for clonal and sexual inheritance."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Chromosome,
    ChromosomeStructure,
    ClonalInheritance,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    NoMutation,
    SexualInheritance,
    UniformIntegerMutation,
)


def make_architecture(
    *,
    mutation=None,
) -> tuple[GeneticArchitecture, Locus[int]]:
    """Return one-locus explicitly diploid genetics for inheritance tests."""
    if mutation is None:
        mutation = NoMutation()

    locus = Locus(
        name="value",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(
            minimum=0,
            maximum=100,
        ),
        mutation=mutation,
    )
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(ChromosomeStructure(name="1", allowed_copy_counts=(2,)),)
        ),
        loci=(locus,),
        traits=(),
    )
    return architecture, locus


def make_genome(
    locus: Locus[int],
    first: int,
    second: int,
) -> Genome:
    """Return a diploid one-locus genome."""
    return Genome(
        chromosomes=(
            Chromosome(
                name="1",
                alleles=(locus.create_allele(first),),
            ),
            Chromosome(
                name="1",
                alleles=(locus.create_allele(second),),
            ),
        )
    )


def test_clonal_inheritance_preserves_chromosome_structure() -> None:
    """Test one-parent inheritance without mutation."""
    architecture, locus = make_architecture()
    parent = make_genome(locus, 4, 8)

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert offspring == parent
    assert offspring is not parent


def test_clonal_inheritance_applies_locus_mutation() -> None:
    """Test that copied alleles pass through locus mutation."""
    architecture, locus = make_architecture(
        mutation=UniformIntegerMutation(
            probability_ppm=1_000_000,
            max_change=1,
        )
    )
    parent = make_genome(locus, 50, 50)

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert tuple(allele.value for allele in offspring.alleles_at("value")) != (50, 50)


@pytest.mark.parametrize(
    "parent_genomes",
    [
        (),
        (
            Genome(chromosomes=()),
            Genome(chromosomes=()),
        ),
    ],
)
def test_clonal_inheritance_requires_one_parent(
    parent_genomes: tuple[Genome, ...],
) -> None:
    """Test clonal inheritance owns its one-parent constraint."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(0, 2)),
            )
        ),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError):
        ClonalInheritance().inherit(
            parent_genomes,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_sexual_inheritance_combines_one_gamete_from_each_parent() -> None:
    """Test two-parent Mendelian inheritance."""
    architecture, locus = make_architecture()
    first_parent = make_genome(locus, 1, 2)
    second_parent = make_genome(locus, 10, 20)

    offspring = SexualInheritance().inherit(
        (first_parent, second_parent),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(allele.value for allele in offspring.alleles_at("value"))

    assert len(values) == 2
    assert values[0] in {1, 2}
    assert values[1] in {10, 20}


@pytest.mark.parametrize(
    "parent_genomes",
    [
        (),
        (Genome(chromosomes=()),),
        (
            Genome(chromosomes=()),
            Genome(chromosomes=()),
            Genome(chromosomes=()),
        ),
    ],
)
def test_sexual_inheritance_requires_two_parents(
    parent_genomes: tuple[Genome, ...],
) -> None:
    """Test sexual inheritance owns its two-parent constraint."""
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError):
        SexualInheritance().inherit(
            parent_genomes,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )
