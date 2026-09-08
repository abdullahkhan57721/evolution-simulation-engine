"""Native Simulation authoring over existing concrete Workbench contracts."""

# PySide's Property setter decorator is a runtime descriptor but its stubs currently
# report paired getter/setter declarations as a redeclaration.
# pyright: reportRedeclaration=false

from __future__ import annotations

import uuid
from typing import cast

import attrs
from PySide6.QtCore import Property, QObject, Signal, Slot

from evo_engine.desktop.artifacts import ConcreteWorkbenchArtifact
from evo_engine.desktop.controllers.reference import ReferenceStudyController
from evo_engine.desktop.models.authoring import (
    MeaningItem,
    MeaningListModel,
    SemanticDiffItem,
    SemanticDiffModel,
)
from evo_engine.workbench import (
    B3CuratedDiff,
    B3StudyRevision,
    ControlledLocomotionIntent,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
    resolve_controlled_locomotion,
)
from evo_engine.workbench.controlled_locomotion import (
    SUPPORTED_MAX_SPEED_MAXIMUM,
    SUPPORTED_MAX_SPEED_MINIMUM,
    SUPPORTED_RESOURCE_GEOGRAPHIES,
)
from evo_engine.workbench.simulation_authoring import (
    controlled_draft_readiness,
    save_controlled_child,
    semantic_slot_label,
    simulation_semantic_diff,
)

_CONTROLLED_DYNAMIC_DERIVED = (
    "controlled-locomotion.initial-focal-max-speed",
    "controlled-locomotion.resource-deposit-layout",
)
_CONTROLLED_FROZEN = (
    "controlled-locomotion.inherited-traits",
    "controlled-locomotion.genetics",
    "controlled-locomotion.inheritance",
    "controlled-locomotion.mutation",
    "controlled-locomotion.sensing",
    "controlled-locomotion.movement-targeting",
    "controlled-locomotion.horizon-step-index",
    "controlled-locomotion.locomotion-cost-coefficient",
    "controlled-locomotion.reproduction-minimum-energy",
    "controlled-locomotion.reproduction-energy-investment",
    "controlled-locomotion.mate-search",
    "controlled-locomotion.predation",
    "controlled-locomotion.metabolism",
    "controlled-locomotion.growth",
    "controlled-locomotion.aging",
    "controlled-locomotion.renewable-resource-generation",
)
_REFERENCE_DYNAMIC_DERIVED = (
    "reference-ecology.resolved-resource-placement",
    "reference-ecology.resolved-exploration-pattern",
    "reference-ecology.effective-mutation-probability-ppm",
    "reference-ecology.effective-mutation-max-change",
)
_REFERENCE_FROZEN = (
    "reference-ecology.fixed-reference-config",
    "reference-ecology.genome-structure",
    "reference-ecology.genetic-expression",
    "reference-ecology.inheritance",
    "reference-ecology.development",
    "reference-ecology.reproduction",
    "reference-ecology.food-targeting",
    "reference-ecology.mate-targeting",
)
_B3_SUMMARY = (
    ("Study design", "b3.study-design"),
    ("Control environment", "b3.control-resource-geography"),
    ("Treatment environment", "b3.treatment-resource-geography"),
    ("Treatment integrity", "b3.treatment-integrity"),
    ("Focal trait", "b3.focal-trait"),
    ("Focal trait semantics", "b3.focal-trait-semantics"),
    ("Founder variants", "b3.founder-variant-values"),
    ("Founder construction", "b3.founder-construction"),
    ("Run horizon", "b3.config.max-steps"),
    ("Mutation probability (ppm)", "b3.config.mutation-probability-ppm"),
    ("Mutation maximum change", "b3.config.mutation-max-change"),
    ("Inheritance", "b3.inheritance"),
    ("Mating system", "b3.mating-types"),
    ("Counterbalance design", "b3.counterbalance-design"),
)


