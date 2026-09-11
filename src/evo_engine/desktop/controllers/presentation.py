"""Native Presentation controller over authoritative Workbench world frames."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Property, QObject, Signal, Slot

from evo_engine.desktop.controllers.application import ApplicationController
from evo_engine.desktop.models import (
    WorldCarcassModel,
    WorldOrganismModel,
    WorldResourceModel,
    WorldTrailModel,
)
from evo_engine.presentation.workbench import (
    build_b3_workbench_world_presentation,
    build_reference_workbench_world_presentation,
)
from evo_engine.presentation.world import (
    OrganismPrimitive,
    WorldPresentationFrame,
    available_step_indices,
)
from evo_engine.workbench import (
    B3CuratedRunResult,
    B3StudyRevision,
    ReferenceRunResult,
    ReferenceStudyRevision,
)
from evo_engine.workbench.b3_curated import B3_VALIDATED_SCENARIO_ID
from evo_engine.workbench.results import (
    inspect_b3_results,
    inspect_reference_study_results,
)
from evo_engine.workbench.support import analysis_availability_diagnostic

_PLAYBACK_SPEEDS = (0.5, 1.0, 2.0, 4.0)
_MATCHED_LANGUAGE = (
    "Control and treatment are matched/blocked by confirmation seed and committed "
    "step. Matching does not imply RNG lockstep after biological divergence."
)


class PresentationController(QObject):
    """Project exact result-owned world frames into narrow Qt presentation models."""

    changed = Signal()
    viewChanged = Signal()

    def __init__(
        self,
        application: ApplicationController,
        parent: QObject | None = None,
    ) -> None:
        if not isinstance(application, ApplicationController):
            raise TypeError("application must be an ApplicationController.")
        super().__init__(parent or application)
        self._application = application
        self._artifact: ReferenceStudyRevision | B3StudyRevision | None = None
        self._result: ReferenceRunResult | B3CuratedRunResult | None = None
        self._owner = ""
        self._family = ""
        self._available = False
        self._message = "Run a supported Study before opening Presentation."
        self._remediation = ""
        self._steps: tuple[int, ...] = ()
        self._position = 0
        self._world_width = 0
        self._world_height = 0
        self._legend_label = ""
        self._legend_lower = 0
        self._legend_upper = 0
        self._selected_id: int | None = None
        self._control_selected_id: int | None = None
        self._treatment_selected_id: int | None = None
        self._inspector_title = "No organism selected"
        self._inspector_body = "Select an organism to inspect committed values."
        self._control_inspector_title = "No organism selected"
        self._control_inspector_body = "Select a control organism."
        self._treatment_inspector_title = "No organism selected"
        self._treatment_inspector_body = "Select a treatment organism."
        self._b3_seeds: tuple[int, ...] = ()
        self._b3_seed_position = 0
        self._playing = False
        self._playback_speed = 1.0
        self._labels_visible = True
        self._trails_visible = True
        self._focus_mode = False
        self._transition_animated = False

        self._organisms = WorldOrganismModel()
        self._resources = WorldResourceModel()
        self._carcasses = WorldCarcassModel()
        self._trails = WorldTrailModel()
        self._control_organisms = WorldOrganismModel()
        self._control_resources = WorldResourceModel()
        self._control_carcasses = WorldCarcassModel()
        self._control_trails = WorldTrailModel()
        self._treatment_organisms = WorldOrganismModel()
        self._treatment_resources = WorldResourceModel()
        self._treatment_carcasses = WorldCarcassModel()
        self._treatment_trails = WorldTrailModel()

        application.presentationChanged.connect(self._sync_from_application)
        application.resultChanged.connect(self._sync_from_application)
        application.artifactChanged.connect(self._sync_from_application)
        self._sync_from_application()

    @Property(str, notify=changed)
    def family(self) -> str:
        return self._family

    @Property(bool, notify=changed)
    def available(self) -> bool:
        return self._available

    @Property(str, notify=changed)
    def message(self) -> str:
        return self._message

    @Property(str, notify=changed)
    def remediation(self) -> str:
        return self._remediation

    @Property(int, notify=changed)
    def worldWidth(self) -> int:  # noqa: N802
        return self._world_width

    @Property(int, notify=changed)
    def worldHeight(self) -> int:  # noqa: N802
        return self._world_height

    @Property(int, notify=changed)
    def committedStep(self) -> int:  # noqa: N802
        return self._steps[self._position] if self._steps else 0

    @Property(int, notify=changed)
    def stepPosition(self) -> int:  # noqa: N802
        return self._position

    @Property(int, notify=changed)
    def stepCount(self) -> int:  # noqa: N802
        return len(self._steps)

    @Property(bool, notify=changed)
    def canPrevious(self) -> bool:  # noqa: N802
        return self._available and self._position > 0

    @Property(bool, notify=changed)
    def canNext(self) -> bool:  # noqa: N802
        return self._available and self._position + 1 < len(self._steps)

    @Property(bool, notify=viewChanged)
    def playing(self) -> bool:
        return self._playing

    @Property(float, notify=viewChanged)
    def playbackSpeed(self) -> float:  # noqa: N802
        return self._playback_speed

    @Property(int, notify=viewChanged)
    def playbackIntervalMs(self) -> int:  # noqa: N802
        return round(800 / self._playback_speed)

    @Property(bool, notify=viewChanged)
    def labelsVisible(self) -> bool:  # noqa: N802
        return self._labels_visible

    @Property(bool, notify=viewChanged)
    def trailsVisible(self) -> bool:  # noqa: N802
        return self._trails_visible

    @Property(bool, notify=viewChanged)
    def focusMode(self) -> bool:  # noqa: N802
        return self._focus_mode

    @Property(bool, notify=viewChanged)
    def transitionAnimated(self) -> bool:  # noqa: N802
        return self._transition_animated

    @Property(int, notify=viewChanged)
    def transitionDurationMs(self) -> int:  # noqa: N802
        return max(80, round(520 / self._playback_speed))

    @Property(str, notify=changed)
    def legendLabel(self) -> str:  # noqa: N802
        return self._legend_label

    @Property(int, notify=changed)
    def legendLower(self) -> int:  # noqa: N802
        return self._legend_lower

    @Property(int, notify=changed)
    def legendUpper(self) -> int:  # noqa: N802
        return self._legend_upper

    @Property(str, notify=changed)
    def inspectorTitle(self) -> str:  # noqa: N802
        return self._inspector_title

    @Property(str, notify=changed)
    def inspectorBody(self) -> str:  # noqa: N802
        return self._inspector_body

    @Property(str, notify=changed)
    def controlInspectorTitle(self) -> str:  # noqa: N802
        return self._control_inspector_title

    @Property(str, notify=changed)
    def controlInspectorBody(self) -> str:  # noqa: N802
        return self._control_inspector_body

    @Property(str, notify=changed)
    def treatmentInspectorTitle(self) -> str:  # noqa: N802
        return self._treatment_inspector_title

    @Property(str, notify=changed)
    def treatmentInspectorBody(self) -> str:  # noqa: N802
        return self._treatment_inspector_body

    @Property(int, notify=changed)
    def b3Seed(self) -> int:  # noqa: N802
        return self._b3_seeds[self._b3_seed_position] if self._b3_seeds else 0

    @Property(int, notify=changed)
    def b3SeedPosition(self) -> int:  # noqa: N802
        return self._b3_seed_position

    @Property(int, notify=changed)
    def b3SeedCount(self) -> int:  # noqa: N802
        return len(self._b3_seeds)

    @Property(bool, notify=changed)
    def canPreviousSeed(self) -> bool:  # noqa: N802
        return self._b3_seed_position > 0

    @Property(bool, notify=changed)
    def canNextSeed(self) -> bool:  # noqa: N802
        return self._b3_seed_position + 1 < len(self._b3_seeds)

    @Property(str, constant=True)
    def matchedLanguage(self) -> str:  # noqa: N802
        return _MATCHED_LANGUAGE

    @Property(QObject, constant=True)
    def organismModel(self) -> QObject:  # noqa: N802
        return self._organisms

    @Property(QObject, constant=True)
    def resourceModel(self) -> QObject:  # noqa: N802
        return self._resources

    @Property(QObject, constant=True)
    def carcassModel(self) -> QObject:  # noqa: N802
        return self._carcasses

    @Property(QObject, constant=True)
    def trailModel(self) -> QObject:  # noqa: N802
        return self._trails

    @Property(QObject, constant=True)
    def controlOrganismModel(self) -> QObject:  # noqa: N802
        return self._control_organisms

    @Property(QObject, constant=True)
    def controlResourceModel(self) -> QObject:  # noqa: N802
        return self._control_resources

    @Property(QObject, constant=True)
    def controlCarcassModel(self) -> QObject:  # noqa: N802
        return self._control_carcasses

    @Property(QObject, constant=True)
    def controlTrailModel(self) -> QObject:  # noqa: N802
        return self._control_trails

    @Property(QObject, constant=True)
    def treatmentOrganismModel(self) -> QObject:  # noqa: N802
        return self._treatment_organisms

    @Property(QObject, constant=True)
    def treatmentResourceModel(self) -> QObject:  # noqa: N802
        return self._treatment_resources

    @Property(QObject, constant=True)
    def treatmentCarcassModel(self) -> QObject:  # noqa: N802
        return self._treatment_carcasses

    @Property(QObject, constant=True)
    def treatmentTrailModel(self) -> QObject:  # noqa: N802
        return self._treatment_trails

    @Slot(int)
    def seekStepPosition(self, position: int) -> None:  # noqa: N802
        if not self._available or not 0 <= position < len(self._steps):
            return
        self._set_position(position, animate=False)

    @Slot()
    def previousStep(self) -> None:  # noqa: N802
        if self._available and self._position > 0:
            self._set_position(self._position - 1, animate=True)

    @Slot()
    def nextStep(self) -> None:  # noqa: N802
        if self._available and self._position + 1 < len(self._steps):
            self._set_position(self._position + 1, animate=True)

    @Slot()
    def togglePlayback(self) -> None:  # noqa: N802
        if not self._available:
            return
        if self._playing:
            self._playing = False
        else:
            if self._position + 1 >= len(self._steps) and self._steps:
                self._set_position(0, animate=False)
            self._playing = True
        self.viewChanged.emit()

    @Slot()
    def advancePlayback(self) -> None:  # noqa: N802
        if not self._playing:
            return
        if self._position + 1 >= len(self._steps):
            self._playing = False
            self.viewChanged.emit()
            return
        self._set_position(self._position + 1, animate=True)

    @Slot(float)
    def setPlaybackSpeed(self, value: float) -> None:  # noqa: N802
        resolved = float(value)
        if resolved not in _PLAYBACK_SPEEDS or resolved == self._playback_speed:
            return
        self._playback_speed = resolved
        self.viewChanged.emit()

    @Slot()
    def toggleLabels(self) -> None:  # noqa: N802
        self._labels_visible = not self._labels_visible
        self.viewChanged.emit()

    @Slot()
    def toggleTrails(self) -> None:  # noqa: N802
        self._trails_visible = not self._trails_visible
        self.viewChanged.emit()

    @Slot()
    def toggleFocusMode(self) -> None:  # noqa: N802
        self._focus_mode = not self._focus_mode
        self.viewChanged.emit()

    @Slot(int)
    def selectOrganism(self, organism_id: int) -> None:  # noqa: N802
        if self._family != "reference" or not self._available:
            return
        self._selected_id = organism_id
        self._rebuild_current(preserve_rows=True, animate=False)

    @Slot(int)
    def selectControlOrganism(self, organism_id: int) -> None:  # noqa: N802
        if self._family != "b3" or not self._available:
            return
        self._control_selected_id = organism_id
        self._rebuild_current(preserve_rows=True, animate=False)

    @Slot(int)
    def selectTreatmentOrganism(self, organism_id: int) -> None:  # noqa: N802
        if self._family != "b3" or not self._available:
            return
        self._treatment_selected_id = organism_id
        self._rebuild_current(preserve_rows=True, animate=False)

    @Slot()
    def previousB3Seed(self) -> None:  # noqa: N802
        if self._family == "b3" and self._b3_seed_position > 0:
            self._select_b3_seed(self._b3_seed_position - 1)

    @Slot()
    def nextB3Seed(self) -> None:  # noqa: N802
        if self._family == "b3" and self._b3_seed_position + 1 < len(self._b3_seeds):
            self._select_b3_seed(self._b3_seed_position + 1)

    @Slot()
    def _sync_from_application(self) -> None:
        owner = self._application.presentationOwner
        artifact = self._application._artifact
        result = self._application._result
        if not owner or result is None:
            self._clear("Run a supported Study before opening Presentation.")
            return
        if owner != self._owner:
            self._reset_view_state()
            self._owner = owner
        if isinstance(artifact, ReferenceStudyRevision) and isinstance(
            result, ReferenceRunResult
        ):
            self._bind_reference(artifact, result)
            return
        if isinstance(artifact, B3StudyRevision) and isinstance(result, B3CuratedRunResult):
            self._bind_b3(artifact, result)
            return
        self._clear(
            "Native scientific world replay is currently available for Reference "
            "Ecology and the canonical B3 confirmation study."
        )

    def _bind_reference(
        self,
        artifact: ReferenceStudyRevision,
        result: ReferenceRunResult,
    ) -> None:
        view = inspect_reference_study_results(artifact, result)
        diagnostic = analysis_availability_diagnostic(view.spatial_availability)
        if diagnostic is not None:
            self._clear(diagnostic.message, remediation=diagnostic.remediation or "")
            return
        steps = available_step_indices(view.spatial_observations)
        if not steps:
            self._clear("No committed spatial observations were recorded for this run.")
            return
        same_binding = self._artifact == artifact and self._result is result
        self._artifact = artifact
        self._result = result
        self._family = "reference"
        self._steps = steps
        self._position = (
            min(self._position, len(steps) - 1) if same_binding else len(steps) - 1
        )
        if not same_binding:
            self._selected_id = None
        self._available = True
        self._message = "Reference replay uses only committed recorded spatial evidence."
        self._remediation = ""
        self._b3_seeds = ()
        self._b3_seed_position = 0
        self._rebuild_current(preserve_rows=False, animate=False)

    def _bind_b3(self, artifact: B3StudyRevision, result: B3CuratedRunResult) -> None:
        if artifact.scenario_identity != B3_VALIDATED_SCENARIO_ID:
            self._clear(
                "Matched flagship replay is available only for the validated canonical B3 "
                "scenario; derived sensitivity forks do not inherit that presentation."
            )
            return
        view = inspect_b3_results(artifact, result)
        if not view.confirmation:
            self._clear("This B3 result contains no authoritative confirmation pairs.")
            return
        same_binding = self._artifact == artifact and self._result is result
        seeds = tuple(pair.summary.seed for pair in view.confirmation)
        self._artifact = artifact
        self._result = result
        self._family = "b3"
        self._available = True
        self._message = _MATCHED_LANGUAGE
        self._remediation = ""
        self._b3_seeds = seeds
        self._b3_seed_position = (
            min(self._b3_seed_position, len(seeds) - 1) if same_binding else 0
        )
        if not same_binding:
            self._control_selected_id = None
            self._treatment_selected_id = None
        self._set_b3_steps(reset_position=not same_binding)
        self._rebuild_current(preserve_rows=False, animate=False)

    def _set_b3_steps(self, *, reset_position: bool) -> None:
        pair = self._current_b3_pair()
        control_steps = available_step_indices(pair.control_evidence.spatial_observations)
        treatment_steps = set(
            available_step_indices(pair.treatment_evidence.spatial_observations)
        )
        self._steps = tuple(step for step in control_steps if step in treatment_steps)
        if not self._steps:
            raise ValueError("B3 matched arms have no common committed spatial step.")
        if reset_position:
            self._position = 0
        else:
            self._position = min(self._position, len(self._steps) - 1)

    def _current_b3_pair(self):
        if not isinstance(self._artifact, B3StudyRevision) or not isinstance(
            self._result, B3CuratedRunResult
        ):
            raise RuntimeError("No exact B3 presentation owner is bound.")
        seed = self._b3_seeds[self._b3_seed_position]
        view = inspect_b3_results(self._artifact, self._result)
        pair = next((item for item in view.confirmation if item.summary.seed == seed), None)
        if pair is None:
            raise KeyError(f"No B3 confirmation replicate for seed {seed}.")
        return pair

    def _select_b3_seed(self, position: int) -> None:
        self._playing = False
        self._b3_seed_position = position
        self._control_selected_id = None
        self._treatment_selected_id = None
        self._set_b3_steps(reset_position=True)
        self._rebuild_current(preserve_rows=False, animate=False)
        self.viewChanged.emit()

    def _set_position(self, position: int, *, animate: bool) -> None:
        if position == self._position:
            return
        adjacent = abs(position - self._position) == 1
        self._position = position
        self._rebuild_current(preserve_rows=adjacent, animate=animate and adjacent)

    def _rebuild_current(self, *, preserve_rows: bool, animate: bool) -> None:
        if not self._available or not self._steps:
            return
        if self._family == "reference":
            self._rebuild_reference(preserve_rows=preserve_rows, animate=animate)
        elif self._family == "b3":
            self._rebuild_b3(preserve_rows=preserve_rows, animate=animate)

    def _rebuild_reference(self, *, preserve_rows: bool, animate: bool) -> None:
        if not isinstance(self._artifact, ReferenceStudyRevision) or not isinstance(
            self._result, ReferenceRunResult
        ):
            return
        frame = build_reference_workbench_world_presentation(
            self._artifact,
            self._result,
            step_index=self._steps[self._position],
            selected_organism_id=self._selected_id,
        ).frame
        same_ids = _same_organism_ids(self._organisms.items(), frame)
        self._set_transition(animate and same_ids)
        self._world_width = frame.world_width
        self._world_height = frame.world_height
        self._organisms.set_items(
            frame.organisms,
            preserve_delegates=preserve_rows and same_ids,
        )
        self._resources.set_items(frame.resources)
        self._carcasses.set_items(frame.carcasses)
        self._trails.set_items(frame.trails)
        self._set_encoding(frame)
        self._set_reference_inspector(frame)
        self.changed.emit()

    def _rebuild_b3(self, *, preserve_rows: bool, animate: bool) -> None:
        if not isinstance(self._artifact, B3StudyRevision) or not isinstance(
            self._result, B3CuratedRunResult
        ):
            return
        step = self._steps[self._position]
        seed = self._b3_seeds[self._b3_seed_position]
        control = build_b3_workbench_world_presentation(
            self._artifact,
            self._result,
            seed=seed,
            arm="control",
            step_index=step,
            selected_organism_id=self._control_selected_id,
        ).frame
        treatment = build_b3_workbench_world_presentation(
            self._artifact,
            self._result,
            seed=seed,
            arm="treatment",
            step_index=step,
            selected_organism_id=self._treatment_selected_id,
        ).frame
        if (
            control.world_width != treatment.world_width
            or control.world_height != treatment.world_height
        ):
            raise ValueError("B3 matched arms must use identical world bounds.")
        if control.focal_encoding != treatment.focal_encoding:
            raise ValueError("B3 matched arms must use one science-owned focal encoding.")
        control_same = _same_organism_ids(self._control_organisms.items(), control)
        treatment_same = _same_organism_ids(self._treatment_organisms.items(), treatment)
        self._set_transition(animate and control_same and treatment_same)
        self._world_width = control.world_width
        self._world_height = control.world_height
        self._control_organisms.set_items(
            control.organisms,
            preserve_delegates=preserve_rows and control_same,
        )
        self._control_resources.set_items(control.resources)
        self._control_carcasses.set_items(control.carcasses)
        self._control_trails.set_items(control.trails)
        self._treatment_organisms.set_items(
            treatment.organisms,
            preserve_delegates=preserve_rows and treatment_same,
        )
        self._treatment_resources.set_items(treatment.resources)
        self._treatment_carcasses.set_items(treatment.carcasses)
        self._treatment_trails.set_items(treatment.trails)
        self._set_encoding(control)
        self._set_b3_inspectors(control, treatment)
        self.changed.emit()

    def _set_encoding(self, frame: WorldPresentationFrame) -> None:
        encoding = frame.focal_encoding
        if encoding is None:
            self._legend_label = "Body mass sets marker size; selection uses an outline."
            self._legend_lower = 0
            self._legend_upper = 0
            return
        self._legend_label = encoding.label
        self._legend_lower = encoding.lower_bound
        self._legend_upper = encoding.upper_bound

    def _set_reference_inspector(self, frame: WorldPresentationFrame) -> None:
        selected = frame.selected_organism()
        if selected is None:
            self._selected_id = None
            self._inspector_title = "No organism selected"
            self._inspector_body = "Select an organism to inspect committed values."
            return
        self._inspector_title, self._inspector_body = _inspector_text(selected)

    def _set_b3_inspectors(
        self,
        control: WorldPresentationFrame,
        treatment: WorldPresentationFrame,
    ) -> None:
        control_selected = control.selected_organism()
        treatment_selected = treatment.selected_organism()
        if control_selected is None:
            self._control_selected_id = None
            self._control_inspector_title = "No organism selected"
            self._control_inspector_body = "Select a control organism."
        else:
            self._control_inspector_title, self._control_inspector_body = _inspector_text(
                control_selected
            )
        if treatment_selected is None:
            self._treatment_selected_id = None
            self._treatment_inspector_title = "No organism selected"
            self._treatment_inspector_body = "Select a treatment organism."
        else:
            (
                self._treatment_inspector_title,
                self._treatment_inspector_body,
            ) = _inspector_text(treatment_selected)

    def _set_transition(self, enabled: bool) -> None:
        self._transition_animated = enabled
        self.viewChanged.emit()

    def _reset_view_state(self) -> None:
        self._playing = False
        self._playback_speed = 1.0
        self._labels_visible = True
        self._trails_visible = True
        self._focus_mode = False
        self._transition_animated = False
        self._selected_id = None
        self._control_selected_id = None
        self._treatment_selected_id = None
        self._position = 0
        self._b3_seed_position = 0
        self.viewChanged.emit()

    def _clear(self, message: str, *, remediation: str = "") -> None:
        self._artifact = None
        self._result = None
        self._family = ""
        self._available = False
        self._message = message
        self._remediation = remediation
        self._steps = ()
        self._position = 0
        self._world_width = 0
        self._world_height = 0
        self._legend_label = ""
        self._legend_lower = 0
        self._legend_upper = 0
        self._b3_seeds = ()
        self._b3_seed_position = 0
        self._playing = False
        self._transition_animated = False
        self._organisms.set_items(())
        self._resources.set_items(())
        self._carcasses.set_items(())
        self._trails.set_items(())
        self._control_organisms.set_items(())
        self._control_resources.set_items(())
        self._control_carcasses.set_items(())
        self._control_trails.set_items(())
        self._treatment_organisms.set_items(())
        self._treatment_resources.set_items(())
        self._treatment_carcasses.set_items(())
        self._treatment_trails.set_items(())
        self.changed.emit()
        self.viewChanged.emit()


def _same_organism_ids(
    current: Sequence[OrganismPrimitive], frame: WorldPresentationFrame
) -> bool:
    return bool(frame.organisms) and tuple(item.organism_id for item in current) == tuple(
        item.organism_id for item in frame.organisms
    )


def _inspector_text(organism: OrganismPrimitive) -> tuple[str, str]:
    trait = (
        ""
        if organism.focal_trait_value is None
        else f" · maximum speed {organism.focal_trait_value}"
    )
    return (
        f"Organism {organism.organism_id}",
        f"age {organism.age} · energy {organism.energy} · body mass "
        f"{organism.body_mass} · mating type {organism.mating_type}{trait}",
    )


__all__ = ["PresentationController"]
