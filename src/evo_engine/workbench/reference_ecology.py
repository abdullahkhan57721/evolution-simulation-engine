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
ExplorationMovement = Literal["moore", "von_neumann", "uniform", "gaussian"]
ResourceGeography = Literal["uniform", "two_patches"]
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


@attrs.frozen(slots=True, kw_only=True)
class ReferenceSlotMetadata:
    """Describe one stable recipe-local authoring slot."""

    slot_id: str
    label: str
    support_tier: SupportTier
    applicable_when: str | None = None


REFERENCE_SLOT_METADATA = (
    ReferenceSlotMetadata(slot_id=WORLD_WIDTH_SLOT, label="World width", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=WORLD_HEIGHT_SLOT, label="World height", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=FOUNDER_POPULATION_SLOT, label="Founder population", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=FOUNDER_ENERGY_SLOT, label="Founder starting energy", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=HORIZON_SLOT, label="Run horizon", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=SEED_SLOT, label="Random seed", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=MAX_SPEED_SLOT, label="Founder maximum speed", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=SENSORY_RANGE_SLOT, label="Founder sensory range", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=SENSORY_ACCURACY_SLOT, label="Founder sensory accuracy", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=EXPLORATION_MOVEMENT_SLOT, label="Exploration movement", support_tier="guided"),
    ReferenceSlotMetadata(
        slot_id=GAUSSIAN_STDDEV_SLOT,
        label="Gaussian standard deviation",
        support_tier="advanced",
        applicable_when="exploration movement is gaussian",
    ),
    ReferenceSlotMetadata(slot_id=RESOURCE_GEOGRAPHY_SLOT, label="Resource geography", support_tier="guided"),
    ReferenceSlotMetadata(slot_id=RESOURCE_AMOUNT_SLOT, label="Renewable resource amount", support_tier="advanced"),
    ReferenceSlotMetadata(slot_id=RESOURCE_DEPOSITS_SLOT, label="Resource deposits per step", support_tier="advanced"),
    ReferenceSlotMetadata(slot_id=PATCH_1_X_SLOT, label="Patch 1 center x", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=PATCH_1_Y_SLOT, label="Patch 1 center y", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=PATCH_1_RADIUS_SLOT, label="Patch 1 radius", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=PATCH_2_X_SLOT, label="Patch 2 center x", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=PATCH_2_Y_SLOT, label="Patch 2 center y", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=PATCH_2_RADIUS_SLOT, label="Patch 2 radius", support_tier="advanced", applicable_when="resource geography is two_patches"),
    ReferenceSlotMetadata(slot_id=MUTATION_ENABLED_SLOT, label="Mutation enabled", support_tier="advanced"),
    ReferenceSlotMetadata(slot_id=MUTATION_PROBABILITY_SLOT, label="Mutation probability (ppm)", support_tier="advanced", applicable_when="mutation is enabled"),
    ReferenceSlotMetadata(slot_id=MUTATION_MAX_CHANGE_SLOT, label="Mutation maximum change", support_tier="advanced", applicable_when="mutation is enabled"),
    ReferenceSlotMetadata(slot_id=RECOMBINATION_PROBABILITY_SLOT, label="Recombination probability (ppm)", support_tier="advanced"),
)

# Deliberately explicit: these are representative engine capabilities that are not
# official authoring slots for this recipe version.
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
            raise ValueError("requested must not contain duplicates.")
        for evidence_id in self.requested:
            if type(evidence_id) is not str or not evidence_id:
                raise TypeError("requested evidence IDs must be non-empty strings.")


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
    def observers(self) -> tuple[object, ...]:
        """Return state observers in deterministic recipe order."""
        values = (
            self.population_recorder,
            self.pedigree_recorder,
            self.genetic_recorder,
            self.spatial_recorder,
        )
        return tuple(value for value in values if value is not None)

    @property
    def telemetry_observers(self) -> tuple[object, ...]:
        """Return telemetry observers in deterministic recipe order."""
        values = (self.event_recorder, self.pedigree_recorder)
        return tuple(value for value in values if value is not None)


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


