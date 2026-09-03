"""Experimental verification for the flagship max-intake demonstration."""

from __future__ import annotations

import json

from evo_engine.experiments import (
    ReferenceReplicateResult,
    run_flagship_max_intake_replicates,
)
from evo_engine.genetics import MAX_INTAKE_RATE
from evo_engine.presets import (
    FLAGSHIP_HIGH_MAX_INTAKE_RATE,
    FLAGSHIP_MAX_INTAKE_ROBUSTNESS_SEEDS,
    FLAGSHIP_MAX_INTAKE_SEED,
)


def _high_frequency(replicate: ReferenceReplicateResult, step: int) -> float:
    locus = replicate.genetic_history[step].locus(MAX_INTAKE_RATE)
    return locus.allele_frequency(FLAGSHIP_HIGH_MAX_INTAKE_RATE)


def test_flagship_seed_41_has_strong_directional_change_without_extinction() -> None:
    """Test the canonical cinematic run tells the measured evolutionary story."""
    replicate = run_flagship_max_intake_replicates(
        seeds=(FLAGSHIP_MAX_INTAKE_SEED,)
    ).replicates[0]

    assert _high_frequency(replicate, 0) == 0.5
    assert _high_frequency(replicate, 30) > 0.85
    assert replicate.final_population_size > 0
    assert replicate.metadata.completed_steps == 40
    assert replicate.event_count("Predation") == 0

    metadata = json.loads(replicate.metadata.config_json)
    assert metadata["scenario"] == "flagship_max_intake"
    assert metadata["founder_max_intake_rate"] == {"low": 2, "high": 8}
    assert metadata["reference_config"]["mutation_probability_ppm"] == 0


def test_flagship_canonical_seed_set_is_directionally_robust() -> None:
    """Test every evidence-backed robustness seed favors the high-intake allele."""
    experiment = run_flagship_max_intake_replicates()

    assert experiment.seeds == FLAGSHIP_MAX_INTAKE_ROBUSTNESS_SEEDS
    for replicate in experiment.replicates:
        assert _high_frequency(replicate, 0) == 0.5
        assert _high_frequency(replicate, 40) > 0.5
        assert replicate.final_population_size > 0
        assert replicate.event_count("Predation") == 0


def test_flagship_replicate_is_reproducible_for_same_seed() -> None:
    """Test the named demo reconstructs the same committed evidence for one seed."""
    first = run_flagship_max_intake_replicates(seeds=(41,)).replicates[0]
    second = run_flagship_max_intake_replicates(seeds=(41,)).replicates[0]

    assert first.population_history == second.population_history
    assert first.genetic_history == second.genetic_history
    assert first.life_histories == second.life_histories
    assert first.event_counts == second.event_counts
