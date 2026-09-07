"""Bounded Workbench recipe for rich reference-ecology custom studies."""

from __future__ import annotations

import hashlib
import json
from importlib import metadata
from typing import Literal, cast

import attrs

from evo_engine.configuration import CompiledSimulation
from evo_engine.ecology import (
    PatchyResourcePlacement,
    ResourcePatch,
    UniformResourcePlacement,
)
from evo_engine.engine import Observer
from evo_engine.genetics import MAX_SPEED, SENSORY_ACCURACY, SENSORY_RANGE
from evo_engine.observation import (
    EventRecorder,
    GeneticCompositionRecorder,
    PedigreeRecorder,
    PopulationRecorder,
    SpatialRecorder,
)
from evo_engine.presets.reference_ecology import (
    ReferenceEcologyConfig,
    ReferenceGaussianMovement,
    ReferenceMooreMovement,
    ReferenceTraitValues,
    ReferenceUniformMovement,
    ReferenceVonNeumannMovement,
    build_reference_spec,
)
from evo_engine.telemetry import TelemetryObserver
from evo_engine.workbench.controlled_locomotion import (
    IncompatibleManifestError,
    SemanticChange,
    WorkbenchDiagnostic,
    WorkbenchNotReadyError,
    WorkbenchReadiness,
)

REFERENCE_RECIPE_ID = "bounded-reference-ecology"
REFERENCE_RECIPE_VERSION = 1
REFERENCE_COMPILER_ID = "workbench.bounded-reference-ecology"
REFERENCE_COMPILER_VERSION = 1
ENGINE_DISTRIBUTION = "evolution-simulation-engine"

SupportTier = Literal["guided", "advanced", "expert", "extension"]
ManifestScalar = str | int | bool
ValuePairs = tuple[tuple[str, ManifestScalar], ...]

WORLD_WIDTH_SLOT = "reference-ecology.world-width"
WORLD_HEIGHT_SLOT = "reference-ecology.world-height"
FOUNDER_POPULATION_SLOT = "reference-ecology.founder-population"
FOUNDER_ENERGY_SLOT = "reference-ecology.founder-energy"
HORIZON_SLOT = "reference-ecology.horizon"
SEED_SLOT = "reference-ecology.seed"
MAX_SPEED_SLOT = "reference-ecology.founder-max-speed"
SENSORY_RANGE_SLOT = "reference-ecology.founder-sensory-range"
SENSORY_ACCURACY_SLOT = "reference-ecology.founder-sensory-accuracy"
EXPLORATION_MOVEMENT_SLOT = "reference-ecology.exploration-movement"
GAUSSIAN_STDDEV_SLOT = "reference-ecology.gaussian-standard-deviation"
RESOURCE_GEOGRAPHY_SLOT = "reference-ecology.resource-geography"
RESOURCE_AMOUNT_SLOT = "reference-ecology.resource-generation-amount"
RESOURCE_DEPOSITS_SLOT = "reference-ecology.resource-deposits-per-step"
PATCH_1_X_SLOT = "reference-ecology.patch-1-center-x"
PATCH_1_Y_SLOT = "reference-ecology.patch-1-center-y"
PATCH_1_RADIUS_SLOT = "reference-ecology.patch-1-radius"
PATCH_2_X_SLOT = "reference-ecology.patch-2-center-x"
PATCH_2_Y_SLOT = "reference-ecology.patch-2-center-y"
PATCH_2_RADIUS_SLOT = "reference-ecology.patch-2-radius"
MUTATION_ENABLED_SLOT = "reference-ecology.mutation-enabled"
MUTATION_PROBABILITY_SLOT = "reference-ecology.mutation-probability-ppm"
MUTATION_MAX_CHANGE_SLOT = "reference-ecology.mutation-max-change"
RECOMBINATION_PROBABILITY_SLOT = "reference-ecology.recombination-probability-ppm"

POPULATION_EVIDENCE_ID = "reference-ecology.population-traits"
EVENT_EVIDENCE_ID = "reference-ecology.committed-events"
PEDIGREE_EVIDENCE_ID = "reference-ecology.pedigree"
GENETIC_EVIDENCE_ID = "reference-ecology.genetic-composition"
SPATIAL_EVIDENCE_ID = "reference-ecology.spatial-replay"
SUPPORTED_EVIDENCE_IDS = frozenset(
    {
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
        PEDIGREE_EVIDENCE_ID,
        GENETIC_EVIDENCE_ID,
        SPATIAL_EVIDENCE_ID,
    }
)

_DERIVED_RESOURCE_PLACEMENT = "reference-ecology.resolved-resource-placement"
_DERIVED_EXPLORATION_PATTERN = "reference-ecology.resolved-exploration-pattern"
_DERIVED_MUTATION_PROBABILITY = (
    "reference-ecology.effective-mutation-probability-ppm"
)
_DERIVED_MUTATION_MAX_CHANGE = "reference-ecology.effective-mutation-max-change"
_DERIVED_FIXED_CONFIG = "reference-ecology.fixed-reference-config"
_DERIVED_GENOME_STRUCTURE = "reference-ecology.genome-structure"
_DERIVED_GENETIC_EXPRESSION = "reference-ecology.genetic-expression"
_DERIVED_INHERITANCE = "reference-ecology.inheritance"
_DERIVED_DEVELOPMENT = "reference-ecology.development"
_DERIVED_REPRODUCTION = "reference-ecology.reproduction"
_DERIVED_FOOD_TARGETING = "reference-ecology.food-targeting"
_DERIVED_MATE_TARGETING = "reference-ecology.mate-targeting"
_DERIVED_IDS = (
    _DERIVED_RESOURCE_PLACEMENT,
    _DERIVED_EXPLORATION_PATTERN,
    _DERIVED_MUTATION_PROBABILITY,
    _DERIVED_MUTATION_MAX_CHANGE,
    _DERIVED_FIXED_CONFIG,
    _DERIVED_GENOME_STRUCTURE,
    _DERIVED_GENETIC_EXPRESSION,
    _DERIVED_INHERITANCE,
    _DERIVED_DEVELOPMENT,
    _DERIVED_REPRODUCTION,
    _DERIVED_FOOD_TARGETING,
    _DERIVED_MATE_TARGETING,
)