def slot_metadata(slot_id: str) -> ReferenceSlotMetadata:
    """Return metadata for one officially supported semantic slot."""
    for item in REFERENCE_SLOT_METADATA:
        if item.slot_id == slot_id:
            return item
    raise KeyError(f"Unsupported reference-ecology slot {slot_id!r}.")


def assess_reference_readiness(
    intent: ReferenceEcologyIntent,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> WorkbenchReadiness:
    """Check completeness, official support, and recipe-local applicability."""
    if not isinstance(intent, ReferenceEcologyIntent):
        raise TypeError("intent must be a ReferenceEcologyIntent.")
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("evidence_plan must be a ReferenceEvidencePlan or None.")

    missing: list[WorkbenchDiagnostic] = []
    blocked: list[WorkbenchDiagnostic] = []
    _required_range(missing, blocked, intent.width, WORLD_WIDTH_SLOT, 4, 50)
    _required_range(missing, blocked, intent.height, WORLD_HEIGHT_SLOT, 4, 50)
    _required_range(missing, blocked, intent.founder_population, FOUNDER_POPULATION_SLOT, 2, 100)
    _required_range(missing, blocked, intent.founder_energy, FOUNDER_ENERGY_SLOT, 1, 200)
    _required_range(missing, blocked, intent.horizon, HORIZON_SLOT, 1, 500)
    if intent.seed is None:
        missing.append(_missing(SEED_SLOT, "Select a reproducibility seed."))
    elif type(intent.seed) is not int:
        blocked.append(_unsupported(SEED_SLOT, "Seed must be an integer."))
    _required_range(missing, blocked, intent.max_speed, MAX_SPEED_SLOT, 0, 4)
    _required_range(missing, blocked, intent.sensory_range, SENSORY_RANGE_SLOT, 0, 20)
    _required_range(missing, blocked, intent.sensory_accuracy, SENSORY_ACCURACY_SLOT, 0, 100)

    if intent.exploration_movement is None:
        missing.append(_missing(EXPLORATION_MOVEMENT_SLOT, "Select exploration movement."))
    elif intent.exploration_movement not in {"moore", "von_neumann", "uniform", "gaussian"}:
        blocked.append(_unsupported(EXPLORATION_MOVEMENT_SLOT, "Supported movement choices are moore, von_neumann, uniform, and gaussian."))
    elif intent.exploration_movement == "gaussian":
        _required_range(missing, blocked, intent.gaussian_standard_deviation, GAUSSIAN_STDDEV_SLOT, 0, 10)

    if intent.resource_geography is None:
        missing.append(_missing(RESOURCE_GEOGRAPHY_SLOT, "Select resource geography."))
    elif intent.resource_geography not in {"uniform", "two_patches"}:
        blocked.append(_unsupported(RESOURCE_GEOGRAPHY_SLOT, "Supported resource geographies are uniform and two_patches."))
    _required_range(missing, blocked, intent.resource_generation_amount, RESOURCE_AMOUNT_SLOT, 1, 100)
    _required_range(missing, blocked, intent.resource_deposits_per_step, RESOURCE_DEPOSITS_SLOT, 1, 50)

    if intent.resource_geography == "two_patches":
        patch_values = (
            (intent.patch_1_center_x, PATCH_1_X_SLOT, 0, 49),
            (intent.patch_1_center_y, PATCH_1_Y_SLOT, 0, 49),
            (intent.patch_1_radius, PATCH_1_RADIUS_SLOT, 0, 20),
            (intent.patch_2_center_x, PATCH_2_X_SLOT, 0, 49),
            (intent.patch_2_center_y, PATCH_2_Y_SLOT, 0, 49),
            (intent.patch_2_radius, PATCH_2_RADIUS_SLOT, 0, 20),
        )
        for value, slot_id, minimum, maximum in patch_values:
            _required_range(missing, blocked, value, slot_id, minimum, maximum)
        if (
            intent.width is not None
            and intent.height is not None
            and type(intent.width) is int
            and type(intent.height) is int
        ):
            for value, slot_id, bound in (
                (intent.patch_1_center_x, PATCH_1_X_SLOT, intent.width),
                (intent.patch_2_center_x, PATCH_2_X_SLOT, intent.width),
                (intent.patch_1_center_y, PATCH_1_Y_SLOT, intent.height),
                (intent.patch_2_center_y, PATCH_2_Y_SLOT, intent.height),
            ):
                if type(value) is int and value >= bound:
                    blocked.append(_unsupported(slot_id, "Patch centers must lie inside the selected world."))

    if intent.mutation_enabled is None:
        missing.append(_missing(MUTATION_ENABLED_SLOT, "Choose whether mutation is enabled."))
    elif type(intent.mutation_enabled) is not bool:
        blocked.append(_unsupported(MUTATION_ENABLED_SLOT, "Mutation enabled must be boolean."))
    elif intent.mutation_enabled:
        _required_range(missing, blocked, intent.mutation_probability_ppm, MUTATION_PROBABILITY_SLOT, 0, 100_000)
        _required_range(missing, blocked, intent.mutation_max_change, MUTATION_MAX_CHANGE_SLOT, 1, 4)
    _required_range(missing, blocked, intent.recombination_probability_ppm, RECOMBINATION_PROBABILITY_SLOT, 0, 1_000_000)

    if not plan.requested:
        missing.append(WorkbenchDiagnostic(code="missing-evidence", message="Select at least one supported evidence stream."))
    for evidence_id in plan.requested:
        if evidence_id not in SUPPORTED_EVIDENCE_IDS:
            blocked.append(WorkbenchDiagnostic(code="unsupported-evidence", message=f"Reference recipe does not support evidence request {evidence_id!r}."))
    if SPATIAL_EVIDENCE_ID in plan.requested:
        blocked.append(
            WorkbenchDiagnostic(
                code="advisory-high-volume-evidence",
                message="Spatial replay records full committed world frames; consider storage cost for long runs.",
            )
        ) if False else None

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
    explicit = _normalized_explicit_values(intent)
    derived = _derived_values(explicit)
    return ReferenceEcologyManifest(
        recipe_id=REFERENCE_RECIPE_ID,
        recipe_version=REFERENCE_RECIPE_VERSION,
        compiler_id=REFERENCE_COMPILER_ID,
        compiler_version=REFERENCE_COMPILER_VERSION,
        engine_distribution=ENGINE_DISTRIBUTION,
        engine_version=_installed_engine_version(),
        explicit_values=explicit,
        derived_values=derived,
    )


def compile_reference_ecology(
    manifest: ReferenceEcologyManifest,
    evidence_plan: ReferenceEvidencePlan | None = None,
) -> CompiledReferenceEcology:
    """Reconstruct current typed reference composition and run lower preflight."""
    if not isinstance(manifest, ReferenceEcologyManifest):
        raise TypeError("manifest must be a ReferenceEcologyManifest.")
    _require_current_compatibility(manifest)
    plan = ReferenceEvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, ReferenceEvidencePlan):
        raise TypeError("evidence_plan must be a ReferenceEvidencePlan or None.")
    unsupported = set(plan.requested) - SUPPORTED_EVIDENCE_IDS
    if unsupported or not plan.requested:
        raise ValueError("Evidence plan must contain only supported reference evidence IDs.")
    expected_derived = _derived_values(manifest.explicit_values)
    if manifest.derived_values != expected_derived:
        raise IncompatibleManifestError("Persisted derived values do not match this reference recipe/compiler version.")

    config = _config_from_manifest(manifest)
    evidence = _runtime_evidence(plan)
    biological_spec = build_reference_spec(
        config,
        observers=cast(tuple, evidence.observers),
        telemetry_observers=cast(tuple, evidence.telemetry_observers),
    )
    return CompiledReferenceEcology(compiled=biological_spec.compile(), evidence=evidence)


