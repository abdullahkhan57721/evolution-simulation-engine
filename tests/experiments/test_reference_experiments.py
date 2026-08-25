"""Tests for reference experiment execution and result export."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from evo_engine.experiments import (
    run_reference_replicates,
    write_experiment_json,
    write_population_history_csv,
    write_replicate_summary_csv,
)
from evo_engine.presets import ReferenceEcologyConfig


def _config() -> ReferenceEcologyConfig:
    return ReferenceEcologyConfig(
        width=4,
        height=4,
        initial_population=4,
        max_steps=2,
        seed=999,
    )


def test_reference_replicates_use_requested_unique_seeds() -> None:
    """Test replicate configuration changes only the requested random seed."""
    config = _config()

    result = run_reference_replicates(config, seeds=(3, 7))

    assert result.seeds == (3, 7)
    assert all(replicate.metadata.completed_steps == 2 for replicate in result.replicates)
    for seed in result.seeds:
        replicate = result.replicate(seed)
        serialized_config = json.loads(replicate.metadata.config_json)
        assert serialized_config["seed"] == seed
        assert serialized_config["width"] == config.width
        assert serialized_config["traits"] == {
            key: getattr(config.traits, key)
            for key in serialized_config["traits"]
        }


def test_reference_replicate_is_reproducible_for_same_seed() -> None:
    """Test independent experiments reproduce the same measured trajectory."""
    first = run_reference_replicates(_config(), seeds=(17,)).replicates[0]
    second = run_reference_replicates(_config(), seeds=(17,)).replicates[0]

    assert first.population_history == second.population_history
    assert first.genetic_history == second.genetic_history
    assert first.life_histories == second.life_histories
    assert first.event_counts == second.event_counts
    assert first.final_population_size == second.final_population_size
    assert first.final_total_resources == second.final_total_resources


def test_reference_replicates_reject_duplicate_seeds() -> None:
    """Test duplicate replicate identities are rejected."""
    with pytest.raises(ValueError, match="duplicate seed"):
        run_reference_replicates(_config(), seeds=(5, 5))


def test_experiment_exports_json_and_csv(tmp_path: Path) -> None:
    """Test experiment outputs are machine-readable and contain every replicate."""
    result = run_reference_replicates(_config(), seeds=(2, 4))

    json_path = write_experiment_json(result, tmp_path / "experiment.json")
    summary_path = write_replicate_summary_csv(result, tmp_path / "summary.csv")
    history_path = write_population_history_csv(result, tmp_path / "history.csv")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert [replicate["metadata"]["seed"] for replicate in payload["replicates"]] == [
        2,
        4,
    ]

    with summary_path.open(encoding="utf-8", newline="") as stream:
        summary_rows = list(csv.DictReader(stream))
    assert [int(row["seed"]) for row in summary_rows] == [2, 4]
    assert all(int(row["completed_steps"]) == 2 for row in summary_rows)

    with history_path.open(encoding="utf-8", newline="") as stream:
        history_rows = list(csv.DictReader(stream))
    assert len(history_rows) == 6
    assert {int(row["seed"]) for row in history_rows} == {2, 4}
    assert "trait_mean:growth_rate" in history_rows[0]
