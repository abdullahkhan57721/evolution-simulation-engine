"""Bounded Workbench adapter for the controlled clonal locomotion recipe."""

from __future__ import annotations

import hashlib
import json
from importlib import metadata
from typing import cast

import attrs

from evo_engine.configuration import CompiledSimulation
from evo_engine.experiments.e3_performance import (
    E3_BODY_MASS,
    E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
    E3_HEIGHT,
    E3_HORIZON,
    E3_INITIAL_ENERGY,
    E3_LOCOMOTION_DISTANCE_EXPONENT,
    E3_REPRODUCTION_ENERGY_INVESTMENT,
    E3_REPRODUCTION_MINIMUM_ENERGY,
    E3_RESOURCE_REQUEST_AMOUNT,
    E3_WIDTH,
    E3Environment,
    build_e3_treatment,
)
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import EventRecorder, PopulationRecorder
from evo_engine.presets.controlled_locomotion import build_controlled_locomotion_spec
from evo_engine.workbench.diagnostics import (
    IncompatibleManifestError,
    WorkbenchDiagnostic,
    WorkbenchNotReadyError,
    WorkbenchReadiness,
)

RECIPE_ID = "controlled-clonal-locomotion"
RECIPE_VERSION = 1
COMPILER_ID = "workbench.controlled-clonal-locomotion"
COMPILER_VERSION = 1
ENGINE_DISTRIBUTION = "evolution-simulation-engine"

MAX_SPEED_SLOT = "controlled-locomotion.max-speed"
RESOURCE_GEOGRAPHY_SLOT = "controlled-locomotion.resource-geography"
SEED_SLOT = "controlled-locomotion.seed"

POPULATION_EVIDENCE_ID = "controlled-locomotion.population-focal-trait"
EVENT_EVIDENCE_ID = "controlled-locomotion.committed-events"
SUPPORTED_EVIDENCE_IDS = frozenset({POPULATION_EVIDENCE_ID, EVENT_EVIDENCE_ID})

SUPPORTED_MAX_SPEED_MINIMUM = 1
SUPPORTED_MAX_SPEED_MAXIMUM = 10
SUPPORTED_RESOURCE_GEOGRAPHIES = frozenset({"local_resource", "separated_corridor"})

ManifestScalar = str | int | bool
ValuePairs = tuple[tuple[str, ManifestScalar], ...]


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionIntent:
    """Persist the human-visible semantic selections for the WB1 recipe."""

    max_speed: int | None = None
    resource_geography: str | None = None
    seed: int | None = None

    def __attrs_post_init__(self) -> None:
        if self.max_speed is not None and type(self.max_speed) is not int:
            raise TypeError("max_speed must be an integer or None.")
        if (
            self.resource_geography is not None
            and type(self.resource_geography) is not str
        ):
            raise TypeError("resource_geography must be a string or None.")
        if self.seed is not None and type(self.seed) is not int:
            raise TypeError("seed must be an integer or None.")


