"""Curated B3 Workbench study with exact persistence and bounded fork lineage."""

from __future__ import annotations

import hashlib
import json
import uuid
from importlib import metadata
from typing import Literal, cast

import attrs

from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunEvidence,
    B3RunSummary,
    run_b3_flagship,
    summarize_b3_run,
)
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_BROAD_PATCH_RADIUS,
    B3_COMPACT_PATCH_RADIUS,
    B3_CONFIRMATION_SEEDS,
    B3_COUNTERBALANCE_SEEDS,
    B3_DISCOVERY_SEEDS,
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_MAX_STEPS,
    B3_PATCH_CENTERS,
    B3_PRIMARY_STEP,
    B3_RESOURCE_DEPOSITS_PER_STEP,
    B3_RESOURCE_GENERATION_AMOUNT,
    B3FlagshipSpecification,
    B3FounderAssignment,
    build_b3_flagship_specification,
    validate_b3_treatment_integrity,
)
from evo_engine.presets.reference_ecology.movement import ReferenceMooreMovement
from evo_engine.workbench.controlled_locomotion import (
    ENGINE_DISTRIBUTION,
    IncompatibleManifestError,
    WorkbenchDiagnostic,
    WorkbenchNotReadyError,
    WorkbenchReadiness,
)
from evo_engine.workbench.study import WorkbenchRunProvenance

B3_RECIPE_ID = "curated-b3-flagship"
B3_RECIPE_VERSION = 1
B3_COMPILER_ID = "workbench.curated-b3-flagship"
B3_COMPILER_VERSION = 1
B3_STUDY_FORMAT_ID = "evolution-experiment-workbench-curated-b3-study"
B3_STUDY_FORMAT_VERSION = 1

B3_SCENARIO_ORIGIN_ID = "confirmed-b3-flagship"
B3_VALIDATED_SCENARIO_ID = "confirmed-b3-flagship-radius-1"
B3_TREATMENT_RADIUS_SLOT = "b3.resource-geography.treatment-radius"

B3_POPULATION_EVIDENCE_ID = "b3.population"
B3_GENETIC_EVIDENCE_ID = "b3.genetic-composition"
B3_SPATIAL_EVIDENCE_ID = "b3.spatial"
B3_INDIVIDUAL_TRAIT_EVIDENCE_ID = "b3.individual-max-speed"
B3_EVENT_EVIDENCE_ID = "b3.committed-events"
B3_PEDIGREE_EVIDENCE_ID = "b3.pedigree"
B3_REQUIRED_EVIDENCE_IDS = (
    B3_POPULATION_EVIDENCE_ID,
    B3_GENETIC_EVIDENCE_ID,
    B3_SPATIAL_EVIDENCE_ID,
    B3_INDIVIDUAL_TRAIT_EVIDENCE_ID,
    B3_EVENT_EVIDENCE_ID,
    B3_PEDIGREE_EVIDENCE_ID,
)

B3ManifestScalar = str | int | float | bool
B3ValuePairs = tuple[tuple[str, B3ManifestScalar], ...]
B3StudyKind = Literal["validated-b3", "b3-derived-custom"]


@attrs.frozen(slots=True, kw_only=True)
class B3CuratedIntent:
    """Persist the one supported B3 scientific authoring choice."""

    treatment_radius: int | None = B3_COMPACT_PATCH_RADIUS

    def __attrs_post_init__(self) -> None:
        if self.treatment_radius is not None and type(self.treatment_radius) is not int:
            raise TypeError("treatment_radius must be an integer or None.")


@attrs.frozen(slots=True, kw_only=True)
class B3EvidencePlan:
    """Persist B3 evidence intent separately from the scientific manifest."""

    requested: tuple[str, ...] = B3_REQUIRED_EVIDENCE_IDS

    def __attrs_post_init__(self) -> None:
        if type(self.requested) is not tuple:
            raise TypeError("requested must be a tuple.")
        if self.requested != B3_REQUIRED_EVIDENCE_IDS:
            raise ValueError(
                "The curated B3 recipe requires its frozen existing evidence set."
            )


@attrs.frozen(slots=True, kw_only=True)
class B3SemanticChange:
    """Describe one B3 recipe-scoped scientific value change."""

    slot_id: str
    before: B3ManifestScalar
    after: B3ManifestScalar


@attrs.frozen(slots=True, kw_only=True)
class B3ScenarioIdentityChange:
    """Describe loss or change of validated curated-scenario identity."""

    before: str | None
    after: str | None


@attrs.frozen(slots=True, kw_only=True)
class B3CuratedDiff:
    """Separate authored change, derived consequences, and scenario identity."""

    explicit_changes: tuple[B3SemanticChange, ...]
    derived_changes: tuple[B3SemanticChange, ...]
    scenario_identity_change: B3ScenarioIdentityChange | None
    unchanged_frozen_slots: tuple[str, ...]


