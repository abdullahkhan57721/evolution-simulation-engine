"""Concrete controlled-experiment authoring patterns for the Workbench."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Literal, cast

import attrs

from evo_engine.experiments.e3_performance import (
    E3_SPEED_GRID,
    E3Environment,
    E3ReplicateOutcome,
    E3TreatmentSpecification,
    E3TreatmentSummary,
    build_e3_treatment,
    run_e3_replicate,
    summarize_e3_treatment,
    validate_e3_speed_treatment_integrity,
)
from evo_engine.experiments.e4_selection import (
    E4_FOCAL_SPEEDS,
    E4EnvironmentSummary,
    E4ReplicateOutcome,
    E4TreatmentSpecification,
    build_e4_treatment,
    founder_order_for_replicate,
    run_e4_replicate,
    summarize_e4_environment,
    validate_e4_environment_treatment_integrity,
)
from evo_engine.experiments.science import RunRole
from evo_engine.workbench.controlled_locomotion import (
    EVENT_EVIDENCE_ID,
    MAX_SPEED_SLOT,
    POPULATION_EVIDENCE_ID,
    RESOURCE_GEOGRAPHY_SLOT,
    SEED_SLOT,
    SUPPORTED_MAX_SPEED_MAXIMUM,
    SUPPORTED_MAX_SPEED_MINIMUM,
    SUPPORTED_RESOURCE_GEOGRAPHIES,
    ControlledLocomotionIntent,
    ControlledLocomotionManifest,
    EvidencePlan,
    resolve_controlled_locomotion,
    semantic_diff,
)

EXPERIMENT_DEFINITION_FORMAT_ID = "evolution-experiment-workbench-experiment"
EXPERIMENT_DEFINITION_FORMAT_VERSION = 1

MAX_SPEED_SWEEP_PATTERN_ID = "controlled-locomotion.max-speed-sweep"
ENVIRONMENT_SELECTION_PATTERN_ID = (
    "controlled-locomotion.environment-selection-comparison"
)
INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID = "controlled-locomotion.individual-focal-trait"

E3_SWEEP_REQUIRED_EVIDENCE = frozenset({POPULATION_EVIDENCE_ID, EVENT_EVIDENCE_ID})
E4_COMPARISON_REQUIRED_EVIDENCE = frozenset(
    {
        INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
    }
)
E4_COUNTERBALANCE_ID = "e4-founder-id-cyclic-orders-v1"

TreatmentRole = Literal["control", "treatment"]


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedSweepDefinition:
    """Persist one E3-style user-authored max-speed sweep."""

    base_intent: ControlledLocomotionIntent
    levels: tuple[int, ...] = E3_SPEED_GRID
    seeds: tuple[int, ...]
    factor_slot_id: str = MAX_SPEED_SLOT
    evidence_plan: EvidencePlan = attrs.field(factory=EvidencePlan)
    run_role: RunRole | None = "confirmation"

    def __attrs_post_init__(self) -> None:
        if not isinstance(self.base_intent, ControlledLocomotionIntent):
            raise TypeError("base_intent must be a ControlledLocomotionIntent.")
        if self.factor_slot_id != MAX_SPEED_SLOT:
            raise ValueError(
                f"The max-speed sweep manipulates only {MAX_SPEED_SLOT!r}."
            )
        if self.base_intent.max_speed is not None:
            raise ValueError(
                "base_intent.max_speed must be None because the factor supplies it."
            )
        if self.base_intent.seed is not None:
            raise ValueError(
                "base_intent.seed must be None because replicates supply it."
            )
        if self.base_intent.resource_geography not in SUPPORTED_RESOURCE_GEOGRAPHIES:
            raise ValueError(
                "base_intent.resource_geography must be a supported E3 "
                "resource geography."
            )
        _validate_levels(self.levels)
        _validate_seeds(self.seeds)
        _require_exact_evidence(
            self.evidence_plan,
            required=E3_SWEEP_REQUIRED_EVIDENCE,
            pattern_name="max-speed sweep",
        )
        _validate_run_role(self.run_role)

    def to_json(self) -> str:
        """Serialize the experiment definition canonically."""
        return _canonical_json(
            {
                "base_intent": {
                    "max_speed": self.base_intent.max_speed,
                    "resource_geography": (self.base_intent.resource_geography),
                    "seed": self.base_intent.seed,
                },
                "evidence_ids": list(self.evidence_plan.requested),
                "factor_slot_id": self.factor_slot_id,
                "format_id": EXPERIMENT_DEFINITION_FORMAT_ID,
                "format_version": EXPERIMENT_DEFINITION_FORMAT_VERSION,
                "levels": list(self.levels),
                "pattern_id": MAX_SPEED_SWEEP_PATTERN_ID,
                "run_role": self.run_role,
                "seeds": list(self.seeds),
            }
        )

    @classmethod
    def from_json(cls, value: str) -> MaxSpeedSweepDefinition:
        """Load a stored max-speed sweep without field-path interpretation."""
        mapping = _definition_mapping(
            value,
            expected_pattern_id=MAX_SPEED_SWEEP_PATTERN_ID,
        )
        intent = _required_mapping(mapping, "base_intent")
        return cls(
            base_intent=ControlledLocomotionIntent(
                max_speed=_optional_int(intent, "max_speed"),
                resource_geography=_optional_str(
                    intent,
                    "resource_geography",
                ),
                seed=_optional_int(intent, "seed"),
            ),
            levels=_int_tuple(mapping, "levels"),
            seeds=_int_tuple(mapping, "seeds"),
            factor_slot_id=_required_str(mapping, "factor_slot_id"),
            evidence_plan=EvidencePlan(requested=_str_tuple(mapping, "evidence_ids")),
            run_role=_optional_run_role(mapping, "run_role"),
        )


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedSweepTreatment:
    """Represent one expanded E3 factor-level replicate."""

    factor_level: int
    seed: int
    manifest: ControlledLocomotionManifest

    def __attrs_post_init__(self) -> None:
        if type(self.factor_level) is not int:
            raise TypeError("factor_level must be an integer.")
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer.")
        if not isinstance(self.manifest, ControlledLocomotionManifest):
            raise TypeError("manifest must be a ControlledLocomotionManifest.")
        if self.manifest.explicit_value(MAX_SPEED_SLOT) != self.factor_level:
            raise ValueError("manifest max-speed selection must equal factor_level.")
        if self.manifest.explicit_value(SEED_SLOT) != self.seed:
            raise ValueError("manifest seed must equal treatment seed.")

    @property
    def factor_slot_id(self) -> str:
        """Return the stable semantic factor identity."""
        return MAX_SPEED_SLOT

    def to_e3_treatment(self) -> E3TreatmentSpecification:
        """Reconstruct the existing E3 treatment from the exact manifest."""
        geography = cast(
            E3Environment,
            self.manifest.explicit_value(RESOURCE_GEOGRAPHY_SLOT),
        )
        return build_e3_treatment(
            max_speed=self.factor_level,
            environment=geography,
        )


@attrs.frozen(slots=True, kw_only=True)
class MaxSpeedSweepResult:
    """Preserve expanded treatments and existing E3 scientific results."""

    definition: MaxSpeedSweepDefinition
    treatments: tuple[MaxSpeedSweepTreatment, ...]
    replicate_outcomes: tuple[E3ReplicateOutcome, ...]
    treatment_summaries: tuple[E3TreatmentSummary, ...]


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentSelectionComparisonDefinition:
    """Persist one E4-style matched environment comparison."""

    seeds: tuple[int, ...]
    factor_slot_id: str = RESOURCE_GEOGRAPHY_SLOT
    control_environment: E3Environment = "local_resource"
    treatment_environment: E3Environment = "separated_corridor"
    focal_speeds: tuple[int, int, int] = E4_FOCAL_SPEEDS
    evidence_plan: EvidencePlan = attrs.field(
        factory=lambda: EvidencePlan(
            requested=(
                INDIVIDUAL_FOCAL_TRAIT_EVIDENCE_ID,
                POPULATION_EVIDENCE_ID,
                EVENT_EVIDENCE_ID,
            )
        )
    )
    run_role: RunRole | None = "confirmation"

    def __attrs_post_init__(self) -> None:
        if self.factor_slot_id != RESOURCE_GEOGRAPHY_SLOT:
            raise ValueError(
                f"The E4 comparison manipulates only {RESOURCE_GEOGRAPHY_SLOT!r}."
            )
        if (
            self.control_environment != "local_resource"
            or self.treatment_environment != "separated_corridor"
        ):
            raise ValueError(
                "The E4 comparison preserves the frozen local-resource "
                "control and separated-corridor treatment."
            )
        if self.focal_speeds != E4_FOCAL_SPEEDS:
            raise ValueError(
                "The E4 comparison preserves standing focal composition (1, 3, 9)."
            )
        _validate_seeds(self.seeds)
        _require_exact_evidence(
            self.evidence_plan,
            required=E4_COMPARISON_REQUIRED_EVIDENCE,
            pattern_name="E4 environment comparison",
        )
        _validate_run_role(self.run_role)

    def to_json(self) -> str:
        """Serialize the experiment definition canonically."""
        return _canonical_json(
            {
                "control_environment": self.control_environment,
                "counterbalance_id": E4_COUNTERBALANCE_ID,
                "evidence_ids": list(self.evidence_plan.requested),
                "factor_slot_id": self.factor_slot_id,
                "focal_speeds": list(self.focal_speeds),
                "format_id": EXPERIMENT_DEFINITION_FORMAT_ID,
                "format_version": EXPERIMENT_DEFINITION_FORMAT_VERSION,
                "pattern_id": ENVIRONMENT_SELECTION_PATTERN_ID,
                "run_role": self.run_role,
                "seeds": list(self.seeds),
                "treatment_environment": self.treatment_environment,
            }
        )

    @classmethod
    def from_json(
        cls,
        value: str,
    ) -> EnvironmentSelectionComparisonDefinition:
        """Load a stored E4 comparison without treating counterbalance as a factor."""
        mapping = _definition_mapping(
            value,
            expected_pattern_id=ENVIRONMENT_SELECTION_PATTERN_ID,
        )
        if _required_str(mapping, "counterbalance_id") != E4_COUNTERBALANCE_ID:
            raise ValueError("Unsupported E4 counterbalance identity.")
        focal_speeds = _int_tuple(mapping, "focal_speeds")
        if len(focal_speeds) != 3:
            raise ValueError("focal_speeds must contain exactly three values.")
        return cls(
            seeds=_int_tuple(mapping, "seeds"),
            factor_slot_id=_required_str(mapping, "factor_slot_id"),
            control_environment=cast(
                E3Environment,
                _required_str(mapping, "control_environment"),
            ),
            treatment_environment=cast(
                E3Environment,
                _required_str(mapping, "treatment_environment"),
            ),
            focal_speeds=cast(tuple[int, int, int], focal_speeds),
            evidence_plan=EvidencePlan(requested=_str_tuple(mapping, "evidence_ids")),
            run_role=_optional_run_role(mapping, "run_role"),
        )


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentSelectionTreatment:
    """Represent one expanded E4 arm/replicate with explicit counterbalance."""

    role: TreatmentRole
    seed: int
    founder_speed_order: tuple[int, int, int]
    treatment: E4TreatmentSpecification

    def __attrs_post_init__(self) -> None:
        if self.role not in ("control", "treatment"):
            raise ValueError("role must be control or treatment.")
        if type(self.seed) is not int:
            raise TypeError("seed must be an integer.")
        if not isinstance(self.treatment, E4TreatmentSpecification):
            raise TypeError("treatment must be an E4TreatmentSpecification.")
        if self.founder_speed_order != self.treatment.founder_speed_order:
            raise ValueError("counterbalance order must match the E4 treatment.")

    @property
    def factor_slot_id(self) -> str:
        """Return the stable primary-factor identity."""
        return RESOURCE_GEOGRAPHY_SLOT

    @property
    def factor_level(self) -> E3Environment:
        """Return the resource-environment factor level."""
        return self.treatment.environment

    @property
    def standing_focal_composition(self) -> tuple[int, int, int]:
        """Return composition independently of founder-ID assignment."""
        return E4_FOCAL_SPEEDS


@attrs.frozen(slots=True, kw_only=True)
class EnvironmentSelectionComparisonResult:
    """Preserve expanded treatments and existing E4 scientific results."""

    definition: EnvironmentSelectionComparisonDefinition
    treatments: tuple[EnvironmentSelectionTreatment, ...]
    replicate_outcomes: tuple[E4ReplicateOutcome, ...]
    environment_summaries: tuple[
        E4EnvironmentSummary,
        E4EnvironmentSummary,
    ]


def expand_max_speed_sweep(
    definition: MaxSpeedSweepDefinition,
) -> tuple[MaxSpeedSweepTreatment, ...]:
    """Expand declared E3 factor levels before per-run compilation."""
    if not isinstance(definition, MaxSpeedSweepDefinition):
        raise TypeError("definition must be a MaxSpeedSweepDefinition.")
    geography = cast(
        E3Environment,
        definition.base_intent.resource_geography,
    )
    reference = build_e3_treatment(
        max_speed=definition.levels[0],
        environment=geography,
    )
    expanded: list[MaxSpeedSweepTreatment] = []
    for level in definition.levels:
        treatment = build_e3_treatment(
            max_speed=level,
            environment=geography,
        )
        validate_e3_speed_treatment_integrity(reference, treatment)
        for seed in definition.seeds:
            intent = attrs.evolve(
                definition.base_intent,
                max_speed=level,
                seed=seed,
            )
            manifest = resolve_controlled_locomotion(
                intent,
                definition.evidence_plan,
            )
            expanded.append(
                MaxSpeedSweepTreatment(
                    factor_level=level,
                    seed=seed,
                    manifest=manifest,
                )
            )
    _validate_sweep_manifest_differences(expanded)
    return tuple(expanded)


def run_max_speed_sweep(
    definition: MaxSpeedSweepDefinition,
) -> MaxSpeedSweepResult:
    """Execute an authored sweep through existing E3 analysis semantics."""
    treatments = expand_max_speed_sweep(definition)
    outcomes = tuple(
        run_e3_replicate(
            treatment.to_e3_treatment(),
            seed=treatment.seed,
            run_role=definition.run_role,
        )
        for treatment in treatments
    )
    summaries = tuple(
        summarize_e3_treatment(
            tuple(
                outcome for outcome in outcomes if outcome.treatment.max_speed == level
            )
        )
        for level in definition.levels
    )
    return MaxSpeedSweepResult(
        definition=definition,
        treatments=treatments,
        replicate_outcomes=outcomes,
        treatment_summaries=summaries,
    )


def expand_environment_selection_comparison(
    definition: EnvironmentSelectionComparisonDefinition,
) -> tuple[EnvironmentSelectionTreatment, ...]:
    """Expand matched E4 arms while keeping counterbalance separate."""
    if not isinstance(
        definition,
        EnvironmentSelectionComparisonDefinition,
    ):
        raise TypeError(
            "definition must be an EnvironmentSelectionComparisonDefinition."
        )
    expanded: list[EnvironmentSelectionTreatment] = []
    for index, seed in enumerate(definition.seeds):
        founder_order = founder_order_for_replicate(index)
        control = build_e4_treatment(
            environment=definition.control_environment,
            founder_speed_order=founder_order,
        )
        treatment = build_e4_treatment(
            environment=definition.treatment_environment,
            founder_speed_order=founder_order,
        )
        validate_e4_environment_treatment_integrity(control, treatment)
        expanded.extend(
            (
                EnvironmentSelectionTreatment(
                    role="control",
                    seed=seed,
                    founder_speed_order=founder_order,
                    treatment=control,
                ),
                EnvironmentSelectionTreatment(
                    role="treatment",
                    seed=seed,
                    founder_speed_order=founder_order,
                    treatment=treatment,
                ),
            )
        )
    return tuple(expanded)


def run_environment_selection_comparison(
    definition: EnvironmentSelectionComparisonDefinition,
) -> EnvironmentSelectionComparisonResult:
    """Execute an authored matched comparison through existing E4 analysis."""
    treatments = expand_environment_selection_comparison(definition)
    outcomes = tuple(
        run_e4_replicate(
            expanded.treatment,
            seed=expanded.seed,
            run_role=definition.run_role,
        )
        for expanded in treatments
    )
    control_outcomes = tuple(
        outcome
        for expanded, outcome in zip(treatments, outcomes, strict=True)
        if expanded.role == "control"
    )
    treatment_outcomes = tuple(
        outcome
        for expanded, outcome in zip(treatments, outcomes, strict=True)
        if expanded.role == "treatment"
    )
    summaries = (
        summarize_e4_environment(control_outcomes),
        summarize_e4_environment(treatment_outcomes),
    )
    return EnvironmentSelectionComparisonResult(
        definition=definition,
        treatments=treatments,
        replicate_outcomes=outcomes,
        environment_summaries=summaries,
    )


def _validate_sweep_manifest_differences(
    expanded: Sequence[MaxSpeedSweepTreatment],
) -> None:
    by_seed: dict[int, list[MaxSpeedSweepTreatment]] = {}
    for item in expanded:
        by_seed.setdefault(item.seed, []).append(item)
    for items in by_seed.values():
        reference = items[0]
        for candidate in items[1:]:
            difference = semantic_diff(
                reference.manifest,
                candidate.manifest,
            )
            explicit_ids = {change.slot_id for change in difference.explicit_changes}
            if explicit_ids != {MAX_SPEED_SLOT}:
                raise RuntimeError(
                    "Sweep treatment manifests differ outside the declared "
                    "max-speed factor."
                )


def _validate_levels(levels: tuple[int, ...]) -> None:
    if type(levels) is not tuple:
        raise TypeError("levels must be a tuple.")
    if not levels:
        raise ValueError("levels must contain at least one factor level.")
    if len(levels) != len(set(levels)):
        raise ValueError("levels must not contain duplicates.")
    for index, level in enumerate(levels):
        if type(level) is not int:
            raise TypeError(f"levels[{index}] must be an integer.")
        if not (SUPPORTED_MAX_SPEED_MINIMUM <= level <= SUPPORTED_MAX_SPEED_MAXIMUM):
            raise ValueError(
                "levels must stay within the characterized Workbench max-speed range."
            )


def _validate_seeds(seeds: tuple[int, ...]) -> None:
    if type(seeds) is not tuple:
        raise TypeError("seeds must be a tuple.")
    if not seeds:
        raise ValueError("seeds must contain at least one replicate seed.")
    if len(seeds) != len(set(seeds)):
        raise ValueError("seeds must not contain duplicates.")
    for index, seed in enumerate(seeds):
        if type(seed) is not int:
            raise TypeError(f"seeds[{index}] must be an integer.")


def _require_exact_evidence(
    plan: EvidencePlan,
    *,
    required: frozenset[str],
    pattern_name: str,
) -> None:
    if not isinstance(plan, EvidencePlan):
        raise TypeError("evidence_plan must be an EvidencePlan.")
    requested = set(plan.requested)
    missing = required - requested
    unsupported = requested - required
    if missing:
        raise ValueError(f"{pattern_name} requires evidence IDs {sorted(missing)!r}.")
    if unsupported:
        raise ValueError(
            f"{pattern_name} does not support evidence IDs {sorted(unsupported)!r}."
        )


def _validate_run_role(run_role: RunRole | None) -> None:
    if run_role not in {
        None,
        "discovery",
        "confirmation",
        "representative",
    }:
        raise ValueError(
            "run_role must be discovery, confirmation, representative, or None."
        )


def _canonical_json(mapping: dict[str, object]) -> str:
    return json.dumps(
        mapping,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _definition_mapping(
    value: str,
    *,
    expected_pattern_id: str,
) -> dict[object, object]:
    if type(value) is not str:
        raise TypeError("value must be a string.")
    decoded = json.loads(value)
    if type(decoded) is not dict:
        raise ValueError("experiment JSON must encode an object.")
    if decoded.get("format_id") != EXPERIMENT_DEFINITION_FORMAT_ID:
        raise ValueError("Unsupported Workbench experiment format ID.")
    if decoded.get("format_version") != EXPERIMENT_DEFINITION_FORMAT_VERSION:
        raise ValueError("Unsupported Workbench experiment format version.")
    if decoded.get("pattern_id") != expected_pattern_id:
        raise ValueError("Stored experiment pattern identity does not match.")
    return decoded


def _required_mapping(
    mapping: dict[object, object],
    key: str,
) -> dict[object, object]:
    value = mapping.get(key)
    if type(value) is not dict:
        raise TypeError(f"{key} must be a JSON object.")
    return value


def _required_str(mapping: dict[object, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _optional_str(
    mapping: dict[object, object],
    key: str,
) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not str:
        raise TypeError(f"{key} must be a string or null.")
    return value


def _optional_int(
    mapping: dict[object, object],
    key: str,
) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer or null.")
    return value


def _int_tuple(
    mapping: dict[object, object],
    key: str,
) -> tuple[int, ...]:
    value = mapping.get(key)
    if type(value) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    result: list[int] = []
    for index, item in enumerate(value):
        if type(item) is not int:
            raise TypeError(f"{key}[{index}] must be an integer.")
        result.append(item)
    return tuple(result)


def _str_tuple(
    mapping: dict[object, object],
    key: str,
) -> tuple[str, ...]:
    value = mapping.get(key)
    if type(value) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    result: list[str] = []
    for index, item in enumerate(value):
        if type(item) is not str or not item:
            raise TypeError(f"{key}[{index}] must be a non-empty string.")
        result.append(item)
    return tuple(result)


def _optional_run_role(
    mapping: dict[object, object],
    key: str,
) -> RunRole | None:
    value = mapping.get(key)
    _validate_run_role(cast(RunRole | None, value))
    return cast(RunRole | None, value)