class SimulationAuthoringController(QObject):
    """Own native Simulation draft state without becoming a scientific schema."""

    activeChanged = Signal()
    draftChanged = Signal()
    scientificDraftChanged = Signal()
    revisionCommitted = Signal(object)
    statusChanged = Signal()

    def __init__(
        self, reference: ReferenceStudyController, parent: QObject | None = None
    ):
        super().__init__(parent)
        self._reference = reference
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._controlled_draft: ControlledLocomotionIntent | None = None
        self._diff_parent: ConcreteWorkbenchArtifact | None = None
        self._selected = MeaningListModel()
        self._derived = MeaningListModel()
        self._frozen = MeaningListModel()
        self._diff = SemanticDiffModel()
        self._status = "Simulation authoring is inactive."
        reference.draftChanged.connect(self.refresh_reference_view)

    @Property(bool, notify=activeChanged)
    def active(self) -> bool:
        return self._artifact is not None

    @Property(QObject, constant=True)
    def selectedMeaningModel(self) -> QObject:  # noqa: N802
        return self._selected

    @Property(QObject, constant=True)
    def derivedMeaningModel(self) -> QObject:  # noqa: N802
        return self._derived

    @Property(QObject, constant=True)
    def frozenMeaningModel(self) -> QObject:  # noqa: N802
        return self._frozen

    @Property(QObject, constant=True)
    def semanticDiffModel(self) -> QObject:  # noqa: N802
        return self._diff

    @Property(bool, notify=draftChanged)
    def hasSemanticDiff(self) -> bool:  # noqa: N802
        return bool(self._diff.items())

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(int, constant=True)
    def controlledMinimumMaxSpeed(self) -> int:  # noqa: N802
        return SUPPORTED_MAX_SPEED_MINIMUM

    @Property(int, constant=True)
    def controlledMaximumMaxSpeed(self) -> int:  # noqa: N802
        return SUPPORTED_MAX_SPEED_MAXIMUM

    @Property(int, notify=draftChanged)
    def controlledMaxSpeed(self) -> int:  # noqa: N802
        if self._controlled_draft is None or self._controlled_draft.max_speed is None:
            return SUPPORTED_MAX_SPEED_MINIMUM
        return self._controlled_draft.max_speed

    @controlledMaxSpeed.setter
    def controlledMaxSpeed(self, value: int) -> None:  # noqa: N802
        self.set_controlled_max_speed(value)

    @Property(str, notify=draftChanged)
    def controlledResourceGeography(self) -> str:  # noqa: N802
        if self._controlled_draft is None:
            return ""
        return self._controlled_draft.resource_geography or ""

    @controlledResourceGeography.setter
    def controlledResourceGeography(self, value: str) -> None:  # noqa: N802
        self.set_controlled_resource_geography(value)

    @Property(int, notify=draftChanged)
    def controlledSeed(self) -> int:  # noqa: N802
        if self._controlled_draft is None or self._controlled_draft.seed is None:
            return 0
        return self._controlled_draft.seed

    @controlledSeed.setter
    def controlledSeed(self, value: int) -> None:  # noqa: N802
        self.set_controlled_seed(value)

    @Property(bool, notify=draftChanged)
    def controlledDraftDirty(self) -> bool:  # noqa: N802
        return self.is_controlled_draft_dirty()

    @Property(bool, notify=draftChanged)
    def controlledDraftReady(self) -> bool:  # noqa: N802
        if (
            not isinstance(self._artifact, StudyRevision)
            or self._controlled_draft is None
        ):
            return False
        return (
            controlled_draft_readiness(self._artifact, self._controlled_draft).state
            == "ready"
        )

    @Property(str, notify=draftChanged)
    def controlledReadinessMessage(self) -> str:  # noqa: N802
        if (
            not isinstance(self._artifact, StudyRevision)
            or self._controlled_draft is None
        ):
            return ""
        readiness = controlled_draft_readiness(self._artifact, self._controlled_draft)
        if not readiness.diagnostics:
            return "Ready"
        return " · ".join(item.message for item in readiness.diagnostics)

    @Property(str, constant=True)
    def controlledGeographyPrimary(self) -> str:  # noqa: N802
        return "local_resource"

    @Property(str, constant=True)
    def controlledGeographySecondary(self) -> str:  # noqa: N802
        return "separated_corridor"

    @Property(str, notify=activeChanged)
    def readOnlyMessage(self) -> str:  # noqa: N802
        artifact = self._artifact
        if isinstance(artifact, MaxSpeedSweepDefinition):
            return (
                "Maximum speed and replicate seed are owned by the E3 Experiment "
                "definition. Base resource geography remains read-only here."
            )
        if isinstance(artifact, EnvironmentSelectionComparisonDefinition):
            return (
                "Resource geography is the E4 Experiment factor. Control/treatment, "
                "standing composition, and counterbalance remain read-only here."
            )
        if isinstance(artifact, B3StudyRevision):
            return (
                "B3 is curated and read-only. The only supported Simulation change is "
                "the existing radius-sensitivity scientific fork."
            )
        return ""

    def activate_artifact(
        self,
        artifact: ConcreteWorkbenchArtifact,
        *,
        diff_parent: ConcreteWorkbenchArtifact | None = None,
    ) -> None:
        """Bind exact application ownership and initialize only transient draft state."""
        self._artifact = artifact
        self._diff_parent = diff_parent
        self._controlled_draft = (
            artifact.intent if isinstance(artifact, StudyRevision) else None
        )
        self._refresh_models()
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status(
            "Simulation authoring follows the active exact Workbench artifact."
        )

    def clear(self) -> None:
        self._artifact = None
        self._controlled_draft = None
        self._diff_parent = None
        self._selected.set_items(())
        self._derived.set_items(())
        self._frozen.set_items(())
        self._diff.set_items(())
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Simulation authoring is inactive.")

    def is_controlled_draft_dirty(self) -> bool:
        return (
            isinstance(self._artifact, StudyRevision)
            and self._controlled_draft is not None
            and self._controlled_draft != self._artifact.intent
        )

    def set_controlled_max_speed(self, value: int) -> None:
        if self._controlled_draft is None or type(value) is not int:
            return
        self._replace_controlled(max_speed=value)

    def set_controlled_resource_geography(self, value: str) -> None:
        if (
            self._controlled_draft is None
            or type(value) is not str
            or value not in SUPPORTED_RESOURCE_GEOGRAPHIES
        ):
            return
        self._replace_controlled(resource_geography=value)

    def set_controlled_seed(self, value: int) -> None:
        if self._controlled_draft is None or type(value) is not int:
            return
        self._replace_controlled(seed=value)

    @Slot(result=bool)
    def saveControlledChildRevision(self) -> bool:  # noqa: N802
        if (
            not isinstance(self._artifact, StudyRevision)
            or self._controlled_draft is None
        ):
            return False
        if not self.is_controlled_draft_dirty():
            self._set_status("No controlled Simulation draft changes to save.")
            return False
        try:
            child = save_controlled_child(
                self._artifact,
                draft=self._controlled_draft,
                revision_id=f"controlled-{uuid.uuid4().hex[:10]}",
            )
        except (TypeError, ValueError) as exc:
            self._set_status(f"Simulation revision is not ready: {exc}")
            return False
        self.revisionCommitted.emit(child)
        return True

    @Slot()
    def refresh_reference_view(self) -> None:
        if isinstance(self._artifact, ReferenceStudyRevision):
            self._refresh_models()
            self.draftChanged.emit()

    def _replace_controlled(self, **changes: object) -> None:
        assert self._controlled_draft is not None
        candidate = attrs.evolve(self._controlled_draft, **changes)
        if candidate == self._controlled_draft:
            return
        self._controlled_draft = candidate
        self._refresh_models()
        self.draftChanged.emit()
        self.scientificDraftChanged.emit()
        self._set_status("Unsaved controlled Simulation draft changed.")

    def _refresh_models(self) -> None:
        artifact = self._artifact
        if isinstance(artifact, StudyRevision):
            self._refresh_controlled_meaning(artifact)
        elif isinstance(artifact, ReferenceStudyRevision):
            self._refresh_reference_meaning(artifact)
        elif isinstance(artifact, B3StudyRevision):
            self._refresh_b3_meaning(artifact)
        else:
            self._selected.set_items(())
            self._derived.set_items(())
            self._frozen.set_items(())
        self._refresh_diff()

    def _refresh_controlled_meaning(self, revision: StudyRevision) -> None:
        draft = self._controlled_draft or revision.intent
        readiness = controlled_draft_readiness(revision, draft)
        manifest = (
            resolve_controlled_locomotion(draft, revision.evidence_plan)
            if readiness.state == "ready"
            else revision.manifest
        )
        self._selected.set_items(_pairs(manifest.explicit_values))
        self._derived.set_items(
            _selected_derived(manifest, _CONTROLLED_DYNAMIC_DERIVED)
        )
        self._frozen.set_items(_selected_derived(manifest, _CONTROLLED_FROZEN))

    def _refresh_reference_meaning(self, revision: ReferenceStudyRevision) -> None:
        manifest = self._reference.preview_manifest() or revision.manifest
        self._selected.set_items(_pairs(manifest.explicit_values))
        self._derived.set_items(_selected_derived(manifest, _REFERENCE_DYNAMIC_DERIVED))
        self._frozen.set_items(_selected_derived(manifest, _REFERENCE_FROZEN))

    def _refresh_b3_meaning(self, revision: B3StudyRevision) -> None:
        self._selected.set_items(())
        values: list[MeaningItem] = []
        for label, slot_id in _B3_SUMMARY:
            try:
                value = revision.manifest.derived_value(slot_id)
            except KeyError:
                continue
            values.append(MeaningItem(label=label, value=_format_value(value)))
        self._derived.set_items(values)
        self._frozen.set_items(())

    def _refresh_diff(self) -> None:
        current = self._artifact
        parent = self._diff_parent
        if not isinstance(
            current, (StudyRevision, ReferenceStudyRevision, B3StudyRevision)
        ) or not isinstance(
            parent, (StudyRevision, ReferenceStudyRevision, B3StudyRevision)
        ):
            self._diff.set_items(())
            return
        if current.parent_revision_id != getattr(parent, "revision_id", None):
            self._diff.set_items(())
            return
        try:
            diff = simulation_semantic_diff(
                cast(StudyRevision | ReferenceStudyRevision | B3StudyRevision, parent),
                cast(StudyRevision | ReferenceStudyRevision | B3StudyRevision, current),
            )
        except TypeError:
            self._diff.set_items(())
            return
        items = [
            SemanticDiffItem(
                group="Explicit changes",
                label=semantic_slot_label(change.slot_id),
                before=_format_value(change.before),
                after=_format_value(change.after),
            )
            for change in diff.explicit_changes
        ]
        items.extend(
            SemanticDiffItem(
                group="Derived changes",
                label=semantic_slot_label(change.slot_id),
                before=_format_value(change.before),
                after=_format_value(change.after),
            )
            for change in diff.derived_changes
        )
        if (
            isinstance(diff, B3CuratedDiff)
            and diff.scenario_identity_change is not None
        ):
            items.append(
                SemanticDiffItem(
                    group="Identity changes",
                    label="Validated scenario identity",
                    before=_format_value(diff.scenario_identity_change.before),
                    after=_format_value(diff.scenario_identity_change.after),
                    tone="warning"
                    if diff.scenario_identity_change.after is None
                    else "neutral",
                )
            )
        self._diff.set_items(items)

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _pairs(values: tuple[tuple[str, object], ...]) -> tuple[MeaningItem, ...]:
    return tuple(
        MeaningItem(label=semantic_slot_label(slot_id), value=_format_value(value))
        for slot_id, value in values
    )


def _selected_derived(
    manifest: object, slot_ids: tuple[str, ...]
) -> tuple[MeaningItem, ...]:
    result: list[MeaningItem] = []
    for slot_id in slot_ids:
        try:
            value = manifest.derived_value(slot_id)  # type: ignore[attr-defined]
        except KeyError:
            continue
        result.append(
            MeaningItem(label=semantic_slot_label(slot_id), value=_format_value(value))
        )
    return tuple(result)


def _format_value(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "On" if value else "Off"
    return str(value).replace("_", " ")


__all__ = ["SimulationAuthoringController"]
