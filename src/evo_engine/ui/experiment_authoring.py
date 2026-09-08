"""UI-only helpers for the concrete Workbench experiment patterns."""

from __future__ import annotations

import attrs

from evo_engine.workbench import (
    E4_COUNTERBALANCE_ID,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    compile_b3_curated,
    expand_environment_selection_comparison,
    expand_max_speed_sweep,
)
from evo_engine.workbench.controlled_locomotion import RESOURCE_GEOGRAPHY_SLOT


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedRunRow:
    """Present one authoritative expanded E3 treatment replicate."""

    maximum_speed: int
    seed: int
    resource_geography: str


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentRunRow:
    """Present one authoritative expanded E4 matched-arm replicate."""

    seed: int
    role: str
    environment: str
    standing_focal_composition: tuple[int, int, int]
    founder_speed_order: tuple[int, int, int]


@attrs.frozen(slots=True, kw_only=True)
class B3CaseCounts:
    """Present authoritative B3 compiled case counts without duplicating design logic."""

    confirmation_pairs: int
    radius_sensitivity_runs: int
    counterbalanced_pairs: int
    total_simulations: int


def parse_integer_sequence(value: str, *, name: str) -> tuple[int, ...]:
    """Parse a comma-separated UI field into integer values."""
    if type(value) is not str:
        raise TypeError("value must be a string.")
    if type(name) is not str or not name:
        raise TypeError("name must be a non-empty string.")
    stripped = value.strip()
    if not stripped:
        return ()
    result: list[int] = []
    for index, item in enumerate(stripped.split(",")):
        candidate = item.strip()
        if not candidate:
            raise ValueError(f"{name} contains an empty value at position {index + 1}.")
        try:
            result.append(int(candidate))
        except ValueError as exc:
            raise ValueError(
                f"{name} value {candidate!r} is not an integer."
            ) from exc
    return tuple(result)


def update_max_speed_sweep(
    definition: MaxSpeedSweepDefinition,
    *,
    levels: tuple[int, ...],
    seeds: tuple[int, ...],
) -> MaxSpeedSweepDefinition:
    """Create a new immutable E3 definition through its existing constructor checks."""
    if not isinstance(definition, MaxSpeedSweepDefinition):
        raise TypeError("definition must be a MaxSpeedSweepDefinition.")
    return attrs.evolve(definition, levels=levels, seeds=seeds)


def update_environment_selection_comparison(
    definition: EnvironmentSelectionComparisonDefinition,
    *,
    seeds: tuple[int, ...],
) -> EnvironmentSelectionComparisonDefinition:
    """Create a new immutable E4 definition while preserving its frozen design."""
    if not isinstance(definition, EnvironmentSelectionComparisonDefinition):
        raise TypeError(
            "definition must be an EnvironmentSelectionComparisonDefinition."
        )
    return attrs.evolve(definition, seeds=seeds)


def max_speed_run_rows(
    definition: MaxSpeedSweepDefinition,
) -> tuple[MaxSpeedRunRow, ...]:
    """Build UI rows only from the authoritative Workbench E3 expansion."""
    return tuple(
        MaxSpeedRunRow(
            maximum_speed=treatment.factor_level,
            seed=treatment.seed,
            resource_geography=str(
                treatment.manifest.explicit_value(RESOURCE_GEOGRAPHY_SLOT)
            ),
        )
        for treatment in expand_max_speed_sweep(definition)
    )


def environment_run_rows(
    definition: EnvironmentSelectionComparisonDefinition,
) -> tuple[EnvironmentRunRow, ...]:
    """Build UI rows only from the authoritative Workbench E4 expansion."""
    return tuple(
        EnvironmentRunRow(
            seed=treatment.seed,
            role=treatment.role,
            environment=treatment.factor_level,
            standing_focal_composition=treatment.standing_focal_composition,
            founder_speed_order=treatment.founder_speed_order,
        )
        for treatment in expand_environment_selection_comparison(definition)
    )


def b3_case_counts(revision: B3StudyRevision) -> B3CaseCounts:
    """Return case counts from authoritative B3 compilation."""
    if not isinstance(revision, B3StudyRevision):
        raise TypeError("revision must be a B3StudyRevision.")
    compiled = compile_b3_curated(revision.manifest, revision.evidence_plan)
    confirmation_pairs = len(compiled.confirmation_pairs)
    radius_sensitivity_runs = len(compiled.radius_sensitivity)
    counterbalanced_pairs = len(compiled.counterbalanced_pairs)
    return B3CaseCounts(
        confirmation_pairs=confirmation_pairs,
        radius_sensitivity_runs=radius_sensitivity_runs,
        counterbalanced_pairs=counterbalanced_pairs,
        total_simulations=(
            confirmation_pairs * 2
            + radius_sensitivity_runs
            + counterbalanced_pairs * 2
        ),
    )


def e4_counterbalance_label() -> str:
    """Return a scientific UI label while retaining the authoritative identity."""
    return f"Founder-order counterbalance ({E4_COUNTERBALANCE_ID})"


__all__ = [
    "B3CaseCounts",
    "EnvironmentRunRow",
    "MaxSpeedRunRow",
    "b3_case_counts",
    "e4_counterbalance_label",
    "environment_run_rows",
    "max_speed_run_rows",
    "parse_integer_sequence",
    "update_environment_selection_comparison",
    "update_max_speed_sweep",
]