@attrs.frozen(slots=True, kw_only=True)
class B3CuratedManifest:
    """Store the exact resolved scientific meaning of one curated B3 revision."""

    recipe_id: str
    recipe_version: int
    compiler_id: str
    compiler_version: int
    engine_distribution: str
    engine_version: str
    explicit_values: B3ValuePairs
    derived_values: B3ValuePairs

    def __attrs_post_init__(self) -> None:
        _validate_manifest_identity(self)
        _validate_pairs(self.explicit_values, name="explicit_values")
        _validate_pairs(self.derived_values, name="derived_values")
        if tuple(key for key, _ in self.explicit_values) != (B3_TREATMENT_RADIUS_SLOT,):
            raise ValueError(
                "explicit_values must contain only the stable B3 treatment-radius slot."
            )

    @property
    def digest(self) -> str:
        """Return a stable digest used by run-to-manifest provenance."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def explicit_value(self, slot_id: str) -> B3ManifestScalar:
        """Return one explicit value by stable scientific slot ID."""
        return _value_for(self.explicit_values, slot_id)

    def derived_value(self, slot_id: str) -> B3ManifestScalar:
        """Return one derived value by stable scientific slot ID."""
        return _value_for(self.derived_values, slot_id)

    def to_json(self) -> str:
        """Serialize the resolved B3 manifest canonically."""
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
    def from_json(cls, value: str) -> "B3CuratedManifest":
        """Deserialize a persisted manifest without resolving current defaults."""
        decoded = _json_object(value, name="manifest")
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
class B3MatchedSpecifications:
    """Hold one matched uniform/treatment B3 specification pair."""

    seed: int
    founder_assignment: B3FounderAssignment
    control: B3FlagshipSpecification
    treatment: B3FlagshipSpecification


@attrs.frozen(slots=True, kw_only=True)
class CompiledB3CuratedStudy:
    """Hold B3 specifications reconstructed from an exact compatible manifest."""

    confirmation_pairs: tuple[B3MatchedSpecifications, ...]
    radius_sensitivity: tuple[B3FlagshipSpecification, ...]
    counterbalanced_pairs: tuple[B3MatchedSpecifications, ...]


@attrs.frozen(slots=True, kw_only=True)
class B3StudyRevision:
    """Persist one immutable curated B3 revision and exact scenario lineage."""

    revision_id: str
    intent: B3CuratedIntent
    manifest: B3CuratedManifest
    evidence_plan: B3EvidencePlan
    scenario_origin: str
    scenario_identity: str | None
    parent_revision_id: str | None = None
    runs: tuple[WorkbenchRunProvenance, ...] = ()

    def __attrs_post_init__(self) -> None:
        _require_nonempty(self.revision_id, "revision_id")
        if not isinstance(self.intent, B3CuratedIntent):
            raise TypeError("intent must be a B3CuratedIntent.")
        if not isinstance(self.manifest, B3CuratedManifest):
            raise TypeError("manifest must be a B3CuratedManifest.")
        if not isinstance(self.evidence_plan, B3EvidencePlan):
            raise TypeError("evidence_plan must be a B3EvidencePlan.")
        if self.scenario_origin != B3_SCENARIO_ORIGIN_ID:
            raise ValueError("B3 scenario_origin must retain the confirmed B3 origin.")
        expected_identity = _scenario_identity(self.intent.treatment_radius)
        if self.scenario_identity != expected_identity:
            raise ValueError("scenario_identity does not match the exact B3 manifest.")
        if self.parent_revision_id is not None:
            _require_nonempty(self.parent_revision_id, "parent_revision_id")
            if self.parent_revision_id == self.revision_id:
                raise ValueError("parent_revision_id must differ from revision_id.")
        _validate_revision_alignment(self)
        _validate_runs(self)

    @property
    def study_kind(self) -> B3StudyKind:
        """Return whether this is exact validated B3 or a B3-derived custom fork."""
        return (
            "validated-b3"
            if self.scenario_identity == B3_VALIDATED_SCENARIO_ID
            else "b3-derived-custom"
        )

    def with_run(self, provenance: WorkbenchRunProvenance) -> "B3StudyRevision":
        """Return a new revision snapshot with one completed-study run reference."""
        if not isinstance(provenance, WorkbenchRunProvenance):
            raise TypeError("provenance must be WorkbenchRunProvenance.")
        _validate_run_for_revision(self, provenance)
        if any(run.run_id == provenance.run_id for run in self.runs):
            raise ValueError(f"Run ID {provenance.run_id!r} is already recorded.")
        return attrs.evolve(self, runs=(*self.runs, provenance))

    def to_json(self) -> str:
        """Serialize exact B3 study persistence canonically."""
        return json.dumps(
            {
                "evidence_plan": {"requested": list(self.evidence_plan.requested)},
                "format_id": B3_STUDY_FORMAT_ID,
                "format_version": B3_STUDY_FORMAT_VERSION,
                "intent": {"treatment_radius": self.intent.treatment_radius},
                "manifest_json": self.manifest.to_json(),
                "parent_revision_id": self.parent_revision_id,
                "revision_id": self.revision_id,
                "runs": [_run_to_mapping(run) for run in self.runs],
                "scenario_identity": self.scenario_identity,
                "scenario_origin": self.scenario_origin,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @classmethod
    def from_json(cls, value: str) -> "B3StudyRevision":
        """Load stored B3 intent/manifest exactly without re-resolving it."""
        decoded = _json_object(value, name="study")
        if decoded.get("format_id") != B3_STUDY_FORMAT_ID:
            raise ValueError("Unsupported curated B3 study format ID.")
        if decoded.get("format_version") != B3_STUDY_FORMAT_VERSION:
            raise ValueError("Unsupported curated B3 study format version.")
        intent_mapping = _required_mapping(decoded, "intent")
        plan_mapping = _required_mapping(decoded, "evidence_plan")
        requested = _required_list(plan_mapping, "requested")
        runs = _required_list(decoded, "runs")
        return cls(
            revision_id=_required_str(decoded, "revision_id"),
            parent_revision_id=_optional_str(decoded, "parent_revision_id"),
            intent=B3CuratedIntent(
                treatment_radius=_optional_int(intent_mapping, "treatment_radius")
            ),
            manifest=B3CuratedManifest.from_json(
                _required_str(decoded, "manifest_json")
            ),
            evidence_plan=B3EvidencePlan(
                requested=tuple(_strings(requested, "evidence_plan.requested"))
            ),
            scenario_origin=_required_str(decoded, "scenario_origin"),
            scenario_identity=_optional_str(decoded, "scenario_identity"),
            runs=tuple(
                _run_from_mapping(item, index=index) for index, item in enumerate(runs)
            ),
        )


@attrs.frozen(slots=True, kw_only=True)
class B3MatchedRunArtifacts:
    """Bundle existing B3 evidence and summary for one matched pair."""

    control_evidence: B3RunEvidence
    treatment_evidence: B3RunEvidence
    summary: B3MatchedPairSummary


@attrs.frozen(slots=True, kw_only=True)
class B3SingleRunArtifacts:
    """Bundle existing B3 evidence and summary for one single B3 run."""

    evidence: B3RunEvidence
    summary: B3RunSummary


@attrs.frozen(slots=True, kw_only=True)
class B3CuratedRunResult:
    """Expose existing authoritative B3 evidence/results from one study run."""

    provenance: WorkbenchRunProvenance
    scenario_origin: str
    scenario_identity: str | None
    confirmation: tuple[B3MatchedRunArtifacts, ...]
    radius_sensitivity: tuple[B3SingleRunArtifacts, ...]
    counterbalanced: tuple[B3MatchedRunArtifacts, ...]


def assess_b3_readiness(
    intent: B3CuratedIntent,
    evidence_plan: B3EvidencePlan | None = None,
) -> WorkbenchReadiness:
    """Check the bounded WB2 authoring surface before B3 composition."""
    if not isinstance(intent, B3CuratedIntent):
        raise TypeError("intent must be a B3CuratedIntent.")
    plan = B3EvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, B3EvidencePlan):
        raise TypeError("evidence_plan must be B3EvidencePlan or None.")
    if intent.treatment_radius is None:
        return WorkbenchReadiness(
            state="draft",
            diagnostics=(
                WorkbenchDiagnostic(
                    code="missing-selection",
                    slot_id=B3_TREATMENT_RADIUS_SLOT,
                    message="Select the supported B3 treatment radius.",
                ),
            ),
        )
    if intent.treatment_radius not in (
        B3_COMPACT_PATCH_RADIUS,
        B3_BROAD_PATCH_RADIUS,
    ):
        return WorkbenchReadiness(
            state="blocked",
            diagnostics=(
                WorkbenchDiagnostic(
                    code="unsupported-value",
                    slot_id=B3_TREATMENT_RADIUS_SLOT,
                    message=(
                        "WB2 supports only B3 radius 1 and its radius 2 sensitivity."
                    ),
                ),
            ),
        )
    return WorkbenchReadiness(state="ready")


def resolve_b3_curated(
    intent: B3CuratedIntent,
    evidence_plan: B3EvidencePlan | None = None,
) -> B3CuratedManifest:
    """Resolve B3 authoring intent into an immutable exact scientific manifest."""
    readiness = assess_b3_readiness(intent, evidence_plan)
    if readiness.state != "ready":
        raise WorkbenchNotReadyError(readiness)
    radius = cast(int, intent.treatment_radius)
    return B3CuratedManifest(
        recipe_id=B3_RECIPE_ID,
        recipe_version=B3_RECIPE_VERSION,
        compiler_id=B3_COMPILER_ID,
        compiler_version=B3_COMPILER_VERSION,
        engine_distribution=ENGINE_DISTRIBUTION,
        engine_version=_installed_engine_version(),
        explicit_values=((B3_TREATMENT_RADIUS_SLOT, radius),),
        derived_values=_derived_values(radius),
    )


def compile_b3_curated(
    manifest: B3CuratedManifest,
    evidence_plan: B3EvidencePlan | None = None,
) -> CompiledB3CuratedStudy:
    """Reconstruct exact B3 cases through the existing authoritative builders."""
    if not isinstance(manifest, B3CuratedManifest):
        raise TypeError("manifest must be a B3CuratedManifest.")
    _require_current_compatibility(manifest)
    plan = B3EvidencePlan() if evidence_plan is None else evidence_plan
    if not isinstance(plan, B3EvidencePlan):
        raise TypeError("evidence_plan must be B3EvidencePlan or None.")

    radius = _exact_int(
        manifest.explicit_value(B3_TREATMENT_RADIUS_SLOT),
        B3_TREATMENT_RADIUS_SLOT,
    )
    if radius not in (B3_COMPACT_PATCH_RADIUS, B3_BROAD_PATCH_RADIUS):
        raise IncompatibleManifestError("Persisted B3 treatment radius is unsupported.")
    expected = _derived_values(radius)
    if manifest.derived_values != expected:
        raise IncompatibleManifestError(
            "Persisted B3 assumptions no longer match this recipe/compiler."
        )

    confirmation_pairs = tuple(
        _build_matched_specifications(
            seed=seed,
            founder_assignment="standard",
            treatment_radius=radius,
        )
        for seed in B3_CONFIRMATION_SEEDS
    )
    radius_sensitivity = (
        tuple(
            build_b3_flagship_specification(
                seed=seed,
                environment="broad_patch",
                founder_assignment="standard",
            )
            for seed in B3_CONFIRMATION_SEEDS
        )
        if radius == B3_COMPACT_PATCH_RADIUS
        else ()
    )
    counterbalanced_pairs = tuple(
        _build_matched_specifications(
            seed=seed,
            founder_assignment="swapped",
            treatment_radius=radius,
        )
        for seed in B3_COUNTERBALANCE_SEEDS
    )
    return CompiledB3CuratedStudy(
        confirmation_pairs=confirmation_pairs,
        radius_sensitivity=radius_sensitivity,
        counterbalanced_pairs=counterbalanced_pairs,
    )


def create_b3_study_revision(
    *,
    revision_id: str,
    evidence_plan: B3EvidencePlan | None = None,
) -> B3StudyRevision:
    """Create the canonical exact validated B3 study revision."""
    _require_nonempty(revision_id, "revision_id")
    plan = B3EvidencePlan() if evidence_plan is None else evidence_plan
    intent = B3CuratedIntent(treatment_radius=B3_COMPACT_PATCH_RADIUS)
    manifest = resolve_b3_curated(intent, plan)
    return B3StudyRevision(
        revision_id=revision_id,
        intent=intent,
        manifest=manifest,
        evidence_plan=plan,
        scenario_origin=B3_SCENARIO_ORIGIN_ID,
        scenario_identity=B3_VALIDATED_SCENARIO_ID,
    )


def fork_b3_study_revision(
    parent: B3StudyRevision,
    *,
    revision_id: str,
    treatment_radius: int = B3_BROAD_PATCH_RADIUS,
) -> B3StudyRevision:
    """Fork canonical B3 only along its pre-established radius-2 sensitivity."""
    if not isinstance(parent, B3StudyRevision):
        raise TypeError("parent must be a B3StudyRevision.")
    _require_nonempty(revision_id, "revision_id")
    if revision_id == parent.revision_id:
        raise ValueError("A fork must use a new revision_id.")
    if parent.scenario_identity != B3_VALIDATED_SCENARIO_ID:
        raise ValueError("WB2 supports a scientific fork only from canonical B3.")
    if treatment_radius != B3_BROAD_PATCH_RADIUS:
        raise ValueError("WB2 supports only the B3 radius-1 to radius-2 fork.")

    intent = B3CuratedIntent(treatment_radius=treatment_radius)
    manifest = resolve_b3_curated(intent, parent.evidence_plan)
    return B3StudyRevision(
        revision_id=revision_id,
        parent_revision_id=parent.revision_id,
        intent=intent,
        manifest=manifest,
        evidence_plan=parent.evidence_plan,
        scenario_origin=parent.scenario_origin,
        scenario_identity=None,
    )


def diff_b3_study_revisions(
    before: B3StudyRevision,
    after: B3StudyRevision,
) -> B3CuratedDiff:
    """Return the stable scientific diff between two B3 study revisions."""
    if not isinstance(before, B3StudyRevision) or not isinstance(
        after, B3StudyRevision
    ):
        raise TypeError("before and after must be B3StudyRevision values.")
    if (before.manifest.recipe_id, before.manifest.recipe_version) != (
        after.manifest.recipe_id,
        after.manifest.recipe_version,
    ):
        raise ValueError("B3 semantic diff requires the same recipe identity/version.")

    explicit = _changes(before.manifest.explicit_values, after.manifest.explicit_values)
    derived = _changes(before.manifest.derived_values, after.manifest.derived_values)
    unchanged = tuple(
        slot_id
        for slot_id, value in before.manifest.derived_values
        if after.manifest.derived_value(slot_id) == value
    )
    identity_change = (
        None
        if before.scenario_identity == after.scenario_identity
        else B3ScenarioIdentityChange(
            before=before.scenario_identity,
            after=after.scenario_identity,
        )
    )
    return B3CuratedDiff(
        explicit_changes=explicit,
        derived_changes=derived,
        scenario_identity_change=identity_change,
        unchanged_frozen_slots=unchanged,
    )


def run_b3_study_revision(
    revision: B3StudyRevision,
    *,
    run_id: str | None = None,
) -> B3CuratedRunResult:
    """Run exact B3 cases and expose existing B3 evidence-derived result contracts."""
    if not isinstance(revision, B3StudyRevision):
        raise TypeError("revision must be a B3StudyRevision.")
    resolved_run_id = uuid.uuid4().hex if run_id is None else run_id
    _require_nonempty(resolved_run_id, "run_id")

    compiled = compile_b3_curated(revision.manifest, revision.evidence_plan)
    confirmation = tuple(_run_pair(pair) for pair in compiled.confirmation_pairs)
    sensitivity = tuple(
        _run_single(specification) for specification in compiled.radius_sensitivity
    )
    counterbalanced = tuple(_run_pair(pair) for pair in compiled.counterbalanced_pairs)
    provenance = WorkbenchRunProvenance(
        run_id=resolved_run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(
            f"{resolved_run_id}:b3-confirmation-evidence",
            f"{resolved_run_id}:b3-radius-sensitivity-evidence",
            f"{resolved_run_id}:b3-counterbalance-evidence",
        )
        if compiled.radius_sensitivity
        else (
            f"{resolved_run_id}:b3-confirmation-evidence",
            f"{resolved_run_id}:b3-counterbalance-evidence",
        ),
        result_references=(
            f"{resolved_run_id}:b3-confirmation-summaries",
            f"{resolved_run_id}:b3-radius-sensitivity-summaries",
            f"{resolved_run_id}:b3-counterbalance-summaries",
        )
        if compiled.radius_sensitivity
        else (
            f"{resolved_run_id}:b3-confirmation-summaries",
            f"{resolved_run_id}:b3-counterbalance-summaries",
        ),
    )
    return B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=confirmation,
        radius_sensitivity=sensitivity,
        counterbalanced=counterbalanced,
    )


def _run_pair(specifications: B3MatchedSpecifications) -> B3MatchedRunArtifacts:
    control_evidence = run_b3_flagship(specifications.control)
    treatment_evidence = run_b3_flagship(specifications.treatment)
    control = summarize_b3_run(control_evidence)
    treatment = summarize_b3_run(treatment_evidence)
    summary = B3MatchedPairSummary(
        seed=specifications.seed,
        founder_assignment=specifications.founder_assignment,
        control=control,
        treatment=treatment,
    )
    return B3MatchedRunArtifacts(
        control_evidence=control_evidence,
        treatment_evidence=treatment_evidence,
        summary=summary,
    )


def _run_single(specification: B3FlagshipSpecification) -> B3SingleRunArtifacts:
    evidence = run_b3_flagship(specification)
    return B3SingleRunArtifacts(
        evidence=evidence,
        summary=summarize_b3_run(evidence),
    )


def _build_matched_specifications(
    *,
    seed: int,
    founder_assignment: B3FounderAssignment,
    treatment_radius: int,
) -> B3MatchedSpecifications:
    control = build_b3_flagship_specification(
        seed=seed,
        environment="uniform",
        founder_assignment=founder_assignment,
    )
    compact = build_b3_flagship_specification(
        seed=seed,
        environment="compact_patch",
        founder_assignment=founder_assignment,
    )
    validate_b3_treatment_integrity(control, compact)
    treatment = compact
    if treatment_radius == B3_BROAD_PATCH_RADIUS:
        treatment = build_b3_flagship_specification(
            seed=seed,
            environment="broad_patch",
            founder_assignment=founder_assignment,
        )
        _validate_broad_sensitivity(compact=compact, broad=treatment)
    return B3MatchedSpecifications(
        seed=seed,
        founder_assignment=founder_assignment,
        control=control,
        treatment=treatment,
    )


def _validate_broad_sensitivity(
    *,
    compact: B3FlagshipSpecification,
    broad: B3FlagshipSpecification,
) -> None:
    if broad.environment != "broad_patch":
        raise IncompatibleManifestError("B3 radius-2 fork must use broad_patch.")
    normalized = attrs.evolve(
        broad,
        environment="compact_patch",
        config=attrs.evolve(
            broad.config,
            resource_placement_model=compact.config.resource_placement_model,
        ),
    )
    if normalized != compact:
        raise IncompatibleManifestError(
            "Current B3 radius-2 sensitivity differs outside resource placement."
        )


def _derived_values(radius: int) -> B3ValuePairs:
    environment = (
        "compact_patch" if radius == B3_COMPACT_PATCH_RADIUS else "broad_patch"
    )
    specification = build_b3_flagship_specification(
        seed=B3_CONFIRMATION_SEEDS[0],
        environment=environment,
        founder_assignment="standard",
    )
    config = specification.config
    if not isinstance(config.exploration_movement, ReferenceMooreMovement):
        raise IncompatibleManifestError(
            "B3 expected the authoritative reference Moore exploration movement."
        )
    traits = config.traits
    tradeoffs = config.physiological_tradeoffs
    investment = config.mating_type_investment_scales
    treatment_label = (
        "two-equal-weight-radius-1-patches"
        if radius == B3_COMPACT_PATCH_RADIUS
        else "two-equal-weight-radius-2-patches"
    )
    radius_sensitivity_assignment = (
        "standard"
        if radius == B3_COMPACT_PATCH_RADIUS
        else "not-applicable-promoted-primary-treatment"
    )
    representative_semantics = (
        "selected-after-confirmation-by-predeclared-b3-rule"
        if radius == B3_COMPACT_PATCH_RADIUS
        else "not-inherited-by-derived-fork"
    )
    return (
        ("b3.study-design", "matched-uniform-versus-resource-geography"),
        ("b3.control-resource-geography", "uniform"),
        ("b3.treatment-resource-geography", treatment_label),
        ("b3.resource-geography.patch-radius", radius),
        ("b3.resource-geography.patch-centers", _coordinate_text(B3_PATCH_CENTERS)),
        ("b3.resource-geography.patch-weights", "1,1"),
        (
            "b3.treatment-integrity",
            "same-seed-control-and-primary-treatment-differ-only-resource-placement",
        ),
        ("b3.rng-coupling", "blocked-by-seed-not-lockstep-after-treatment"),
        (
            "b3.radius-sensitivity-role",
            "predeclared-radius-2-sensitivity"
            if radius == B3_COMPACT_PATCH_RADIUS
            else "promoted-to-primary-treatment",
        ),
        ("b3.radius-sensitivity-founder-assignment", radius_sensitivity_assignment),
        ("b3.focal-trait", specification.focal_trait),
        (
            "b3.focal-trait-semantics",
            "genetic-phenotype-maximum-movement-capacity",
        ),
        ("b3.founder-variant-values", _integer_text(specification.variant_values)),
        ("b3.founder-construction", "balanced-homozygous"),
        ("b3.primary-founder-assignment", specification.founder_assignment),
        ("b3.counterbalance-founder-assignment", "swapped"),
        (
            "b3.counterbalance-design",
            "swap-focal-values-across-deterministic-founder-id-position-pattern",
        ),
        ("b3.initial-high-speed-allele-frequency", 0.5),
        ("b3.discovery-seeds", _integer_text(B3_DISCOVERY_SEEDS)),
        ("b3.confirmation-seeds", _integer_text(B3_CONFIRMATION_SEEDS)),
        ("b3.counterbalance-seeds", _integer_text(B3_COUNTERBALANCE_SEEDS)),
        ("b3.primary-step-index", B3_PRIMARY_STEP),
        ("b3.replicate-unit", "simulation-run"),
        ("b3.confirmation-blocking", "matched-by-seed"),
        ("b3.representative-story-semantics", representative_semantics),
        (
            "b3.representative-selection-authority",
            "existing-b3-scientific-handoff"
            if radius == B3_COMPACT_PATCH_RADIUS
            else "none-inherited-by-derived-fork",
        ),
        (
            "b3.original-headline-claim-applicability",
            "validated-scenario-only"
            if radius == B3_COMPACT_PATCH_RADIUS
            else "not-inherited-by-derived-fork",
        ),
        ("b3.config.width", config.width),
        ("b3.config.height", config.height),
        ("b3.config.initial-population", config.initial_population),
        ("b3.config.initial-energy", config.initial_energy),
        ("b3.config.max-steps", config.max_steps),
        ("b3.config.exploration-movement", "reference-moore"),
        ("b3.config.trait.adult-body-mass", traits.adult_body_mass),
        ("b3.config.trait.growth-rate", traits.growth_rate),
        ("b3.config.trait.max-speed-background", traits.max_speed),
        (
            "b3.config.trait.locomotion-cost-coefficient",
            traits.locomotion_cost_coefficient,
        ),
        ("b3.config.trait.sensory-range", traits.sensory_range),
        ("b3.config.trait.sensory-accuracy", traits.sensory_accuracy),
        ("b3.config.trait.max-intake-rate", traits.max_intake_rate),
        (
            "b3.config.trait.assimilation-efficiency",
            traits.assimilation_efficiency,
        ),
        (
            "b3.config.trait.metabolic-cost-coefficient",
            traits.metabolic_cost_coefficient,
        ),
        (
            "b3.config.trait.energy-conservation-threshold",
            traits.energy_conservation_threshold,
        ),
        ("b3.config.trait.energy-reserve", traits.energy_reserve),
        ("b3.config.trait.attack-strength", traits.attack_strength),
        ("b3.config.trait.defense", traits.defense),
        ("b3.config.trait.mate-search-range", traits.mate_search_range),
        ("b3.config.trait.choosiness", traits.choosiness),
        ("b3.config.trait.mating-signal", traits.mating_signal),
        ("b3.config.trait.maturity-age", traits.maturity_age),
        (
            "b3.config.trait.reproduction-energy-threshold",
            traits.reproduction_energy_threshold,
        ),
        ("b3.config.trait.offspring-energy", traits.offspring_energy),
        ("b3.config.trait.maximum-age", traits.maximum_age),
        ("b3.config.tradeoff.cost-denominator", tradeoffs.cost_denominator),
        ("b3.config.tradeoff.max-speed-cost", tradeoffs.max_speed_cost),
        ("b3.config.tradeoff.sensory-range-cost", tradeoffs.sensory_range_cost),
        (
            "b3.config.tradeoff.sensory-accuracy-cost",
            tradeoffs.sensory_accuracy_cost,
        ),
        (
            "b3.config.tradeoff.sensory-accuracy-baseline",
            tradeoffs.sensory_accuracy_baseline,
        ),
        (
            "b3.config.tradeoff.max-intake-rate-cost",
            tradeoffs.max_intake_rate_cost,
        ),
        (
            "b3.config.tradeoff.assimilation-efficiency-cost",
            tradeoffs.assimilation_efficiency_cost,
        ),
        (
            "b3.config.tradeoff.assimilation-efficiency-baseline",
            tradeoffs.assimilation_efficiency_baseline,
        ),
        (
            "b3.config.tradeoff.attack-strength-cost",
            tradeoffs.attack_strength_cost,
        ),
        ("b3.config.tradeoff.defense-cost", tradeoffs.defense_cost),
        ("b3.config.investment-scale.denominator", investment.denominator),
        (
            "b3.config.investment-scale.type-a-numerator",
            investment.type_a_numerator,
        ),
        (
            "b3.config.investment-scale.type-b-numerator",
            investment.type_b_numerator,
        ),
        ("b3.config.mutation-probability-ppm", config.mutation_probability_ppm),
        ("b3.config.mutation-max-change", config.mutation_max_change),
        (
            "b3.config.recombination-probability-ppm",
            config.recombination_probability_ppm,
        ),
        ("b3.config.resource-generation-amount", config.resource_generation_amount),
        ("b3.config.resource-deposits-per-step", config.resource_deposits_per_step),
        ("b3.config.decomposition-amount", config.decomposition_amount),
        ("b3.config.resource-request-amount", config.resource_request_amount),
        ("b3.config.metabolic-mass-exponent", config.metabolic_mass_exponent),
        ("b3.config.locomotion-mass-exponent", config.locomotion_mass_exponent),
        (
            "b3.config.locomotion-distance-exponent",
            config.locomotion_distance_exponent,
        ),
        ("b3.config.growth-energy-per-mass", config.growth_energy_per_mass),
        ("b3.config.predation-radius", config.predation_radius),
        (
            "b3.config.predation-consumption-percent",
            config.predation_consumption_percent,
        ),
        ("b3.config.mating-radius", config.mating_radius),
        ("b3.config.newborn-mass-numerator", config.newborn_mass_numerator),
        ("b3.config.newborn-mass-denominator", config.newborn_mass_denominator),
        ("b3.inheritance", "ordinary-reference-sexual"),
        ("b3.mating-types", "ordinary-reference"),
        (
            "b3.renewable-generation.expected-event-count",
            B3_RESOURCE_DEPOSITS_PER_STEP * B3_MAX_STEPS,
        ),
        (
            "b3.renewable-generation.expected-total-units",
            B3_RESOURCE_DEPOSITS_PER_STEP
            * B3_MAX_STEPS
            * B3_RESOURCE_GENERATION_AMOUNT,
        ),
        ("b3.low-max-speed", B3_LOW_MAX_SPEED),
        ("b3.high-max-speed", B3_HIGH_MAX_SPEED),
    )


def _scenario_identity(radius: int | None) -> str | None:
    return B3_VALIDATED_SCENARIO_ID if radius == B3_COMPACT_PATCH_RADIUS else None


def _changes(
    before: B3ValuePairs,
    after: B3ValuePairs,
) -> tuple[B3SemanticChange, ...]:
    before_mapping = dict(before)
    after_mapping = dict(after)
    if before_mapping.keys() != after_mapping.keys():
        raise ValueError("B3 semantic diff requires matching scientific slot IDs.")
    return tuple(
        B3SemanticChange(
            slot_id=slot_id,
            before=before_mapping[slot_id],
            after=after_mapping[slot_id],
        )
        for slot_id in before_mapping
        if before_mapping[slot_id] != after_mapping[slot_id]
    )


def _validate_revision_alignment(revision: B3StudyRevision) -> None:
    radius = revision.intent.treatment_radius
    if revision.manifest.explicit_value(B3_TREATMENT_RADIUS_SLOT) != radius:
        raise ValueError("Stored B3 intent does not match stored manifest.")
    if revision.evidence_plan.requested != B3_REQUIRED_EVIDENCE_IDS:
        raise ValueError("Stored B3 revision lost required B3 evidence intent.")


def _validate_runs(revision: B3StudyRevision) -> None:
    if type(revision.runs) is not tuple:
        raise TypeError("runs must be a tuple.")
    seen: set[str] = set()
    for run in revision.runs:
        if not isinstance(run, WorkbenchRunProvenance):
            raise TypeError("runs must contain WorkbenchRunProvenance values.")
        _validate_run_for_revision(revision, run)
        if run.run_id in seen:
            raise ValueError(f"Duplicate run ID {run.run_id!r}.")
        seen.add(run.run_id)


def _validate_run_for_revision(
    revision: B3StudyRevision,
    provenance: WorkbenchRunProvenance,
) -> None:
    if provenance.study_revision_id != revision.revision_id:
        raise ValueError("Run provenance references a different study revision.")
    if provenance.manifest_digest != revision.manifest.digest:
        raise ValueError("Run provenance references a different B3 manifest.")
    if provenance.evidence_ids != revision.evidence_plan.requested:
        raise ValueError("Run provenance references a different B3 evidence plan.")


def _installed_engine_version() -> str:
    try:
        return metadata.version(ENGINE_DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return "source-tree-uninstalled"


def _require_current_compatibility(manifest: B3CuratedManifest) -> None:
    current = _installed_engine_version()
    if manifest.engine_version != current:
        raise IncompatibleManifestError(
            "Persisted B3 manifest requires "
            f"{manifest.engine_distribution}=={manifest.engine_version}; "
            f"current version is {current}."
        )


def _validate_manifest_identity(manifest: B3CuratedManifest) -> None:
    expected = (
        B3_RECIPE_ID,
        B3_RECIPE_VERSION,
        B3_COMPILER_ID,
        B3_COMPILER_VERSION,
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
            "Persisted B3 recipe/compiler identity is not supported."
        )


def _validate_pairs(values: B3ValuePairs, *, name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{name} must be a tuple.")
    keys: list[str] = []
    for index, item in enumerate(values):
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(f"{name}[{index}] must be a two-item tuple.")
        key, value = item
        if type(key) is not str or not key:
            raise TypeError(f"{name}[{index}] slot ID must be a non-empty string.")
        if type(value) not in (str, int, float, bool):
            raise TypeError(f"{name}[{index}] contains an unsupported manifest value.")
        if type(value) is float and (
            value != value or value in (float("inf"), -float("inf"))
        ):
            raise ValueError(f"{name}[{index}] float must be finite.")
        keys.append(key)
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} contains duplicate slot IDs.")


def _value_for(values: B3ValuePairs, slot_id: str) -> B3ManifestScalar:
    for key, value in values:
        if key == slot_id:
            return value
    raise KeyError(slot_id)


def _decode_pairs(mapping: dict[str, object], key: str) -> B3ValuePairs:
    raw = _required_list(mapping, key)
    pairs: list[tuple[str, B3ManifestScalar]] = []
    for index, item in enumerate(raw):
        if type(item) is not list or len(item) != 2:
            raise TypeError(f"{key}[{index}] must be a two-item JSON array.")
        slot_id, value = item
        if type(slot_id) is not str or not slot_id:
            raise TypeError(f"{key}[{index}][0] must be a non-empty string.")
        if type(value) not in (str, int, float, bool):
            raise TypeError(f"{key}[{index}][1] has an unsupported value.")
        pairs.append((slot_id, cast(B3ManifestScalar, value)))
    return tuple(pairs)


def _json_object(value: str, *, name: str) -> dict[str, object]:
    if type(value) is not str:
        raise TypeError(f"{name} JSON must be a string.")
    decoded = json.loads(value)
    if type(decoded) is not dict:
        raise ValueError(f"{name} JSON must encode an object.")
    return cast(dict[str, object], decoded)


def _required_mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping.get(key)
    if type(value) is not dict:
        raise TypeError(f"{key} must be a JSON object.")
    return cast(dict[str, object], value)


def _required_list(mapping: dict[str, object], key: str) -> list[object]:
    value = mapping.get(key)
    if type(value) is not list:
        raise TypeError(f"{key} must be a JSON array.")
    return cast(list[object], value)


def _required_str(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string.")
    return value


def _optional_str(mapping: dict[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not str or not value:
        raise TypeError(f"{key} must be a non-empty string or null.")
    return value


def _required_int(mapping: dict[str, object], key: str) -> int:
    value = mapping.get(key)
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer.")
    return value


def _optional_int(mapping: dict[str, object], key: str) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{key} must be an integer or null.")
    return value


def _strings(values: list[object], name: str) -> list[str]:
    result: list[str] = []
    for index, value in enumerate(values):
        if type(value) is not str or not value:
            raise TypeError(f"{name}[{index}] must be a non-empty string.")
        result.append(value)
    return result


def _exact_int(value: B3ManifestScalar, slot_id: str) -> int:
    if type(value) is not int:
        raise IncompatibleManifestError(f"{slot_id} must contain an exact integer.")
    return value


def _integer_text(values: tuple[int, ...]) -> str:
    return ",".join(str(value) for value in values)


def _coordinate_text(values: tuple[tuple[int, int], ...]) -> str:
    return ";".join(f"{x},{y}" for x, y in values)


def _require_nonempty(value: str, name: str) -> None:
    if type(value) is not str or not value.strip():
        raise TypeError(f"{name} must be a non-empty string.")


def _run_to_mapping(run: WorkbenchRunProvenance) -> dict[str, object]:
    return {
        "evidence_ids": list(run.evidence_ids),
        "evidence_references": list(run.evidence_references),
        "manifest_digest": run.manifest_digest,
        "result_references": list(run.result_references),
        "run_id": run.run_id,
        "study_revision_id": run.study_revision_id,
    }


def _run_from_mapping(value: object, *, index: int) -> WorkbenchRunProvenance:
    if type(value) is not dict:
        raise TypeError(f"runs[{index}] must be a JSON object.")
    mapping = cast(dict[str, object], value)
    return WorkbenchRunProvenance(
        run_id=_required_str(mapping, "run_id"),
        study_revision_id=_required_str(mapping, "study_revision_id"),
        manifest_digest=_required_str(mapping, "manifest_digest"),
        evidence_ids=tuple(
            _strings(
                _required_list(mapping, "evidence_ids"),
                f"runs[{index}].evidence_ids",
            )
        ),
        evidence_references=tuple(
            _strings(
                _required_list(mapping, "evidence_references"),
                f"runs[{index}].evidence_references",
            )
        ),
        result_references=tuple(
            _strings(
                _required_list(mapping, "result_references"),
                f"runs[{index}].result_references",
            )
        ),
    )


__all__ = [
    "B3_COMPILER_ID",
    "B3_COMPILER_VERSION",
    "B3_EVENT_EVIDENCE_ID",
    "B3_GENETIC_EVIDENCE_ID",
    "B3_INDIVIDUAL_TRAIT_EVIDENCE_ID",
    "B3_PEDIGREE_EVIDENCE_ID",
    "B3_POPULATION_EVIDENCE_ID",
    "B3_RECIPE_ID",
    "B3_RECIPE_VERSION",
    "B3_REQUIRED_EVIDENCE_IDS",
    "B3_SCENARIO_ORIGIN_ID",
    "B3_SPATIAL_EVIDENCE_ID",
    "B3_STUDY_FORMAT_ID",
    "B3_STUDY_FORMAT_VERSION",
    "B3_TREATMENT_RADIUS_SLOT",
    "B3_VALIDATED_SCENARIO_ID",
    "B3CuratedDiff",
    "B3CuratedIntent",
    "B3CuratedManifest",
    "B3CuratedRunResult",
    "B3EvidencePlan",
    "B3MatchedRunArtifacts",
    "B3MatchedSpecifications",
    "B3ScenarioIdentityChange",
    "B3SemanticChange",
    "B3SingleRunArtifacts",
    "B3StudyRevision",
    "CompiledB3CuratedStudy",
    "assess_b3_readiness",
    "compile_b3_curated",
    "create_b3_study_revision",
    "diff_b3_study_revisions",
    "fork_b3_study_revision",
    "resolve_b3_curated",
    "run_b3_study_revision",
]
