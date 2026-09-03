"""Tests for dashboard adapters around canonical experiment exporters."""

from __future__ import annotations

import csv
import io
import json

from evo_engine.ui.exports import build_experiment_downloads
from evo_engine.ui.models import (
    build_curated_config,
    run_dashboard_experiment,
)


def test_experiment_downloads_reuse_existing_json_and_csv_formats() -> None:
    """Test UI downloads contain canonical experiment-export content."""
    result = run_dashboard_experiment(
        build_curated_config(
            max_steps=1,
            initial_population=4,
            width=4,
            height=4,
        ),
        seeds=(7, 9),
    )

    artifacts = build_experiment_downloads(result)

    assert tuple(artifact.filename for artifact in artifacts) == (
        "reference_experiment.json",
        "reference_replicate_summary.csv",
        "reference_population_history.csv",
    )
    payload = json.loads(artifacts[0].data.decode("utf-8"))
    assert [item["metadata"]["seed"] for item in payload["replicates"]] == [7, 9]

    summary_rows = list(csv.DictReader(io.StringIO(artifacts[1].data.decode("utf-8"))))
    assert [int(row["seed"]) for row in summary_rows] == [7, 9]

    history_rows = list(csv.DictReader(io.StringIO(artifacts[2].data.decode("utf-8"))))
    assert {int(row["seed"]) for row in history_rows} == {7, 9}
    assert {int(row["step_index"]) for row in history_rows} == {0, 1}
