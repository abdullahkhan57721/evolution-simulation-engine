"""Tests for raw allele and genotype composition observation."""

from __future__ import annotations

from evo_engine.genetics import (
    Chromosome,
    ChromosomeCopyExpectation,
    CompleteDominanceExpression,
    GeneticArchitecture,
    Genome,
    GenomeStructure,
    IntegerAlleleDomain,
    Locus,
    NoMutation,
    Trait,
)
from evo_engine.observation import GeneticCompositionRecorder
from evo_engine.world import Organism, WorldState


def _architecture() -> GeneticArchitecture:
    locus = Locus(
        name="signal",
        chromosome_name="1",
        position=0,
        domain=IntegerAlleleDomain(minimum=0, maximum=1),
        mutation=NoMutation(),
    )
    return GeneticArchitecture(
        genome_structure=GenomeStructure(
            chromosome_expectations=(
                ChromosomeCopyExpectation(
                    chromosome_name="1",
                    allowed_copy_counts=(2,),
                ),
            )
        ),
        loci=(locus,),
        traits=(
            Trait(
                name="signal",
                locus_names=("signal",),
                expression=CompleteDominanceExpression(dominance_order=(1, 0)),
            ),
        ),
    )


def _organism(
    architecture: GeneticArchitecture,
    first: int,
    second: int,
) -> Organism:
    locus = architecture.locus("signal")
    genome = Genome(
        chromosomes=(
            Chromosome(name="1", alleles=(locus.create_allele(first),)),
            Chromosome(name="1", alleles=(locus.create_allele(second),)),
        )
    )
    return Organism.from_genome(
        genetic_architecture=architecture,
        genome=genome,
        energy=10,
    )


def test_recorder_exposes_hidden_genetic_variation_under_dominance() -> None:
    """Test equal expressed phenotypes can have different recorded genotypes."""
    architecture = _architecture()
    homozygous = _organism(architecture, 1, 1)
    heterozygous = _organism(architecture, 1, 0)
    world = WorldState(width=2, height=1)
    world.add_organism(homozygous)
    world.add_organism(heterozygous)
    recorder = GeneticCompositionRecorder(locus_names=("signal",))

    assert homozygous.genetic_phenotype.int_value("signal") == 1
    assert heterozygous.genetic_phenotype.int_value("signal") == 1

    recorder.observe(world, step_index=0)

    composition = recorder.latest
    assert composition is not None
    locus = composition.locus("signal")
    assert locus.organism_count == 2
    assert locus.allele_copy_count == 4
    assert locus.allele_frequency(0) == 0.25
    assert locus.allele_frequency(1) == 0.75
    assert tuple((item.allele_values, item.count) for item in locus.genotypes) == (
        ((0, 1), 1),
        ((1, 1), 1),
    )


def test_genotype_counts_are_unphased() -> None:
    """Test reciprocal allele-copy order contributes to one genotype count."""
    architecture = _architecture()
    world = WorldState(width=2, height=1)
    world.add_organism(_organism(architecture, 1, 0))
    world.add_organism(_organism(architecture, 0, 1))
    recorder = GeneticCompositionRecorder(locus_names=("signal",))

    recorder.observe(world, step_index=0)

    locus = recorder.observations[0].locus("signal")
    assert len(locus.genotypes) == 1
    assert locus.genotypes[0].allele_values == (0, 1)
    assert locus.genotypes[0].count == 2
    assert locus.genotypes[0].frequency == 1.0


def test_empty_population_records_zero_composition() -> None:
    """Test extinct populations retain named loci with zero frequencies."""
    recorder = GeneticCompositionRecorder(locus_names=("signal",))
    world = WorldState(width=1, height=1)

    recorder.observe(world, step_index=0)

    locus = recorder.observations[0].locus("signal")
    assert locus.organism_count == 0
    assert locus.allele_copy_count == 0
    assert locus.alleles == ()
    assert locus.genotypes == ()