def semantic_diff(
    before: ReferenceEcologyManifest,
    after: ReferenceEcologyManifest,
) -> ReferenceEcologyDiff:
    """Compare stable recipe-owned scientific values only."""
    if not isinstance(before, ReferenceEcologyManifest) or not isinstance(after, ReferenceEcologyManifest):
        raise TypeError("before and after must be ReferenceEcologyManifest values.")
    if (before.recipe_id, before.recipe_version) != (after.recipe_id, after.recipe_version):
        raise ValueError("Semantic diff requires the same recipe identity and version.")
    return ReferenceEcologyDiff(
        explicit_changes=_changes(before.explicit_values, after.explicit_values),
        derived_changes=_changes(before.derived_values, after.derived_values),
    )


def _normalized_explicit_values(intent: ReferenceEcologyIntent) -> ValuePairs:
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
        values.append((GAUSSIAN_STDDEV_SLOT, cast(int, intent.gaussian_standard_deviation)))
    values.extend(
        (
            (RESOURCE_GEOGRAPHY_SLOT, cast(str, intent.resource_geography)),
            (RESOURCE_AMOUNT_SLOT, cast(int, intent.resource_generation_amount)),
            (RESOURCE_DEPOSITS_SLOT, cast(int, intent.resource_deposits_per_step)),
        )
    )
    if intent.resource_geography == "two_patches":
        values.extend(
            (
                (PATCH_1_X_SLOT, cast(int, intent.patch_1_center_x)),
                (PATCH_1_Y_SLOT, cast(int, intent.patch_1_center_y)),
                (PATCH_1_RADIUS_SLOT, cast(int, intent.patch_1_radius)),
                (PATCH_2_X_SLOT, cast(int, intent.patch_2_center_x)),
                (PATCH_2_Y_SLOT, cast(int, intent.patch_2_center_y)),
                (PATCH_2_RADIUS_SLOT, cast(int, intent.patch_2_radius)),
            )
        )
    values.append((MUTATION_ENABLED_SLOT, cast(bool, intent.mutation_enabled)))
    if intent.mutation_enabled:
        values.extend(
            (
                (MUTATION_PROBABILITY_SLOT, cast(int, intent.mutation_probability_ppm)),
                (MUTATION_MAX_CHANGE_SLOT, cast(int, intent.mutation_max_change)),
            )
        )
    values.append((RECOMBINATION_PROBABILITY_SLOT, cast(int, intent.recombination_probability_ppm)))
    return tuple(values)