@attrs.frozen(slots=True, kw_only=True)
class ReferenceSlotMetadata:
    """Describe one stable recipe-local authoring slot."""

    slot_id: str
    label: str
    support_tier: SupportTier
    applicable_when: str | None = None


@attrs.frozen(slots=True, kw_only=True)
class EvidenceAdvisory:
    """Describe one non-blocking evidence-volume warning."""

    code: str
    evidence_id: str
    message: str


REFERENCE_SUPPORT_TIERS: tuple[tuple[SupportTier, str], ...] = (
    ("guided", "Stable choices suitable for ordinary scientific authoring."),
    ("advanced", "Supported choices requiring more scientific judgment."),
    ("expert", "Official choices with limited interpretation or guardrails."),
    ("extension", "Engine capability not officially authorable in this recipe."),
)

REFERENCE_SLOT_METADATA = (
    ReferenceSlotMetadata(
        slot_id=WORLD_WIDTH_SLOT,
        label="World width",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=WORLD_HEIGHT_SLOT,
        label="World height",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=FOUNDER_POPULATION_SLOT,
        label="Founder population",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=FOUNDER_ENERGY_SLOT,
        label="Founder starting energy",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=HORIZON_SLOT,
        label="Run horizon",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=SEED_SLOT,
        label="Random seed",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=MAX_SPEED_SLOT,
        label="Founder maximum speed",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=SENSORY_RANGE_SLOT,
        label="Founder sensory range",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=SENSORY_ACCURACY_SLOT,
        label="Founder sensory accuracy",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=EXPLORATION_MOVEMENT_SLOT,
        label="Exploration movement",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=GAUSSIAN_STDDEV_SLOT,
        label="Gaussian standard deviation",
        support_tier="advanced",
        applicable_when="exploration movement is gaussian",
    ),
    ReferenceSlotMetadata(
        slot_id=RESOURCE_GEOGRAPHY_SLOT,
        label="Resource geography",
        support_tier="guided",
    ),
    ReferenceSlotMetadata(
        slot_id=RESOURCE_AMOUNT_SLOT,
        label="Renewable resource amount",
        support_tier="advanced",
    ),
    ReferenceSlotMetadata(
        slot_id=RESOURCE_DEPOSITS_SLOT,
        label="Resource deposits per step",
        support_tier="advanced",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_1_X_SLOT,
        label="Patch 1 center x",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_1_Y_SLOT,
        label="Patch 1 center y",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_1_RADIUS_SLOT,
        label="Patch 1 radius",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_2_X_SLOT,
        label="Patch 2 center x",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_2_Y_SLOT,
        label="Patch 2 center y",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=PATCH_2_RADIUS_SLOT,
        label="Patch 2 radius",
        support_tier="advanced",
        applicable_when="resource geography is two_patches",
    ),
    ReferenceSlotMetadata(
        slot_id=MUTATION_ENABLED_SLOT,
        label="Mutation enabled",
        support_tier="advanced",
    ),
    ReferenceSlotMetadata(
        slot_id=MUTATION_PROBABILITY_SLOT,
        label="Mutation probability (ppm)",
        support_tier="advanced",
        applicable_when="mutation is enabled",
    ),
    ReferenceSlotMetadata(
        slot_id=MUTATION_MAX_CHANGE_SLOT,
        label="Mutation maximum change",
        support_tier="advanced",
        applicable_when="mutation is enabled",
    ),
    ReferenceSlotMetadata(
        slot_id=RECOMBINATION_PROBABILITY_SLOT,
        label="Recombination probability (ppm)",
        support_tier="advanced",
    ),
)

REFERENCE_EXPERT_SLOT_IDS: tuple[str, ...] = ()
REFERENCE_EXTENSION_CAPABILITIES = (
    "arbitrary-resource-placement-policy",
    "arbitrary-patch-counts-and-weights",
    "arbitrary-reference-traits",
    "physiological-tradeoff-editing",
    "arbitrary-loci-chromosomes-ploidy",
    "genetic-expression-policy-editing",
    "inheritance-policy-switching",
    "reproduction-system-composition",
    "targeted-movement-policy-composition",
    "lifecycle-process-composition",
    "development-policy-editing",
)

