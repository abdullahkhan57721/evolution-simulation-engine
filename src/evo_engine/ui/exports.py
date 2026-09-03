"""Adapt existing experiment exporters to immutable download artifacts."""

from __future__ import annotations

from tempfile import TemporaryDirectory

import attrs

from evo_engine.experiments import (
    ReferenceExperimentResult,
    write_experiment_json,
    write_population_history_csv,
    write_replicate_summary_csv,
)


@attrs.frozen(slots=True, kw_only=True)
class DownloadArtifact:
    """One in-memory file exposed by the portfolio dashboard."""

    filename: str
    mime_type: str
    data: bytes


def build_experiment_downloads(
    result: ReferenceExperimentResult,
) -> tuple[DownloadArtifact, ...]:
    """Return bytes produced by the repository's existing experiment exporters."""
    if not isinstance(result, ReferenceExperimentResult):
        raise TypeError("result must be a ReferenceExperimentResult.")

    with TemporaryDirectory(prefix="evo-engine-ui-") as directory:
        json_path = write_experiment_json(result, f"{directory}/experiment.json")
        summary_path = write_replicate_summary_csv(
            result,
            f"{directory}/replicate_summary.csv",
        )
        history_path = write_population_history_csv(
            result,
            f"{directory}/population_history.csv",
        )
        return (
            DownloadArtifact(
                filename="reference_experiment.json",
                mime_type="application/json",
                data=json_path.read_bytes(),
            ),
            DownloadArtifact(
                filename="reference_replicate_summary.csv",
                mime_type="text/csv",
                data=summary_path.read_bytes(),
            ),
            DownloadArtifact(
                filename="reference_population_history.csv",
                mime_type="text/csv",
                data=history_path.read_bytes(),
            ),
        )
