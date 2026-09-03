"""Tests for biological inheritance models."""

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


def make_architecture(*, mutation_probability_ppm: int = 0) -> GeneticArchitecture:
    """Return a simple explicitly diploid architecture for inheritance tests."""
    mutation = (
        NoMutation()
        if mutation_probability_ppm == 0
        else UniformIntegerMutation(
            probability_ppm=mutation_probability_ppm,
            max_change=1,
        )
    )
    return GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosomes=(
                ChromosomeStructure(name="1", allowed_copy_counts=(2,)),
            )
        ),
        loci=(
            Locus(
                name="value",
                chromosome_name="1",
                position=100,
                domain=IntegerAlleleDomain(),
                mutation=mutation,
            ),
        ),
        traits=(),
    )


def make_genome(architecture: GeneticArchitecture, first: int, second: int) -> Genome:
    """Return one diploid genome for inheritance tests."""
    locus = architecture.locus("value")
    return Genome(
        chromosomes=(
            Chromosome(name="1", alleles=(locus.create_allele(first),)),
            Chromosome(name="1", alleles=(locus.create_allele(second),)),
        )
    )


def test_clonal_inheritance_copies_parent_structure() -> None:
    architecture = make_architecture()
    parent = make_genome(architecture, 3, 7)

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(5),
    )

    assert offspring == parent
    assert offspring is not parent


def test_clonal_inheritance_applies_mutation() -> None:
    architecture = make_architecture(mutation_probability_ppm=1_000_000)
    parent = make_genome(architecture, 3, 7)

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(5),
    )

    assert offspring != parent
    architecture.validate_genome(offspring)


def test_sexual_inheritance_combines_one_gamete_from_each_parent() -> None:
    architecture = make_architecture()
    first_parent = make_genome(architecture, 1, 2)
    second_parent = make_genome(architecture, 8, 9)

    offspring = SexualInheritance().inherit(
        (first_parent, second_parent),
        genetic_architecture=architecture,
        rng=random.Random(4),
    )

    assert len(offspring.chromosomes) == 2
    first_value = offspring.chromosomes[0].allele_at("value").value
    second_value = offspring.chromosomes[1].allele_at("value").value
    assert first_value in {1, 2}
    assert second_value in {8, 9}
    architecture.validate_genome(offspring)


def test_clonal_inheritance_requires_one_parent() -> None:
    architecture = make_architecture()
    parent = make_genome(architecture, 1, 2)

    with pytest.raises(ValueError, match="exactly one parent"):
        ClonalInheritance().inherit(
            (parent, parent),
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_sexual_inheritance_requires_two_parents() -> None:
    architecture = GeneticArchitecture(
        genome_structure=GenomeStructure(),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError, match="exactly two parent"):
        SexualInheritance().inherit(
            (),
            genetic_architecture=architecture,
            rng=random.Random(1),
        )
