"""Export experiment results using standard-library file formats."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import attrs

from evo_engine.experiments.reference import ReferenceExperimentResult
from evo_engine.observation import CategoryCounts


def write_experiment_json(
    result: ReferenceExperimentResult,
    path: str | Path,
) -> Path:
    """Write a complete reference experiment result as formatted JSON.

    Args:
        result: Experiment result to serialize.
        path: Destination JSON path.

    Returns:
        Resolved destination path.

    Raises:
        TypeError: If result is not a ReferenceExperimentResult.
    """
    if not isinstance(result, ReferenceExperimentResult):
        raise TypeError("result must be a ReferenceExperimentResult.")
    destination = _prepare_destination(path)
    with destination.open("w", encoding="utf-8") as stream:
        json.dump(
            _to_jsonable(result),
            stream,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        stream.write("\n")
    return destination


def write_replicate_summary_csv(
    result: ReferenceExperimentResult,
    path: str | Path,
) -> Path:
    """Write one summary row per experiment replicate.

    Final mating-type counts are emitted as
    ``final_mating_type_count:<mating-type>`` columns for the union of labels
    observed anywhere in the experiment.

    Args:
        result: Experiment result to summarize.
        path: Destination CSV path.

    Returns:
        Resolved destination path.
    """
    _validate_result(result)
    destination = _prepare_destination(path)
    mating_type_names = _observed_mating_type_names(result)
    fieldnames = (
        "seed",
        "engine_version",
        "python_version",
        "completed_steps",
        "final_population_size",
        "final_carcass_count",
        "final_total_resources",
        "total_births",
        "total_deaths",
        *(f"final_mating_type_count:{name}" for name in mating_type_names),
    )
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for replicate in result.replicates:
            row: dict[str, object] = {
                "seed": replicate.seed,
                "engine_version": replicate.metadata.engine_version,
                "python_version": replicate.metadata.python_version,
                "completed_steps": replicate.metadata.completed_steps,
                "final_population_size": replicate.final_population_size,
                "final_carcass_count": replicate.final_carcass_count,
                "final_total_resources": replicate.final_total_resources,
                "total_births": replicate.total_births,
                "total_deaths": replicate.total_deaths,
            }
            final_counts = _final_mating_type_counts(replicate.population_history)
            for mating_type in mating_type_names:
                row[f"final_mating_type_count:{mating_type}"] = final_counts.count_for(
                    mating_type
                )
            writer.writerow(row)
    return destination


def write_population_history_csv(
    result: ReferenceExperimentResult,
    path: str | Path,
) -> Path:
    """Write replicate population histories in tidy row-per-step form.

    Trait means are emitted as ``trait_mean:<trait-name>`` columns. Mating-type
    counts are emitted as ``mating_type_count:<mating-type>`` columns for the
    union of labels observed anywhere in the experiment. Empty populations
    produce blank mean cells and zero mating-type counts.

    Args:
        result: Experiment result containing population histories.
        path: Destination CSV path.

    Returns:
        Resolved destination path.
    """
    _validate_result(result)
    destination = _prepare_destination(path)
    trait_names = result.replicates[0].metadata.trait_names
    mating_type_names = _observed_mating_type_names(result)
    fieldnames = (
        "seed",
        "step_index",
        "population_size",
        "carcass_count",
        "total_resources",
        "age_mean",
        "energy_mean",
        "body_mass_mean",
        *(f"mating_type_count:{name}" for name in mating_type_names),
        *(f"trait_mean:{name}" for name in trait_names),
    )
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for replicate in result.replicates:
            for observation in replicate.population_history:
                row: dict[str, object] = {
                    "seed": replicate.seed,
                    "step_index": observation.step_index,
                    "population_size": observation.population_size,
                    "carcass_count": observation.carcass_count,
                    "total_resources": observation.total_resources,
                    "age_mean": observation.age.mean,
                    "energy_mean": observation.energy.mean,
                    "body_mass_mean": observation.body_mass.mean,
                }
                for mating_type in mating_type_names:
                    row[f"mating_type_count:{mating_type}"] = (
                        observation.mating_type_counts.count_for(mating_type)
                    )
                for trait_name in trait_names:
                    row[f"trait_mean:{trait_name}"] = observation.trait(
                        trait_name
                    ).summary.mean
                writer.writerow(row)
    return destination


def _observed_mating_type_names(result: ReferenceExperimentResult) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                mating_type
                for replicate in result.replicates
                for observation in replicate.population_history
                for mating_type, _ in observation.mating_type_counts.value_counts
            }
        )
    )


def _final_mating_type_counts(
    population_history: tuple[object, ...],
) -> CategoryCounts:
    if not population_history:
        return CategoryCounts()
    final_observation = population_history[-1]
    mating_type_counts = getattr(final_observation, "mating_type_counts", None)
    if not isinstance(mating_type_counts, CategoryCounts):
        raise TypeError("population_history must contain PopulationObservation values.")
    return mating_type_counts


def _validate_result(result: ReferenceExperimentResult) -> None:
    if not isinstance(result, ReferenceExperimentResult):
        raise TypeError("result must be a ReferenceExperimentResult.")


def _prepare_destination(path: str | Path) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if attrs.has(type(value)):
        return {
            field.name: _to_jsonable(getattr(value, field.name))
            for field in attrs.fields(type(value))
            if not field.name.startswith("_")
        }
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_jsonable(item) for item in value]
    value_type = type(value)
    return {
        "__type__": f"{value_type.__module__}.{value_type.__qualname__}",
        "__repr__": repr(value),
    }
