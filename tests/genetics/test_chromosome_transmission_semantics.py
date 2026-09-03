"""Tests for explicit chromosome-copy, pairing, and segregation semantics."""

from __future__ import annotations

import random

import pytest

from evo_engine.genetics import (
    BivalentSegregation,
    Chromosome,
    ChromosomeAssociation,
    ChromosomeStructure,
    ClonalInheritance,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    MeioticGameteFormation,
    SameNameBivalentPairing,
    SexualInheritance,
)


def _architecture(*structures: ChromosomeStructure) -> GeneticArchitecture:
    return GeneticArchitecture(
        genome_structure=GenomeStructure(chromosomes=structures),
        loci=(),
        traits=(),
    )


def test_genome_structure_validates_copy_counts_per_chromosome_type() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="A", allowed_copy_counts=(1,)),
        ChromosomeStructure(name="B", allowed_copy_counts=(2,)),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(name="A", alleles=()),
            Chromosome(name="B", alleles=()),
            Chromosome(name="B", alleles=()),
        )
    )

    architecture.validate_genome(genome)


def test_genome_structure_rejects_wrong_copy_count() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(2,)),
    )
    genome = Genome(chromosomes=(Chromosome(name="1", alleles=()),))

    with pytest.raises(ValueError, match="has 1 copies"):
        architecture.validate_genome(genome)


def test_genome_structure_rejects_undeclared_chromosome_type() -> None:
    architecture = _architecture()
    genome = Genome(chromosomes=(Chromosome(name="unexpected", alleles=()),))

    with pytest.raises(ValueError, match="undeclared chromosome type"):
        architecture.validate_genome(genome)


def test_simple_pairing_forms_singleton_and_bivalent_associations() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="A", allowed_copy_counts=(1,)),
        ChromosomeStructure(name="B", allowed_copy_counts=(2,)),
    )
    chromosomes = (
        Chromosome(name="A", alleles=()),
        Chromosome(name="B", alleles=()),
        Chromosome(name="B", alleles=()),
    )
    genome = Genome(chromosomes=chromosomes)

    associations = SameNameBivalentPairing().pair(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(7),
    )

    assert associations == (
        ChromosomeAssociation(chromosomes=(chromosomes[0],)),
        ChromosomeAssociation(chromosomes=chromosomes[1:]),
    )
    assert (
        tuple(
            chromosome
            for association in associations
            for chromosome in association.chromosomes
        )
        == chromosomes
    )


def test_valid_four_copy_genome_can_be_unsupported_by_simple_pairing() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(4,)),
    )
    genome = Genome(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(4))
    )
    architecture.validate_genome(genome)

    with pytest.raises(ValueError, match="supports at most two copies"):
        SameNameBivalentPairing().pair(
            genome,
            genetic_architecture=architecture,
            rng=random.Random(7),
        )


def test_mixed_copy_parent_forms_gamete_without_global_ploidy_rule() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="A", allowed_copy_counts=(1,)),
        ChromosomeStructure(name="B", allowed_copy_counts=(2,)),
    )
    genome = Genome(
        chromosomes=(
            Chromosome(name="A", alleles=()),
            Chromosome(name="B", alleles=()),
            Chromosome(name="B", alleles=()),
        )
    )

    gamete = MeioticGameteFormation().form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(11),
    )

    assert tuple(chromosome.name for chromosome in gamete.chromosomes) == ("A", "B")


class _TwoBivalentPairing:
    def pair(
        self,
        genome: Genome,
        *,
        genetic_architecture: GeneticArchitecture,
        rng: random.Random,
    ) -> tuple[ChromosomeAssociation, ...]:
        del genetic_architecture, rng
        chromosomes = genome.chromosomes_named("1")
        return (
            ChromosomeAssociation(chromosomes=chromosomes[:2]),
            ChromosomeAssociation(chromosomes=chromosomes[2:]),
        )


def test_explicit_pairing_and_segregation_can_form_two_copy_gamete() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(4,)),
    )
    genome = Genome(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(4))
    )
    gamete_formation = MeioticGameteFormation(pairing=_TwoBivalentPairing())

    gamete = gamete_formation.form_gamete(
        genome,
        genetic_architecture=architecture,
        rng=random.Random(13),
    )

    assert len(gamete.chromosomes) == 2
    assert all(chromosome.name == "1" for chromosome in gamete.chromosomes)


def test_sexual_inheritance_combines_two_copy_gametes_into_four_copy_offspring() -> (
    None
):
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(4,)),
    )
    parent = Genome(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(4))
    )
    inheritance = SexualInheritance(
        gamete_formation=MeioticGameteFormation(pairing=_TwoBivalentPairing())
    )

    offspring = inheritance.inherit(
        (parent, parent),
        genetic_architecture=architecture,
        rng=random.Random(17),
    )

    assert len(offspring.chromosomes) == 4
    architecture.validate_genome(offspring)


def test_clonal_inheritance_preserves_valid_four_copy_structure() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(4,)),
    )
    parent = Genome(
        chromosomes=tuple(Chromosome(name="1", alleles=()) for _ in range(4))
    )

    offspring = ClonalInheritance().inherit(
        (parent,),
        genetic_architecture=architecture,
        rng=random.Random(19),
    )

    assert len(offspring.chromosomes) == 4
    architecture.validate_genome(offspring)


def test_bivalent_segregation_transmits_one_copy_per_association() -> None:
    architecture = _architecture(
        ChromosomeStructure(name="1", allowed_copy_counts=(4,)),
    )
    chromosomes = tuple(Chromosome(name="1", alleles=()) for _ in range(4))
    associations = (
        ChromosomeAssociation(chromosomes=chromosomes[:2]),
        ChromosomeAssociation(chromosomes=chromosomes[2:]),
    )

    transmitted = BivalentSegregation().segregate(
        associations,
        genetic_architecture=architecture,
        rng=random.Random(23),
    )

    assert len(transmitted) == 2
    assert transmitted[0] in associations[0].chromosomes
    assert transmitted[1] in associations[1].chromosomes
