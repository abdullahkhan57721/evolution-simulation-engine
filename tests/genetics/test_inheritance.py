"""Tests for clonal and sexual inheritance."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    Chromosome,
    ChromosomeAssociation,
    ChromosomeCopyExpectation,
    ClonalInheritance,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    MeioticGameteFormation,
    NoMutation,
    SexualInheritance,
    UniformIntegerMutation,
)


class AdjacentBivalentPairing:
    """Pair an even same-name chromosome group into adjacent test bivalents."""

    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        """Return adjacent pairs without adding production polyploid policy."""
        genetic_architecture.validate_genome(genome)
        chromosomes = genome.chromosomes_named("1")
        if len(chromosomes) % 2 != 0:
            raise ValueError("test pairing requires an even chromosome-copy count.")
        return tuple(
            ChromosomeAssociation(chromosomes=chromosomes[index : index + 2])
            for index in range(0, len(chromosomes), 2)
        )


def make_architecture(
    *,
    mutation=None,
    copy_count: int = 2,
) -> tuple[GeneticArchitecture, Locus[int]]:
    """Return one-locus genetics for inheritance tests."""
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
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(copy_count,),
                ),
            )
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


def make_copy_count_genome(locus: Locus[int], values: tuple[int, ...]) -> Genome:
    """Return a one-locus genome with explicitly supplied chromosome copies."""
    return Genome(
        chromosomes=tuple(
            Chromosome(
                name="1",
                alleles=(locus.create_allele(value),),
            )
            for value in values
        )
    )


def test_clonal_inheritance_preserves_chromosome_structure() -> None:
    """Test one-parent inheritance without mutation."""
    architecture, locus = make_architecture()
    parent = make_genome(
        locus,
        4,
        8,
    )

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert offspring == parent
    assert offspring is not parent


def test_clonal_inheritance_preserves_higher_copy_structure() -> None:
    """Test clonal inheritance is not restricted to diploid genomes."""
    architecture, locus = make_architecture(copy_count=4)
    parent = make_copy_count_genome(locus, (1, 2, 3, 4))

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    assert offspring == parent
    assert len(offspring.chromosomes_named("1")) == 4


def test_clonal_inheritance_applies_locus_mutation() -> None:
    """Test that copied alleles pass through locus mutation."""
    architecture, locus = make_architecture(
        mutation=UniformIntegerMutation(
            probability_ppm=1_000_000,
            max_change=1,
        )
    )
    parent = make_genome(
        locus,
        50,
        50,
    )

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
    architecture, _ = make_architecture()

    with pytest.raises(ValueError):
        ClonalInheritance().inherit(
            parent_genomes,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )


def test_sexual_inheritance_combines_one_gamete_from_each_parent() -> None:
    """Test two-parent Mendelian inheritance."""
    architecture, locus = make_architecture()
    first_parent = make_genome(
        locus,
        1,
        2,
    )
    second_parent = make_genome(
        locus,
        10,
        20,
    )

    offspring = SexualInheritance().inherit(
        (
            first_parent,
            second_parent,
        ),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(allele.value for allele in offspring.alleles_at("value"))

    assert len(values) == 2
    assert values[0] in {1, 2}
    assert values[1] in {10, 20}


def test_sexual_inheritance_supports_four_copy_offspring() -> None:
    """Test inheritance remains neutral to chromosome copies within each gamete."""
    architecture, locus = make_architecture(copy_count=4)
    first_parent = make_copy_count_genome(locus, (1, 2, 3, 4))
    second_parent = make_copy_count_genome(locus, (10, 20, 30, 40))
    inheritance = SexualInheritance(
        gamete_formation=MeioticGameteFormation(
            pairing=AdjacentBivalentPairing(),
        )
    )

    offspring = inheritance.inherit(
        (first_parent, second_parent),
        genetic_architecture=architecture,
        rng=random.Random(1),
    )

    values = tuple(allele.value for allele in offspring.alleles_at("value"))
    assert len(values) == 4
    assert values[0] in {1, 2}
    assert values[1] in {3, 4}
    assert values[2] in {10, 20}
    assert values[3] in {30, 40}


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
        genome_structure=GenomeStructure(chromosome_expectations=()),
        loci=(),
        traits=(),
    )

    with pytest.raises(ValueError):
        SexualInheritance().inherit(
            parent_genomes,
            genetic_architecture=architecture,
            rng=random.Random(1),
        )