def _derived_values(explicit: ValuePairs) -> ValuePairs:
    movement = cast(str, _value_for(explicit, EXPLORATION_MOVEMENT_SLOT))
    geography = cast(str, _value_for(explicit, RESOURCE_GEOGRAPHY_SLOT))
    mutation_enabled = cast(bool, _value_for(explicit, MUTATION_ENABLED_SLOT))
    mutation_probability = (
        cast(int, _value_for(explicit, MUTATION_PROBABILITY_SLOT)) if mutation_enabled else 0
    )
    mutation_change = cast(int, _value_for(explicit, MUTATION_MAX_CHANGE_SLOT)) if mutation_enabled else 0
    if geography == "uniform":
        geography_description = "uniform"
    else:
        geography_description = json.dumps(
            {
                "patches": [
                    {
                        "center_x": _value_for(explicit, PATCH_1_X_SLOT),
                        "center_y": _value_for(explicit, PATCH_1_Y_SLOT),
                        "radius": _value_for(explicit, PATCH_1_RADIUS_SLOT),
                        "weight": 1,
                    },
                    {
                        "center_x": _value_for(explicit, PATCH_2_X_SLOT),
                        "center_y": _value_for(explicit, PATCH_2_Y_SLOT),
                        "radius": _value_for(explicit, PATCH_2_RADIUS_SLOT),
                        "weight": 1,
                    },
                ]
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    return (
        ("reference-ecology.resource-placement", geography_description),
        ("reference-ecology.exploration-pattern", movement),
        ("reference-ecology.effective-mutation-probability-ppm", mutation_probability),
        ("reference-ecology.effective-mutation-max-change", mutation_change),
        ("reference-ecology.genome-structure", "diploid-single-reference-chromosome"),
        ("reference-ecology.genetic-expression", "mean-integer-expression"),
        ("reference-ecology.inheritance", "sexual-meiotic-single-crossover"),
        ("reference-ecology.development", "reference-developmental-profile"),
        ("reference-ecology.reproduction", "reference-pairwise-sexual"),
        ("reference-ecology.food-targeting", "nearest-detectable-resource"),
        ("reference-ecology.mate-targeting", "preferred-compatible-mate"),
    )


def _config_from_manifest(manifest: ReferenceEcologyManifest) -> ReferenceEcologyConfig:
    explicit = manifest.explicit_values
    traits = attrs.evolve(
        ReferenceTraitValues(),
        max_speed=cast(int, _value_for(explicit, MAX_SPEED_SLOT)),
        sensory_range=cast(int, _value_for(explicit, SENSORY_RANGE_SLOT)),
        sensory_accuracy=cast(int, _value_for(explicit, SENSORY_ACCURACY_SLOT)),
    )
    movement_kind = cast(str, _value_for(explicit, EXPLORATION_MOVEMENT_SLOT))
    if movement_kind == "moore":
        movement = ReferenceMooreMovement()
    elif movement_kind == "von_neumann":
        movement = ReferenceVonNeumannMovement()
    elif movement_kind == "uniform":
        movement = ReferenceUniformMovement()
    elif movement_kind == "gaussian":
        movement = ReferenceGaussianMovement(
            standard_deviation=cast(int, _value_for(explicit, GAUSSIAN_STDDEV_SLOT))
        )
    else:
        raise IncompatibleManifestError("Unsupported persisted exploration movement.")

    geography = cast(str, _value_for(explicit, RESOURCE_GEOGRAPHY_SLOT))
    if geography == "uniform":
        placement = UniformResourcePlacement()
    elif geography == "two_patches":
        placement = PatchyResourcePlacement(
            patches=(
                ResourcePatch(
                    center_x=cast(int, _value_for(explicit, PATCH_1_X_SLOT)),
                    center_y=cast(int, _value_for(explicit, PATCH_1_Y_SLOT)),
                    radius=cast(int, _value_for(explicit, PATCH_1_RADIUS_SLOT)),
                ),
                ResourcePatch(
                    center_x=cast(int, _value_for(explicit, PATCH_2_X_SLOT)),
                    center_y=cast(int, _value_for(explicit, PATCH_2_Y_SLOT)),
                    radius=cast(int, _value_for(explicit, PATCH_2_RADIUS_SLOT)),
                ),
            )
        )
    else:
        raise IncompatibleManifestError("Unsupported persisted resource geography.")

    mutation_enabled = cast(bool, _value_for(explicit, MUTATION_ENABLED_SLOT))
    mutation_probability = cast(int, manifest.derived_value("reference-ecology.effective-mutation-probability-ppm"))
    mutation_change = cast(int, manifest.derived_value("reference-ecology.effective-mutation-max-change"))
    if not mutation_enabled and (mutation_probability != 0 or mutation_change != 0):
        raise IncompatibleManifestError("Disabled mutation must resolve to zero mutation parameters.")

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
        mutation_probability_ppm=mutation_probability,
        mutation_max_change=mutation_change,
        recombination_probability_ppm=cast(int, _value_for(explicit, RECOMBINATION_PROBABILITY_SLOT)),
        resource_generation_amount=cast(int, _value_for(explicit, RESOURCE_AMOUNT_SLOT)),
        resource_deposits_per_step=cast(int, _value_for(explicit, RESOURCE_DEPOSITS_SLOT)),
        resource_placement_model=placement,
    )


def _runtime_evidence(plan: ReferenceEvidencePlan) -> ReferenceRuntimeEvidence:
    requested = set(plan.requested)
    return ReferenceRuntimeEvidence(
        population_recorder=(
            PopulationRecorder(trait_names=(MAX_SPEED, SENSORY_RANGE, SENSORY_ACCURACY))
            if POPULATION_EVIDENCE_ID in requested
            else None
        ),
        event_recorder=EventRecorder() if EVENT_EVIDENCE_ID in requested else None,
        pedigree_recorder=PedigreeRecorder() if PEDIGREE_EVIDENCE_ID in requested else None,
        genetic_recorder=(
            GeneticCompositionRecorder(locus_names=(MAX_SPEED, SENSORY_RANGE, SENSORY_ACCURACY))
            if GENETIC_EVIDENCE_ID in requested
            else None
        ),
        spatial_recorder=SpatialRecorder() if SPATIAL_EVIDENCE_ID in requested else None,
    )


def _changes(before: ValuePairs, after: ValuePairs) -> tuple[SemanticChange, ...]:
    before_values = dict(before)
    after_values = dict(after)
    changes: list[SemanticChange] = []
    for slot_id in dict.fromkeys((*before_values, *after_values)):
        old = before_values.get(slot_id, "<inactive>")
        new = after_values.get(slot_id, "<inactive>")
        if old != new:
            changes.append(SemanticChange(slot_id=slot_id, before=old, after=new))
    return tuple(changes)


def _required_range(
    missing: list[WorkbenchDiagnostic],
    blocked: list[WorkbenchDiagnostic],
    value: int | None,
    slot_id: str,
    minimum: int,
    maximum: int,
) -> None:
    if value is None:
        missing.append(_missing(slot_id, f"Select {slot_id}."))
    elif type(value) is not int or not minimum <= value <= maximum:
        blocked.append(_unsupported(slot_id, f"Workbench support is {minimum} through {maximum}."))


def _missing(slot_id: str, message: str) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(code="missing-selection", slot_id=slot_id, message=message)


def _unsupported(slot_id: str, message: str) -> WorkbenchDiagnostic:
    return WorkbenchDiagnostic(code="unsupported-value", slot_id=slot_id, message=message)


def _require_current_compatibility(manifest: ReferenceEcologyManifest) -> None:
    expected = (
        REFERENCE_RECIPE_ID,
        REFERENCE_RECIPE_VERSION,
        REFERENCE_COMPILER_ID,
        REFERENCE_COMPILER_VERSION,
        ENGINE_DISTRIBUTION,
        _installed_engine_version(),
    )
    actual = (
        manifest.recipe_id,
        manifest.recipe_version,
        manifest.compiler_id,
        manifest.compiler_version,
        manifest.engine_distribution,
        manifest.engine_version,
    )
    if actual != expected:
        raise IncompatibleManifestError("Persisted reference manifest is not compatible with the current recipe/compiler/engine.")


def _installed_engine_version() -> str:
    try:
        return metadata.version(ENGINE_DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "0+unknown"


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
    if len(result) != len({item[0] for item in result}):
        raise ValueError(f"{key} must not contain duplicate semantic IDs.")
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
    "GENETIC_EVIDENCE_ID",
    "GAUSSIAN_STDDEV_SLOT",
    "MUTATION_ENABLED_SLOT",
    "MUTATION_MAX_CHANGE_SLOT",
    "MUTATION_PROBABILITY_SLOT",
    "PEDIGREE_EVIDENCE_ID",
    "REFERENCE_EXTENSION_CAPABILITIES",
    "REFERENCE_RECIPE_ID",
    "REFERENCE_RECIPE_VERSION",
    "REFERENCE_SLOT_METADATA",
    "RESOURCE_GEOGRAPHY_SLOT",
    "SPATIAL_EVIDENCE_ID",
    "CompiledReferenceEcology",
    "ReferenceEcologyDiff",
    "ReferenceEcologyIntent",
    "ReferenceEcologyManifest",
    "ReferenceEvidencePlan",
    "ReferenceRuntimeEvidence",
    "ReferenceSlotMetadata",
    "assess_reference_readiness",
    "compile_reference_ecology",
    "resolve_reference_ecology",
    "semantic_diff",
    "slot_metadata",
]
