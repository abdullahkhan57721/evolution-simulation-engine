"""Integration tests for pedigree and lifetime-fitness flows."""

from __future__ import annotations

from evo_engine.presets import (
    ReferenceEcologyConfig,
    ReferenceTraitValues,
    build_reference_ecology,
)


def _reproduction_traits(**overrides: int) -> ReferenceTraitValues:
    values = {
        "growth_rate": 0,
        "max_speed": 0,
        "locomotion_cost_coefficient": 0,
        "metabolic_cost_coefficient": 0,
        "energy_conservation_threshold": 0,
        "energy_reserve": 0,
        "maturity_age": 0,
        "reproduction_energy_threshold": 0,
        "offspring_energy": 1,
        "mate_search_range": 3,
        "choosiness": 0,
        "mating_signal": 10,
        "maximum_age": 20,
    }
    values.update(overrides)
    return ReferenceTraitValues(**values)


def test_reference_ecology_records_realized_parentage() -> None:
    """Test a real reference birth updates parent and offspring life histories."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            width=3,
            height=1,
            initial_population=2,
            initial_energy=20,
            max_steps=1,
            seed=11,
            traits=_reproduction_traits(),
        )
    )

    ecology.engine.run(ecology.simulation)

    recorder = ecology.pedigree_recorder
    founders = recorder.founder_ids
    nonfounders = tuple(record for record in recorder.records if not record.is_founder)

    assert len(founders) == 2
    assert len(nonfounders) == 1
    offspring = nonfounders[0]
    assert set(offspring.parent_ids) == set(founders)
    assert offspring.birth_step == 1
    assert all(
        recorder.offspring_of(parent_id) == (offspring.organism_id,)
        for parent_id in founders
    )


def test_reference_ecology_records_maximum_age_death_and_completed_fitness() -> None:
    """Test built-in mortality closes an individual's lifetime fitness record."""
    ecology = build_reference_ecology(
        ReferenceEcologyConfig(
            width=1,
            height=1,
            initial_population=1,
            initial_energy=20,
            max_steps=1,
            seed=13,
            traits=_reproduction_traits(maximum_age=1),
        )
    )

    ecology.engine.run(ecology.simulation)

    founder_id = ecology.pedigree_recorder.founder_ids[0]
    record = ecology.pedigree_recorder.record(founder_id)
    assert not record.is_alive
    assert record.death_step == 1
    assert record.death_cause == "MaximumAgeMortality"
    assert record.lifetime_reproductive_success == 0