@attrs.frozen(slots=True, kw_only=True)
class EvidencePlan:
    """Persist the concrete evidence requested from the WB1 recipe."""

    requested: tuple[str, ...] = (
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
    )

    def __attrs_post_init__(self) -> None:
        if type(self.requested) is not tuple:
            raise TypeError("requested must be a tuple.")
        for index, evidence_id in enumerate(self.requested):
            if type(evidence_id) is not str or not evidence_id.strip():
                raise TypeError(f"requested[{index}] must be a non-empty string.")
        if len(self.requested) != len(set(self.requested)):
            raise ValueError("requested must not contain duplicate evidence IDs.")


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionManifest:
    """Store immutable resolved scientific meaning for one WB1 revision."""

    recipe_id: str
    recipe_version: int
    compiler_id: str
    compiler_version: int
    engine_distribution: str
    engine_version: str
    explicit_values: ValuePairs
    derived_values: ValuePairs

    def __attrs_post_init__(self) -> None:
        _validate_manifest_identity(self)
        _validate_value_pairs(self.explicit_values, name="explicit_values")
        _validate_value_pairs(self.derived_values, name="derived_values")
        explicit_ids = tuple(key for key, _ in self.explicit_values)
        if explicit_ids != (MAX_SPEED_SLOT, RESOURCE_GEOGRAPHY_SLOT, SEED_SLOT):
            raise ValueError(
                "explicit_values must contain the WB1 semantic slots in stable order."
            )

    @property
    def digest(self) -> str:
        """Return a stable content digest for run-to-manifest provenance."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def explicit_value(self, slot_id: str) -> ManifestScalar:
        """Return one explicit value by its stable scientific slot ID."""
        return _value_for(self.explicit_values, slot_id)

    def derived_value(self, slot_id: str) -> ManifestScalar:
        """Return one derived value by its stable scientific slot ID."""
        return _value_for(self.derived_values, slot_id)

    def to_json(self) -> str:
        """Serialize the resolved manifest canonically."""
        return json.dumps(
            {
                "compiler_id": self.compiler_id,
                "compiler_version": self.compiler_version,
                "derived_values": [list(item) for item in self.derived_values],
                "engine_distribution": self.engine_distribution,
                "engine_version": self.engine_version,
                "explicit_values": [list(item) for item in self.explicit_values],
                "recipe_id": self.recipe_id,
                "recipe_version": self.recipe_version,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_json(cls, value: str) -> ControlledLocomotionManifest:
        """Deserialize a persisted manifest without re-resolving authoring intent."""
        if type(value) is not str:
            raise TypeError("value must be a string.")
        decoded = json.loads(value)
        if type(decoded) is not dict:
            raise ValueError("manifest JSON must encode an object.")
        return cls(
            recipe_id=_required_str(decoded, "recipe_id"),
            recipe_version=_required_int(decoded, "recipe_version"),
            compiler_id=_required_str(decoded, "compiler_id"),
            compiler_version=_required_int(decoded, "compiler_version"),
            engine_distribution=_required_str(decoded, "engine_distribution"),
            engine_version=_required_str(decoded, "engine_version"),
            explicit_values=_decode_pairs(decoded, "explicit_values"),
            derived_values=_decode_pairs(decoded, "derived_values"),
        )


@attrs.frozen(slots=True, kw_only=True)
class RuntimeEvidence:
    """Hold fresh mutable recorders reconstructed from one persisted evidence plan."""

    population_recorder: PopulationRecorder | None = None
    event_recorder: EventRecorder | None = None

    @property
    def observers(self) -> tuple[PopulationRecorder, ...]:
        return () if self.population_recorder is None else (self.population_recorder,)

    @property
    def telemetry_observers(self) -> tuple[EventRecorder, ...]:
        return () if self.event_recorder is None else (self.event_recorder,)


@attrs.frozen(slots=True, kw_only=True)
class CompiledControlledLocomotion:
    """Bundle authoritative compilation with recorders that participated in preflight.

    The recorders are the same mutable objects passed into lower-layer dependency
    collection and authoritative preflight.
    """

    compiled: CompiledSimulation
    evidence: RuntimeEvidence


@attrs.frozen(slots=True, kw_only=True)
class SemanticChange:
    """Describe one recipe-scoped scientific value change."""

    slot_id: str
    before: ManifestScalar
    after: ManifestScalar


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionDiff:
    """Separate authored changes from recipe-owned derived consequences."""

    explicit_changes: tuple[SemanticChange, ...]
    derived_changes: tuple[SemanticChange, ...]


def assess_readiness(
    intent: ControlledLocomotionIntent,
    evidence_plan: EvidencePlan | None = None,
) -> WorkbenchReadiness:
    """Check only WB1 support/applicability before authoritative lower preflight."""
    if not isinstance(intent, ControlledLocomotionIntent):
        raise TypeError("intent must be a ControlledLocomotionIntent.")
    plan = EvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, EvidencePlan):
        raise TypeError("evidence_plan must be an EvidencePlan or None.")

    missing: list[WorkbenchDiagnostic] = []
    blocked: list[WorkbenchDiagnostic] = []
    if intent.max_speed is None:
        missing.append(
            _missing(MAX_SPEED_SLOT, "Select max_speed before resolving the study.")
        )
    elif not (
        SUPPORTED_MAX_SPEED_MINIMUM <= intent.max_speed <= SUPPORTED_MAX_SPEED_MAXIMUM
    ):
        blocked.append(
            WorkbenchDiagnostic(
                code="unsupported-value",
                slot_id=MAX_SPEED_SLOT,
                context=RECIPE_ID,
                message=(
                    "WB1 supports max_speed from "
                    f"{SUPPORTED_MAX_SPEED_MINIMUM} through "
                    f"{SUPPORTED_MAX_SPEED_MAXIMUM}."
                ),
                remediation=(
                    "Choose a max_speed inside the characterized WB1 range; the "
                    "broader engine-valid range is not automatically Workbench support."
                ),
            )
        )

    if intent.resource_geography is None:
        missing.append(
            _missing(
                RESOURCE_GEOGRAPHY_SLOT,
                "Select resource geography before resolving the study.",
            )
        )
    elif intent.resource_geography not in SUPPORTED_RESOURCE_GEOGRAPHIES:
        blocked.append(
            WorkbenchDiagnostic(
                code="unsupported-value",
                slot_id=RESOURCE_GEOGRAPHY_SLOT,
                context=RECIPE_ID,
                message="WB1 supports only local_resource and separated_corridor.",
                remediation="Choose one of the two characterized WB1 geographies.",
            )
        )
    if intent.seed is None:
        missing.append(
            _missing(SEED_SLOT, "Select a reproducibility seed before resolving.")
        )
    if not plan.requested:
        missing.append(
            WorkbenchDiagnostic(
                code="missing-evidence",
                context=RECIPE_ID,
                message="Select at least one supported evidence stream.",
                remediation=(
                    "Request population focal-trait evidence, committed events, or both."
                ),
            )
        )
    for evidence_id in plan.requested:
        if evidence_id not in SUPPORTED_EVIDENCE_IDS:
            blocked.append(
                WorkbenchDiagnostic(
                    code="unsupported-evidence",
                    context=evidence_id,
                    message=f"WB1 does not support evidence request {evidence_id!r}.",
                    remediation="Remove the unsupported evidence request for this recipe.",
                )
            )

    if blocked:
        return WorkbenchReadiness(state="blocked", diagnostics=tuple(blocked + missing))
    if missing:
        return WorkbenchReadiness(state="draft", diagnostics=tuple(missing))
    return WorkbenchReadiness(state="ready")


def resolve_controlled_locomotion(
    intent: ControlledLocomotionIntent,
    evidence_plan: EvidencePlan | None = None,
) -> ControlledLocomotionManifest:
    """Resolve semantic authoring intent into an immutable recipe-owned manifest."""
    readiness = assess_readiness(intent, evidence_plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    max_speed = cast(int, intent.max_speed)
    geography = cast(E3Environment, intent.resource_geography)
    seed = cast(int, intent.seed)
    return ControlledLocomotionManifest(
        recipe_id=RECIPE_ID,
        recipe_version=RECIPE_VERSION,
        compiler_id=COMPILER_ID,
        compiler_version=COMPILER_VERSION,
        engine_distribution=ENGINE_DISTRIBUTION,
        engine_version=_installed_engine_version(),
        explicit_values=(
            (MAX_SPEED_SLOT, max_speed),
            (RESOURCE_GEOGRAPHY_SLOT, geography),
            (SEED_SLOT, seed),
        ),
        derived_values=_derived_values(max_speed=max_speed, geography=geography),
    )


def compile_controlled_locomotion(
    manifest: ControlledLocomotionManifest,
    evidence_plan: EvidencePlan | None = None,
) -> CompiledControlledLocomotion:
    """Reconstruct existing typed composition and run authoritative preflight."""
    if not isinstance(manifest, ControlledLocomotionManifest):
        raise TypeError("manifest must be a ControlledLocomotionManifest.")
    _require_current_compatibility(manifest)
    plan = EvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, EvidencePlan):
        raise TypeError("evidence_plan must be an EvidencePlan or None.")
    if not plan.requested:
        raise ValueError("WB1 requires at least one supported evidence stream.")
    unsupported = set(plan.requested) - SUPPORTED_EVIDENCE_IDS
    if unsupported:
        raise ValueError(f"Unsupported WB1 evidence IDs: {sorted(unsupported)!r}.")

    max_speed = _require_exact_int(
        manifest.explicit_value(MAX_SPEED_SLOT), MAX_SPEED_SLOT
    )
    if not (SUPPORTED_MAX_SPEED_MINIMUM <= max_speed <= SUPPORTED_MAX_SPEED_MAXIMUM):
        raise IncompatibleManifestError(
            "Persisted max_speed is outside WB1 support.", context=RECIPE_ID
        )
    geography_value = manifest.explicit_value(RESOURCE_GEOGRAPHY_SLOT)
    if (
        type(geography_value) is not str
        or geography_value not in SUPPORTED_RESOURCE_GEOGRAPHIES
    ):
        raise IncompatibleManifestError(
            "Persisted resource geography is not supported by this recipe version.",
            context=RECIPE_ID,
        )
    geography = cast(E3Environment, geography_value)
    seed = _require_exact_int(manifest.explicit_value(SEED_SLOT), SEED_SLOT)
    expected_derived = _derived_values(max_speed=max_speed, geography=geography)
    if manifest.derived_values != expected_derived:
        raise IncompatibleManifestError(
            "Persisted derived values do not match this recipe/compiler version.",
            context=RECIPE_ID,
        )

    treatment = build_e3_treatment(max_speed=max_speed, environment=geography)
    evidence = _resolve_runtime_evidence(plan)
    biological_spec = build_controlled_locomotion_spec(
        treatment.to_config(seed=seed),
        observers=evidence.observers,
        telemetry_observers=evidence.telemetry_observers,
    )
    return CompiledControlledLocomotion(
        compiled=biological_spec.compile(),
        evidence=evidence,
    )


def semantic_diff(
    before: ControlledLocomotionManifest,
    after: ControlledLocomotionManifest,
) -> ControlledLocomotionDiff:
    """Compare only stable recipe-owned scientific values."""
    if not isinstance(before, ControlledLocomotionManifest) or not isinstance(
        after, ControlledLocomotionManifest
    ):
        raise TypeError("before and after must be ControlledLocomotionManifest values.")
    if (before.recipe_id, before.recipe_version) != (
        after.recipe_id,
        after.recipe_version,
    ):
        raise ValueError("Semantic diff requires the same recipe identity and version.")
    return ControlledLocomotionDiff(
        explicit_changes=_changes(before.explicit_values, after.explicit_values),
        derived_changes=_changes(before.derived_values, after.derived_values),
    )


def _derived_values(*, max_speed: int, geography: E3Environment) -> ValuePairs:
    treatment = build_e3_treatment(max_speed=max_speed, environment=geography)
    return (
        ("controlled-locomotion.initial-focal-max-speed", max_speed),
        (
            "controlled-locomotion.resource-deposit-layout",
            _canonical_resource_layout(treatment.resource_deposits),
        ),
        ("controlled-locomotion.inherited-traits", MAX_SPEED),
        ("controlled-locomotion.genetics", "controlled-single-locus"),
        ("controlled-locomotion.inheritance", "clonal"),
        ("controlled-locomotion.mutation", "off"),
        ("controlled-locomotion.sensing", "perfect-full-world"),
        ("controlled-locomotion.movement-targeting", "nearest-resource"),
        ("controlled-locomotion.world-width", E3_WIDTH),
        ("controlled-locomotion.world-height", E3_HEIGHT),
        ("controlled-locomotion.horizon-step-index", E3_HORIZON),
        ("controlled-locomotion.initial-energy", E3_INITIAL_ENERGY),
        ("controlled-locomotion.body-mass", E3_BODY_MASS),
        (
            "controlled-locomotion.locomotion-cost-coefficient",
            E3_CANONICAL_LOCOMOTION_COST_COEFFICIENT,
        ),
        (
            "controlled-locomotion.locomotion-distance-exponent",
            E3_LOCOMOTION_DISTANCE_EXPONENT,
        ),
        ("controlled-locomotion.resource-request-amount", E3_RESOURCE_REQUEST_AMOUNT),
        (
            "controlled-locomotion.reproduction-minimum-energy",
            E3_REPRODUCTION_MINIMUM_ENERGY,
        ),
        (
            "controlled-locomotion.reproduction-energy-investment",
            E3_REPRODUCTION_ENERGY_INVESTMENT,
        ),
        ("controlled-locomotion.mate-search", False),
        ("controlled-locomotion.predation", False),
        ("controlled-locomotion.metabolism", False),
        ("controlled-locomotion.growth", False),
        ("controlled-locomotion.aging", False),
        ("controlled-locomotion.renewable-resource-generation", False),
    )


def _resolve_runtime_evidence(plan: EvidencePlan) -> RuntimeEvidence:
    population = (
        PopulationRecorder(
            trait_names=(MAX_SPEED,),
            every_n_steps=1,
            include_step_zero=True,
        )
        if POPULATION_EVIDENCE_ID in plan.requested
        else None
    )
    events = EventRecorder() if EVENT_EVIDENCE_ID in plan.requested else None
    return RuntimeEvidence(population_recorder=population, event_recorder=events)


def _missing(slot_id: str, message: str) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(
        code="missing-selection",
        slot_id=slot_id,
        context=RECIPE_ID,
        message=message,
        remediation="Provide this required semantic selection before resolving the Study.",
    )


def _changes(before: ValuePairs, after: ValuePairs) -> tuple[SemanticChange, ...]:
    before_mapping = dict(before)
    after_mapping = dict(after)
    if before_mapping.keys() != after_mapping.keys():
        raise ValueError("Semantic diff requires matching recipe-scoped value IDs.")
    return tuple(
        SemanticChange(
            slot_id=slot_id,
            before=before_mapping[slot_id],
            after=after_mapping[slot_id],
        )
        for slot_id in before_mapping
        if before_mapping[slot_id] != after_mapping[slot_id]
    )


def _installed_engine_version() -> str:
    try:
        return metadata.version(ENGINE_DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "source-tree-uninstalled"


def _require_current_compatibility(manifest: ControlledLocomotionManifest) -> None:
    current = _installed_engine_version()
    if manifest.engine_version != current:
        raise IncompatibleManifestError(
            "Persisted manifest requires "
            f"{manifest.engine_distribution}=={manifest.engine_version}; "
            f"current version is {current}.",
            context=RECIPE_ID,
        )


def _validate_manifest_identity(manifest: ControlledLocomotionManifest) -> None:
    expected = (
        RECIPE_ID,
        RECIPE_VERSION,
        COMPILER_ID,
        COMPILER_VERSION,
        ENGINE_DISTRIBUTION,
    )
    actual = (
        manifest.recipe_id,
        manifest.recipe_version,
        manifest.compiler_id,
        manifest.compiler_version,
        manifest.engine_distribution,
    )
    if actual != expected:
        raise IncompatibleManifestError(
            "Manifest recipe/compiler identity is not supported by WB1.",
            context=RECIPE_ID,
        )
    if type(manifest.engine_version) is not str or not manifest.engine_version:
        raise TypeError("engine_version must be a non-empty string.")


def _validate_value_pairs(values: ValuePairs, *, name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple.")
    seen: set[str] = set()
    for index, item in enumerate(values):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(f"{name}[{index}] must be a two-item tuple.")
        key, value = item
        if type(key) is not str or not key:
            raise TypeError(f"{name}[{index}][0] must be a non-empty string.")
        if key in seen:
            raise ValueError(f"{name} must not contain duplicate semantic IDs.")
        if type(value) not in (str, int, bool):
            raise TypeError(f"{name}[{index}][1] must be a manifest scalar.")
        seen.add(key)


def _value_for(values: ValuePairs, slot_id: str) -> ManifestScalar:
    for candidate, value in values:
        if candidate == slot_id:
            return value
    raise KeyError(slot_id)


def _required_str(mapping: dict[object, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _required_int(mapping: dict[object, object], key: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer.")
    return value


def _decode_pairs(mapping: dict[object, object], key: str) -> ValuePairs:
    raw = mapping.get(key)
    if type(raw) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    decoded: list[tuple[str, ManifestScalar]] = []
    for index, item in enumerate(raw):
        if type(item) is not list or len(item) != 2:
            raise TypeError(f"{key}[{index}] must be a two-item JSON array.")
        item_key, item_value = item
        if type(item_key) is not str:
            raise TypeError(f"{key}[{index}][0] must be a string.")
        if type(item_value) not in (str, int, bool):
            raise TypeError(f"{key}[{index}][1] must be a manifest scalar.")
        decoded.append((item_key, item_value))
    return tuple(decoded)


def _require_exact_int(value: ManifestScalar, name: str) -> int:
    if type(value) is not int:
        raise IncompatibleManifestError(
            f"{name} must remain an integer.", context=RECIPE_ID
        )
    return value


def _canonical_resource_layout(deposits: tuple[tuple[int, int, int], ...]) -> str:
    return json.dumps(
        [list(deposit) for deposit in deposits],
        separators=(",", ":"),
        allow_nan=False,
    )