_PATCH_SLOT_IDS = frozenset(
    {
        PATCH_1_X_SLOT,
        PATCH_1_Y_SLOT,
        PATCH_1_RADIUS_SLOT,
        PATCH_2_X_SLOT,
        PATCH_2_Y_SLOT,
        PATCH_2_RADIUS_SLOT,
    }
)
_MUTATION_PARAMETER_SLOT_IDS = frozenset(
    {MUTATION_PROBABILITY_SLOT, MUTATION_MAX_CHANGE_SLOT}
)


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcologyIntent:
    """Persist editable semantic choices for the bounded reference recipe."""

    width: int | None = None
    height: int | None = None
    founder_population: int | None = None
    founder_energy: int | None = None
    horizon: int | None = None
    seed: int | None = None
    max_speed: int | None = None
    sensory_range: int | None = None
    sensory_accuracy: int | None = None
    exploration_movement: str | None = None
    gaussian_standard_deviation: int | None = None
    resource_geography: str | None = None
    resource_generation_amount: int | None = None
    resource_deposits_per_step: int | None = None
    patch_1_center_x: int | None = None
    patch_1_center_y: int | None = None
    patch_1_radius: int | None = None
    patch_2_center_x: int | None = None
    patch_2_center_y: int | None = None
    patch_2_radius: int | None = None
    mutation_enabled: bool | None = None
    mutation_probability_ppm: int | None = None
    mutation_max_change: int | None = None
    recombination_probability_ppm: int | None = None


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEvidencePlan:
    """Persist requested concrete evidence for the bounded reference recipe."""

    requested: tuple[str, ...] = (
        POPULATION_EVIDENCE_ID,
        EVENT_EVIDENCE_ID,
    )

    def __attrs_post_init__(self) -> None:
        if type(self.requested) is not tuple:
            raise TypeError("requested must be a tuple.")
        if len(self.requested) != len(set(self.requested)):
            raise ValueError("requested must not contain duplicate evidence IDs.")
        for index, evidence_id in enumerate(self.requested):
            if type(evidence_id) is not str or not evidence_id.strip():
                raise TypeError(
                    f"requested[{index}] must be a non-empty evidence ID."
                )


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcologyManifest:
    """Store exact normalized scientific meaning for one reference recipe revision."""

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
        _validate_explicit_shape(self.explicit_values)
        if tuple(key for key, _ in self.derived_values) != _DERIVED_IDS:
            raise ValueError("derived_values must use the reference recipe schema.")

    @property
    def digest(self) -> str:
        """Return a stable digest of canonical manifest content."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def explicit_value(self, slot_id: str) -> ManifestScalar:
        """Return an explicit value by stable semantic slot ID."""
        return _value_for(self.explicit_values, slot_id)

    def explicit_value_or_none(self, slot_id: str) -> ManifestScalar | None:
        """Return an explicit value when the slot is active in this manifest."""
        for key, value in self.explicit_values:
            if key == slot_id:
                return value
        return None

    def derived_value(self, slot_id: str) -> ManifestScalar:
        """Return a derived value by stable semantic slot ID."""
        return _value_for(self.derived_values, slot_id)

    def to_json(self) -> str:
        """Serialize the manifest canonically."""
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
    def from_json(cls, value: str) -> ReferenceEcologyManifest:
        """Deserialize a stored manifest without re-resolving authoring intent."""
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


@attrs.define(slots=True, kw_only=True)
class ReferenceRuntimeEvidence:
    """Hold fresh concrete recorders reconstructed from evidence intent."""

    population_recorder: PopulationRecorder | None = None
    event_recorder: EventRecorder | None = None
    pedigree_recorder: PedigreeRecorder | None = None
    genetic_recorder: GeneticCompositionRecorder | None = None
    spatial_recorder: SpatialRecorder | None = None

    @property
    def observers(self) -> tuple[Observer, ...]:
        """Return state observers in deterministic recipe order."""
        result: list[Observer] = []
        for recorder in (
            self.population_recorder,
            self.pedigree_recorder,
            self.genetic_recorder,
            self.spatial_recorder,
        ):
            if recorder is not None:
                result.append(recorder)
        return tuple(result)

    @property
    def telemetry_observers(self) -> tuple[TelemetryObserver, ...]:
        """Return telemetry observers in deterministic recipe order."""
        result: list[TelemetryObserver] = []
        for recorder in (self.event_recorder, self.pedigree_recorder):
            if recorder is not None:
                result.append(recorder)
        return tuple(result)


@attrs.frozen(slots=True, kw_only=True)
class CompiledReferenceEcology:
    """Bundle authoritative compilation with the recorders used for preflight."""

    compiled: CompiledSimulation
    evidence: ReferenceRuntimeEvidence


@attrs.frozen(slots=True, kw_only=True)
class ReferenceEcologyDiff:
    """Separate authored changes from recipe-owned derived consequences."""

    explicit_changes: tuple[SemanticChange, ...]
    derived_changes: tuple[SemanticChange, ...]


def default_reference_ecology_intent() -> ReferenceEcologyIntent:
    """Return a complete authoring intent using the pinned reference defaults."""
    config = ReferenceEcologyConfig()
    return ReferenceEcologyIntent(
        width=config.width,
        height=config.height,
        founder_population=config.initial_population,
        founder_energy=config.initial_energy,
        horizon=config.max_steps,
        seed=config.seed,
        max_speed=config.traits.max_speed,
        sensory_range=config.traits.sensory_range,
        sensory_accuracy=config.traits.sensory_accuracy,
        exploration_movement="moore",
        resource_geography="uniform",
        resource_generation_amount=config.resource_generation_amount,
        resource_deposits_per_step=config.resource_deposits_per_step,
        mutation_enabled=config.mutation_probability_ppm > 0,
        mutation_probability_ppm=config.mutation_probability_ppm,
        mutation_max_change=config.mutation_max_change,
        recombination_probability_ppm=config.recombination_probability_ppm,
    )


def slot_metadata(slot_id: str) -> ReferenceSlotMetadata:
    """Return metadata for one officially supported semantic slot."""
    for item in REFERENCE_SLOT_METADATA:
        if item.slot_id == slot_id:
            return item
    raise KeyError(f"Unsupported reference-ecology slot {slot_id!r}.")


def is_slot_applicable(intent: ReferenceEcologyIntent, slot_id: str) -> bool:
    """Return recipe-local applicability for one officially supported slot."""
    slot_metadata(slot_id)
    if slot_id == GAUSSIAN_STDDEV_SLOT:
        return intent.exploration_movement == "gaussian"
    if slot_id in _PATCH_SLOT_IDS:
        return intent.resource_geography == "two_patches"
    if slot_id in _MUTATION_PARAMETER_SLOT_IDS:
        return intent.mutation_enabled is True
    return True


def evidence_advisories(plan: ReferenceEvidencePlan) -> tuple[EvidenceAdvisory, ...]:
    """Return non-blocking storage/computation guidance for requested evidence."""
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("plan must be a ReferenceEvidencePlan.")
    if SPATIAL_EVIDENCE_ID not in plan.requested:
        return ()
    return (
        EvidenceAdvisory(
            code="high-volume-spatial-evidence",
            evidence_id=SPATIAL_EVIDENCE_ID,
            message=(
                "Spatial replay stores full committed world frames; storage grows "
                "with horizon and population size."
            ),
        ),
    )


def assess_reference_readiness(
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> WorkbenchReadiness:
    """Check completeness and official support before authoritative preflight."""
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("evidence_plan must be a ReferenceEvidencePlan or None.")

    missing: list[WorkbenchDiagnostic] = []
    blocked: list[WorkbenchDiagnostic] = []
    _check_guided_core(intent, missing=missing, blocked=blocked)
    _check_movement(intent, missing=missing, blocked=blocked)
    _check_resources(intent, missing=missing, blocked=blocked)
    _check_genetic_processes(intent, missing=missing, blocked=blocked)
    _check_evidence(plan, missing=missing, blocked=blocked)
    if blocked:
        return WorkbenchReadiness(state="blocked", diagnostics=tuple(blocked + missing))
    if missing:
        return WorkbenchReadiness(state="draft", diagnostics=tuple(missing))
    return WorkbenchReadiness(state="ready")


def resolve_reference_ecology(
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> ReferenceEcologyManifest:
    """Normalize authoring state into an immutable recipe-owned manifest."""
    readiness = assess_reference_readiness(intent, evidence_plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    explicit = normalized_reference_explicit_values(intent)
    return ReferenceEcologyManifest(
        recipe_id=REFERENCE_RECIPE_ID,
        recipe_version=REFERENCE_RECIPE_VERSION,
        compiler_id=REFERENCE_COMPILER_ID,
        compiler_version=REFERENCE_COMPILER_VERSION,
        engine_distribution=ENGINE_DISTRIBUTION,
        engine_version=_installed_engine_version(),
        explicit_values=explicit,
        derived_values=_derived_values(explicit),
    )


def normalized_reference_explicit_values(intent: ReferenceEcologyIntent) -> ValuePairs:
    """Return normalized active authoring values in canonical semantic-slot order."""
    values: list[tuple[str, ManifestScalar]] = [
        (WORLD_WIDTH_SLOT, cast(int, intent.width)),
        (WORLD_HEIGHT_SLOT, cast(int, intent.height)),
        (FOUNDER_POPULATION_SLOT, cast(int, intent.founder_population)),
        (FOUNDER_ENERGY_SLOT, cast(int, intent.founder_energy)),
        (HORIZON_SLOT, cast(int, intent.horizon)),
        (SEED_SLOT, cast(int, intent.seed)),
        (MAX_SPEED_SLOT, cast(int, intent.max_speed)),
        (SENSORY_RANGE_SLOT, cast(int, intent.sensory_range)),
        (SENSORY_ACCURACY_SLOT, cast(int, intent.sensory_accuracy)),
        (EXPLORATION_MOVEMENT_SLOT, cast(str, intent.exploration_movement)),
    ]
    if intent.exploration_movement == "gaussian":
        values.append(
            (GAUSSIAN_STDDEV_SLOT, cast(int, intent.gaussian_standard_deviation))
        )
    values.extend(
        (
            (RESOURCE_GEOGRAPHY_SLOT, cast(str, intent.resource_geography)),
            (RESOURCE_AMOUNT_SLOT, cast(int, intent.resource_generation_amount)),
            (
                RESOURCE_DEPOSITS_SLOT,
                cast(int, intent.resource_deposits_per_step),
            ),
        )
    )
    if intent.resource_geography == "two_patches":
        values.extend(_normalized_patch_values(intent))
    values.append((MUTATION_ENABLED_SLOT, cast(bool, intent.mutation_enabled)))
    if intent.mutation_enabled is True:
        values.extend(
            (
                (
                    MUTATION_PROBABILITY_SLOT,
                    cast(int, intent.mutation_probability_ppm),
                ),
                (MUTATION_MAX_CHANGE_SLOT, cast(int, intent.mutation_max_change)),
            )
        )
    values.append(
        (
            RECOMBINATION_PROBABILITY_SLOT,
            cast(int, intent.recombination_probability_ppm),
        )
    )
    return tuple(values)


def compile_reference_ecology(
    manifest: ReferenceEcologyManifest,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> CompiledReferenceEcology:
    """Reconstruct current typed reference composition and run lower preflight."""
    if not isinstance(manifest, ReferenceEcologyManifest):
        raise TypeError("manifest must be a ReferenceEcologyManifest.")
    _require_current_compatibility(manifest)
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    _validate_evidence_plan_for_compile(plan)
    expected_derived = _derived_values(manifest.explicit_values)
    if manifest.derived_values != expected_derived:
        raise IncompatibleManifestError(
            "Persisted derived values do not match this reference recipe/compiler "
            "version."
        )
    config = _config_from_manifest(manifest)
    evidence = _runtime_evidence(plan)
    biological_spec = build_reference_spec(
        config,
        observers=evidence.observers,
        telemetry_observers=evidence.telemetry_observers,
    )
    return CompiledReferenceEcology(
        compiled=biological_spec.compile(),
        evidence=evidence,
    )


def semantic_reference_diff(
    before: ReferenceEcologyManifest,
    after: ReferenceEcologyManifest,
) -> ReferenceEcologyDiff:
    """Compare only stable recipe-owned scientific values."""
    if not isinstance(before, ReferenceEcologyManifest) or not isinstance(
        after, ReferenceEcologyManifest
    ):
        raise TypeError("before and after must be ReferenceEcologyManifest values.")
    if (before.recipe_id, before.recipe_version) != (
        after.recipe_id,
        after.recipe_version,
    ):
        raise ValueError("Semantic diff requires the same recipe identity and version.")
    return ReferenceEcologyDiff(
        explicit_changes=_changes(before.explicit_values, after.explicit_values),
        derived_changes=_changes(before.derived_values, after.derived_values),
    )


def _check_guided_core(
    intent: ReferenceEcologyIntent,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    checks = (
        (intent.width, WORLD_WIDTH_SLOT, 4, 50),
        (intent.height, WORLD_HEIGHT_SLOT, 4, 50),
        (intent.founder_population, FOUNDER_POPULATION_SLOT, 2, 100),
        (intent.founder_energy, FOUNDER_ENERGY_SLOT, 1, 200),
        (intent.horizon, HORIZON_SLOT, 1, 500),
        (intent.max_speed, MAX_SPEED_SLOT, 0, 4),
        (intent.sensory_range, SENSORY_RANGE_SLOT, 0, 20),
        (intent.sensory_accuracy, SENSORY_ACCURACY_SLOT, 0, 100),
    )
    for value, slot_id, minimum, maximum in checks:
        _required_int_range(
            value,
            slot_id,
            minimum,
            maximum,
            missing=missing,
            blocked=blocked,
        )
    if intent.seed is None:
        missing.append(_missing(SEED_SLOT, "Select a reproducibility seed."))
    elif type(intent.seed) is not int:
        blocked.append(_unsupported(SEED_SLOT, "Seed must be an integer."))


def _check_movement(
    intent: ReferenceEcologyIntent,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    movement = intent.exploration_movement
    supported = {"moore", "von_neumann", "uniform", "gaussian"}
    if movement is None:
        missing.append(_missing(EXPLORATION_MOVEMENT_SLOT, "Select movement."))
        return
    if movement not in supported:
        blocked.append(
            _unsupported(
                EXPLORATION_MOVEMENT_SLOT,
                "Supported movement is moore, von_neumann, uniform, or gaussian.",
            )
        )
        return
    if movement == "gaussian":
        _required_int_range(
            intent.gaussian_standard_deviation,
            GAUSSIAN_STDDEV_SLOT,
            0,
            10,
            missing=missing,
            blocked=blocked,
        )


def _check_resources(
    intent: ReferenceEcologyIntent,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    geography = intent.resource_geography
    if geography is None:
        missing.append(_missing(RESOURCE_GEOGRAPHY_SLOT, "Select resource geography."))
    elif geography not in {"uniform", "two_patches"}:
        blocked.append(
            _unsupported(
                RESOURCE_GEOGRAPHY_SLOT,
                "Supported geography is uniform or two_patches.",
            )
        )
    _required_int_range(
        intent.resource_generation_amount,
        RESOURCE_AMOUNT_SLOT,
        1,
        100,
        missing=missing,
        blocked=blocked,
    )
    _required_int_range(
        intent.resource_deposits_per_step,
        RESOURCE_DEPOSITS_SLOT,
        1,
        50,
        missing=missing,
        blocked=blocked,
    )
    if geography == "two_patches":
        _check_patch_geometry(intent, missing=missing, blocked=blocked)


def _check_patch_geometry(
    intent: ReferenceEcologyIntent,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    checks = (
        (intent.patch_1_center_x, PATCH_1_X_SLOT),
        (intent.patch_1_center_y, PATCH_1_Y_SLOT),
        (intent.patch_2_center_x, PATCH_2_X_SLOT),
        (intent.patch_2_center_y, PATCH_2_Y_SLOT),
    )
    for value, slot_id in checks:
        _required_int_range(
            value,
            slot_id,
            0,
            49,
            missing=missing,
            blocked=blocked,
        )
    for value, slot_id in (
        (intent.patch_1_radius, PATCH_1_RADIUS_SLOT),
        (intent.patch_2_radius, PATCH_2_RADIUS_SLOT),
    ):
        _required_int_range(
            value,
            slot_id,
            0,
            20,
            missing=missing,
            blocked=blocked,
        )
    _check_patch_world_bounds(intent, blocked=blocked)


def _check_patch_world_bounds(
    intent: ReferenceEcologyIntent,
    *,
    blocked: list[WorkbenchDiagnostic],
) -> None:
    if type(intent.width) is int:
        for value, slot_id in (
            (intent.patch_1_center_x, PATCH_1_X_SLOT),
            (intent.patch_2_center_x, PATCH_2_X_SLOT),
        ):
            if type(value) is int and value >= intent.width:
                blocked.append(
                    _unsupported(slot_id, "Patch center must lie inside the world.")
                )
    if type(intent.height) is int:
        for value, slot_id in (
            (intent.patch_1_center_y, PATCH_1_Y_SLOT),
            (intent.patch_2_center_y, PATCH_2_Y_SLOT),
        ):
            if type(value) is int and value >= intent.height:
                blocked.append(
                    _unsupported(slot_id, "Patch center must lie inside the world.")
                )


def _check_genetic_processes(
    intent: ReferenceEcologyIntent,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    if intent.mutation_enabled is None:
        missing.append(_missing(MUTATION_ENABLED_SLOT, "Choose mutation state."))
    elif type(intent.mutation_enabled) is not bool:
        blocked.append(
            _unsupported(MUTATION_ENABLED_SLOT, "Mutation state must be boolean.")
        )
    elif intent.mutation_enabled:
        _required_int_range(
            intent.mutation_probability_ppm,
            MUTATION_PROBABILITY_SLOT,
            0,
            100_000,
            missing=missing,
            blocked=blocked,
        )
        _required_int_range(
            intent.mutation_max_change,
            MUTATION_MAX_CHANGE_SLOT,
            1,
            4,
            missing=missing,
            blocked=blocked,
        )
    _required_int_range(
        intent.recombination_probability_ppm,
        RECOMBINATION_PROBABILITY_SLOT,
        0,
        1_000_000,
        missing=missing,
        blocked=blocked,
    )


def _check_evidence(
    plan: ReferenceEvidencePlan,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    if not plan.requested:
        missing.append(
            WorkbenchDiagnostic(
                code="missing-evidence",
                message="Select at least one supported evidence stream.",
            )
        )
    for evidence_id in plan.requested:
        if evidence_id not in SUPPORTED_EVIDENCE_IDS:
            blocked.append(
                WorkbenchDiagnostic(
                    code="unsupported-evidence",
                    message=f"Unsupported reference evidence {evidence_id!r}.",
                )
            )


def _required_int_range(
    value: int | None,
    slot_id: str,
    minimum: int,
    maximum: int,
    *,
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
) -> None:
    if value is None:
        missing.append(_missing(slot_id, f"Select {slot_id}."))
        return
    if type(value) is not int or not minimum <= value <= maximum:
        blocked.append(
            _unsupported(
                slot_id,
                f"Workbench support is {minimum} through {maximum}.",
            )
        )


def _normalized_patch_values(intent: ReferenceEcologyIntent) -> ValuePairs:
    return (
        (PATCH_1_X_SLOT, cast(int, intent.patch_1_center_x)),
        (PATCH_1_Y_SLOT, cast(int, intent.patch_1_center_y)),
        (PATCH_1_RADIUS_SLOT, cast(int, intent.patch_1_radius)),
        (PATCH_2_X_SLOT, cast(int, intent.patch_2_center_x)),
        (PATCH_2_Y_SLOT, cast(int, intent.patch_2_center_y)),
        (PATCH_2_RADIUS_SLOT, cast(int, intent.patch_2_radius)),
    )


def _derived_values(explicit: ValuePairs) -> ValuePairs:
    movement = cast(str, _value_for(explicit, EXPLORATION_MOVEMENT_SLOT))
    geography = cast(str, _value_for(explicit, RESOURCE_GEOGRAPHY_SLOT))
    mutation_enabled = cast(bool, _value_for(explicit, MUTATION_ENABLED_SLOT))
    mutation_probability = 0
    mutation_change = 0
    if mutation_enabled:
        mutation_probability = cast(
            int,
            _value_for(explicit, MUTATION_PROBABILITY_SLOT),
        )
        mutation_change = cast(int, _value_for(explicit, MUTATION_MAX_CHANGE_SLOT))
    return (
        (_DERIVED_RESOURCE_PLACEMENT, _resource_placement_description(explicit)),
        (_DERIVED_EXPLORATION_PATTERN, movement),
        (_DERIVED_MUTATION_PROBABILITY, mutation_probability),
        (_DERIVED_MUTATION_MAX_CHANGE, mutation_change),
        (_DERIVED_FIXED_CONFIG, _fixed_reference_config_json()),
        (_DERIVED_GENOME_STRUCTURE, "diploid-single-reference-chromosome"),
        (_DERIVED_GENETIC_EXPRESSION, "one-integer-locus-mean-expression-per-trait"),
        (_DERIVED_INHERITANCE, "sexual-meiotic-single-crossover"),
        (_DERIVED_DEVELOPMENT, "reference-developmental-profile"),
        (_DERIVED_REPRODUCTION, "reference-pairwise-sexual"),
        (_DERIVED_FOOD_TARGETING, "nearest-detectable-resource"),
        (_DERIVED_MATE_TARGETING, "preferred-compatible-mate"),
    )


def _resource_placement_description(explicit: ValuePairs) -> str:
    geography = cast(str, _value_for(explicit, RESOURCE_GEOGRAPHY_SLOT))
    if geography == "uniform":
        return "uniform"
    return json.dumps(
        {
            "patches": [
                _patch_mapping(explicit, prefix=1),
                _patch_mapping(explicit, prefix=2),
            ]
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _patch_mapping(explicit: ValuePairs, *, prefix: int) -> dict[str, int]:
    if prefix == 1:
        x_slot, y_slot, radius_slot = PATCH_1_X_SLOT, PATCH_1_Y_SLOT, PATCH_1_RADIUS_SLOT
    else:
        x_slot, y_slot, radius_slot = PATCH_2_X_SLOT, PATCH_2_Y_SLOT, PATCH_2_RADIUS_SLOT
    return {
        "center_x": cast(int, _value_for(explicit, x_slot)),
        "center_y": cast(int, _value_for(explicit, y_slot)),
        "radius": cast(int, _value_for(explicit, radius_slot)),
        "weight": 1,
    }


def _fixed_reference_config_json() -> str:
    config = ReferenceEcologyConfig()
    fixed_traits = {
        key: value
        for key, value in config.traits.as_mapping().items()
        if key not in {MAX_SPEED, SENSORY_RANGE, SENSORY_ACCURACY}
    }
    fixed = {
        "decomposition_amount": config.decomposition_amount,
        "growth_energy_per_mass": config.growth_energy_per_mass,
        "locomotion_distance_exponent": config.locomotion_distance_exponent,
        "locomotion_mass_exponent": config.locomotion_mass_exponent,
        "mating_radius": config.mating_radius,
        "mating_type_investment_scales": attrs.asdict(
            config.mating_type_investment_scales
        ),
        "metabolic_mass_exponent": config.metabolic_mass_exponent,
        "newborn_mass_denominator": config.newborn_mass_denominator,
        "newborn_mass_numerator": config.newborn_mass_numerator,
        "physiological_tradeoffs": attrs.asdict(config.physiological_tradeoffs),
        "predation_consumption_percent": config.predation_consumption_percent,
        "predation_radius": config.predation_radius,
        "resource_request_amount": config.resource_request_amount,
        "traits": fixed_traits,
    }
    return json.dumps(
        fixed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _config_from_manifest(manifest: ReferenceEcologyManifest) -> ReferenceEcologyConfig:
    explicit = manifest.explicit_values
    traits = attrs.evolve(
        ReferenceTraitValues(),
        max_speed=cast(int, _value_for(explicit, MAX_SPEED_SLOT)),
        sensory_range=cast(int, _value_for(explicit, SENSORY_RANGE_SLOT)),
        sensory_accuracy=cast(int, _value_for(explicit, SENSORY_ACCURACY_SLOT)),
    )
    movement = _movement_from_manifest(explicit)
    placement = _placement_from_manifest(explicit)
    return attrs.evolve(
        ReferenceEcologyConfig(),
        width=cast(int, _value_for(explicit, WORLD_WIDTH_SLOT)),
        height=cast(int, _value_for(explicit, WORLD_HEIGHT_SLOT)),
        initial_population=cast(int, _value_for(explicit, FOUNDER_POPULATION_SLOT)),
        initial_energy=cast(int, _value_for(explicit, FOUNDER_ENERGY_SLOT)),
        max_steps=cast(int, _value_for(explicit, HORIZON_SLOT)),
        seed=cast(int, _value_for(explicit, SEED_SLOT)),
        exploration_movement=movement,
        traits=traits,
        mutation_probability_ppm=cast(
            int,
            manifest.derived_value(_DERIVED_MUTATION_PROBABILITY),
        ),
        mutation_max_change=cast(
            int,
            manifest.derived_value(_DERIVED_MUTATION_MAX_CHANGE),
        ),
        recombination_probability_ppm=cast(
            int,
            _value_for(explicit, RECOMBINATION_PROBABILITY_SLOT),
        ),
        resource_generation_amount=cast(
            int,
            _value_for(explicit, RESOURCE_AMOUNT_SLOT),
        ),
        resource_deposits_per_step=cast(
            int,
            _value_for(explicit, RESOURCE_DEPOSITS_SLOT),
        ),
        resource_placement_model=placement,
    )


def _movement_from_manifest(explicit: ValuePairs) -> object:
    movement = cast(str, _value_for(explicit, EXPLORATION_MOVEMENT_SLOT))
    if movement == "moore":
        return ReferenceMooreMovement()
    if movement == "von_neumann":
        return ReferenceVonNeumannMovement()
    if movement == "uniform":
        return ReferenceUniformMovement()
    if movement == "gaussian":
        return ReferenceGaussianMovement(
            standard_deviation=cast(
                int,
                _value_for(explicit, GAUSSIAN_STDDEV_SLOT),
            )
        )
    raise IncompatibleManifestError("Unsupported persisted exploration movement.")


def _placement_from_manifest(explicit: ValuePairs) -> object:
    geography = cast(str, _value_for(explicit, RESOURCE_GEOGRAPHY_SLOT))
    if geography == "uniform":
        return UniformResourcePlacement()
    if geography == "two_patches":
        return PatchyResourcePlacement(
            patches=(
                _resource_patch(explicit, prefix=1),
                _resource_patch(explicit, prefix=2),
            )
        )
    raise IncompatibleManifestError("Unsupported persisted resource geography.")


def _resource_patch(explicit: ValuePairs, *, prefix: int) -> ResourcePatch:
    mapping = _patch_mapping(explicit, prefix=prefix)
    return ResourcePatch(
        center_x=mapping["center_x"],
        center_y=mapping["center_y"],
        radius=mapping["radius"],
    )


def _runtime_evidence(plan: ReferenceEvidencePlan) -> ReferenceRuntimeEvidence:
    requested = set(plan.requested)
    return ReferenceRuntimeEvidence(
        population_recorder=(
            PopulationRecorder(
                trait_names=(MAX_SPEED, SENSORY_RANGE, SENSORY_ACCURACY)
            )
            if POPULATION_EVIDENCE_ID in requested
            else None
        ),
        event_recorder=EventRecorder() if EVENT_EVIDENCE_ID in requested else None,
        pedigree_recorder=(
            PedigreeRecorder() if PEDIGREE_EVIDENCE_ID in requested else None
        ),
        genetic_recorder=(
            GeneticCompositionRecorder(
                locus_names=(MAX_SPEED, SENSORY_RANGE, SENSORY_ACCURACY)
            )
            if GENETIC_EVIDENCE_ID in requested
            else None
        ),
        spatial_recorder=(
            SpatialRecorder() if SPATIAL_EVIDENCE_ID in requested else None
        ),
    )


def _validate_evidence_plan_for_compile(plan: ReferenceEvidencePlan) -> None:
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("evidence_plan must be a ReferenceEvidencePlan or None.")
    if not plan.requested:
        raise ValueError("Reference recipe requires at least one evidence stream.")
    unsupported = set(plan.requested) - SUPPORTED_EVIDENCE_IDS
    if unsupported:
        raise ValueError(f"Unsupported reference evidence IDs: {sorted(unsupported)!r}.")


def _validate_manifest_identity(manifest: ReferenceEcologyManifest) -> None:
    expected = (
        REFERENCE_RECIPE_ID,
        REFERENCE_RECIPE_VERSION,
        REFERENCE_COMPILER_ID,
        REFERENCE_COMPILER_VERSION,
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
        raise ValueError("Unsupported reference recipe/compiler identity.")
    if type(manifest.engine_version) is not str or not manifest.engine_version.strip():
        raise ValueError("engine_version must be a non-empty string.")


def _validate_explicit_shape(values: ValuePairs) -> None:
    value_map = dict(values)
    movement = value_map.get(EXPLORATION_MOVEMENT_SLOT)
    geography = value_map.get(RESOURCE_GEOGRAPHY_SLOT)
    mutation_enabled = value_map.get(MUTATION_ENABLED_SLOT)
    expected = [
        WORLD_WIDTH_SLOT,
        WORLD_HEIGHT_SLOT,
        FOUNDER_POPULATION_SLOT,
        FOUNDER_ENERGY_SLOT,
        HORIZON_SLOT,
        SEED_SLOT,
        MAX_SPEED_SLOT,
        SENSORY_RANGE_SLOT,
        SENSORY_ACCURACY_SLOT,
        EXPLORATION_MOVEMENT_SLOT,
    ]
    if movement == "gaussian":
        expected.append(GAUSSIAN_STDDEV_SLOT)
    expected.extend(
        [RESOURCE_GEOGRAPHY_SLOT, RESOURCE_AMOUNT_SLOT, RESOURCE_DEPOSITS_SLOT]
    )
    if geography == "two_patches":
        expected.extend(
            [
                PATCH_1_X_SLOT,
                PATCH_1_Y_SLOT,
                PATCH_1_RADIUS_SLOT,
                PATCH_2_X_SLOT,
                PATCH_2_Y_SLOT,
                PATCH_2_RADIUS_SLOT,
            ]
        )
    expected.append(MUTATION_ENABLED_SLOT)
    if mutation_enabled is True:
        expected.extend([MUTATION_PROBABILITY_SLOT, MUTATION_MAX_CHANGE_SLOT])
    expected.append(RECOMBINATION_PROBABILITY_SLOT)
    if tuple(key for key, _ in values) != tuple(expected):
        raise ValueError("explicit_values must use the normalized reference schema.")


def _validate_value_pairs(values: ValuePairs, *, name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple.")
    keys: list[str] = []
    for index, item in enumerate(values):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(f"{name}[{index}] must be a two-item tuple.")
        key, value = item
        if type(key) is not str or not key:
            raise TypeError(f"{name}[{index}] key must be a non-empty string.")
        if type(value) not in {str, int, bool}:
            raise TypeError(f"{name}[{index}] value must be a supported scalar.")
        keys.append(key)
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} must not contain duplicate semantic IDs.")


def _require_current_compatibility(manifest: ReferenceEcologyManifest) -> None:
    if manifest.engine_version != _installed_engine_version():
        raise IncompatibleManifestError(
            "Persisted reference manifest targets a different engine version."
        )


def _installed_engine_version() -> str:
    try:
        return metadata.version(ENGINE_DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "0+unknown"


def _changes(before: ValuePairs, after: ValuePairs) -> tuple[SemanticChange, ...]:
    before_values = dict(before)
    after_values = dict(after)
    slot_order = tuple(dict.fromkeys((*before_values, *after_values)))
    changes: list[SemanticChange] = []
    for slot_id in slot_order:
        before_value = before_values.get(slot_id, "<inactive>")
        after_value = after_values.get(slot_id, "<inactive>")
        if before_value != after_value:
            changes.append(
                SemanticChange(
                    slot_id=slot_id,
                    before=before_value,
                    after=after_value,
                )
            )
    return tuple(changes)


def _missing(slot_id: str, message: str) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(
        code="missing-selection",
        slot_id=slot_id,
        message=message,
    )


def _unsupported(slot_id: str, message: str) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(
        code="unsupported-value",
        slot_id=slot_id,
        message=message,
    )


def _value_for(values: ValuePairs, slot_id: str) -> ManifestScalar:
    for key, value in values:
        if key == slot_id:
            return value
    raise KeyError(slot_id)


def _decode_pairs(mapping: dict[object, object], key: str) -> ValuePairs:
    raw = mapping.get(key)
    if type(raw) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    result: list[tuple[str, ManifestScalar]] = []
    for item in raw:
        if type(item) is not list or len(item) != 2:
            raise TypeError(f"{key} entries must be two-item arrays.")
        item_key, item_value = item
        if type(item_key) is not str or type(item_value) not in {str, int, bool}:
            raise TypeError(f"{key} entries must contain a string ID and scalar value.")
        result.append((item_key, cast(ManifestScalar, item_value)))
    return tuple(result)


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


__all__ = [
    "EVENT_EVIDENCE_ID",
    "EXPLORATION_MOVEMENT_SLOT",
    "EvidenceAdvisory",
    "FOUNDER_ENERGY_SLOT",
    "FOUNDER_POPULATION_SLOT",
    "GAUSSIAN_STDDEV_SLOT",
    "GENETIC_EVIDENCE_ID",
    "HORIZON_SLOT",
    "MAX_SPEED_SLOT",
    "MUTATION_ENABLED_SLOT",
    "MUTATION_MAX_CHANGE_SLOT",
    "MUTATION_PROBABILITY_SLOT",
    "PATCH_1_RADIUS_SLOT",
    "PATCH_1_X_SLOT",
    "PATCH_1_Y_SLOT",
    "PATCH_2_RADIUS_SLOT",
    "PATCH_2_X_SLOT",
    "PATCH_2_Y_SLOT",
    "PEDIGREE_EVIDENCE_ID",
    "POPULATION_EVIDENCE_ID",
    "RECOMBINATION_PROBABILITY_SLOT",
    "REFERENCE_EXPERT_SLOT_IDS",
    "REFERENCE_EXTENSION_CAPABILITIES",
    "REFERENCE_RECIPE_ID",
    "REFERENCE_RECIPE_VERSION",
    "REFERENCE_SLOT_METADATA",
    "REFERENCE_SUPPORT_TIERS",
    "RESOURCE_AMOUNT_SLOT",
    "RESOURCE_DEPOSITS_SLOT",
    "RESOURCE_GEOGRAPHY_SLOT",
    "SEED_SLOT",
    "SENSORY_ACCURACY_SLOT",
    "SENSORY_RANGE_SLOT",
    "SPATIAL_EVIDENCE_ID",
    "WORLD_HEIGHT_SLOT",
    "WORLD_WIDTH_SLOT",
    "CompiledReferenceEcology",
    "ReferenceEcologyDiff",
    "ReferenceEcologyIntent",
    "ReferenceEcologyManifest",
    "ReferenceEvidencePlan",
    "ReferenceRuntimeEvidence",
    "ReferenceSlotMetadata",
    "assess_reference_readiness",
    "compile_reference_ecology",
    "default_reference_ecology_intent",
    "evidence_advisories",
    "is_slot_applicable",
    "normalized_reference_explicit_values",
    "resolve_reference_ecology",
    "semantic_reference_diff",
    "slot_metadata",
]
