"""Integration tests for raw genetic-composition observation flows."""

from __future__ import annotations

from evo_engine.genetics import GENETIC_ARCHITECTURE, GROWTH_RATE
from evo_engine.presets import ReferenceEcologyConfig, build_reference_ecology


def test_reference_ecology_records_all_loci_each_committed_state() -> None:
    """Test reference runs expose allele/genotype time series for every locus."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            initial_population=4,
            max_steps=2,
            seed=23,
        )
    )

    ecology.engine.run(ecology.simulation)

    observations = ecology.genetic_recorder.observations
    assert tuple(observation.step_index for observation in observations) == (0, 1, 2)
    architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    expected_loci = {locus.name for locus in architecture.loci}
    assert {locus.locus_name for locus in observations[0].loci} == expected_loci

    growth = observations[0].locus(GROWTH_RATE)
    assert growth.organism_count == 4
    assert growth.allele_copy_count == 8
    assert growth.allele_frequency(ecology.config.traits.growth_rate) == 1.0
    assert len(growth.genotypes) == 1
    assert growth.genotypes[0].frequency == 1.0
