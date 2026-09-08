"""Native authoring for existing concrete E3/E4 experiment definitions."""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from evo_engine.desktop.artifacts import ConcreteWorkbenchArtifact
from evo_engine.desktop.models.authoring import (
    ExperimentRunItem,
    ExperimentRunModel,
    FactorLevelItem,
    FactorLevelModel,
)
from evo_engine.workbench.experiment_authoring import (
    b3_case_counts,
    e4_counterbalance_label,
    environment_run_rows,
    max_speed_run_rows,
    parse_integer_sequence,
    update_environment_selection_comparison,
    update_max_speed_sweep,
)
from evo_engine.workbench import (
    SUPPORTED_MAX_SPEED_MAXIMUM,
    SUPPORTED_MAX_SPEED_MINIMUM,
    B3StudyRevision,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)


class ExperimentAuthoringController(QObject):
    """Own transient E3/E4 definition edits and authoritative expansion rows."""

    activeChanged = Signal()
    draftChanged = Signal()
    scientificDraftChanged = Signal()
    artifactReplaced = Signal(object)
    statusChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._artifact: ConcreteWorkbenchArtifact | None = None
        self._candidate: (
            MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition | None
        ) = None
        self._error = ""
        self._levels = FactorLevelModel()
        self._runs = ExperimentRunModel()
        self._status = "Experiment authoring is inactive."

    @Property(QObject, constant=True)
    def factorLevelModel(self) -> QObject:  # noqa: N802
        return self._levels

    @Property(QObject, constant=True)
    def runModel(self) -> QObject:  # noqa: N802
        return self._runs

    @Property(bool, notify=activeChanged)
    def active(self) -> bool:
        return self._artifact is not None

    @Property(str, notify=activeChanged)
    def mode(self) -> str:
        if isinstance(self._artifact, MaxSpeedSweepDefinition):
            return "e3"
        if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition):
            return "e4"
        if isinstance(self._artifact, B3StudyRevision):
            return "b3"
        if isinstance(self._artifact, StudyRevision):
            return "controlled-single"
        if isinstance(self._artifact, ReferenceStudyRevision):
            return "reference-single"
        return ""

    @Property(bool, notify=draftChanged)
    def draftDirty(self) -> bool:  # noqa: N802
        return self._candidate is not None and self._candidate != self._artifact

    @Property(bool, notify=draftChanged)
    def draftValid(self) -> bool:  # noqa: N802
        return self._error == ""

    @Property(str, notify=draftChanged)
    def validationMessage(self) -> str:  # noqa: N802
        return self._error

    @Property(str, notify=draftChanged)
    def replicateSeedsText(self) -> str:  # noqa: N802
        definition = self._working_definition()
        if definition is None:
            return ""
        return ", ".join(str(seed) for seed in definition.seeds)

    @Property(int, notify=draftChanged)
    def totalSimulations(self) -> int:  # noqa: N802
        return len(self._runs.items())

    @Property(str, notify=activeChanged)
    def factorLabel(self) -> str:  # noqa: N802
        if isinstance(self._artifact, MaxSpeedSweepDefinition):
            return "Maximum speed"
        if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition):
            return "Resource geography"
        return ""

    @Property(str, notify=activeChanged)
    def baseResourceGeography(self) -> str:  # noqa: N802
        if isinstance(self._artifact, MaxSpeedSweepDefinition):
            return _humanize(self._artifact.base_intent.resource_geography)
        return ""

    @Property(str, notify=activeChanged)
    def controlEnvironment(self) -> str:  # noqa: N802
        if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition):
            return _humanize(self._artifact.control_environment)
        return ""

    @Property(str, notify=activeChanged)
    def treatmentEnvironment(self) -> str:  # noqa: N802
        if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition):
            return _humanize(self._artifact.treatment_environment)
        return ""

    @Property(str, notify=activeChanged)
    def standingComposition(self) -> str:  # noqa: N802
        if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition):
            return ", ".join(str(value) for value in self._artifact.focal_speeds)
        return ""

    @Property(str, notify=activeChanged)
    def counterbalanceLabel(self) -> str:  # noqa: N802
        return (
            e4_counterbalance_label()
            if isinstance(self._artifact, EnvironmentSelectionComparisonDefinition)
            else ""
        )

    @Property(int, notify=activeChanged)
    def b3ConfirmationPairs(self) -> int:  # noqa: N802
        return self._b3_counts("confirmation_pairs")

    @Property(int, notify=activeChanged)
    def b3RadiusSensitivityRuns(self) -> int:  # noqa: N802
        return self._b3_counts("radius_sensitivity_runs")

    @Property(int, notify=activeChanged)
    def b3CounterbalancedPairs(self) -> int:  # noqa: N802
        return self._b3_counts("counterbalanced_pairs")

    @Property(int, notify=activeChanged)
    def b3TotalSimulations(self) -> int:  # noqa: N802
        return self._b3_counts("total_simulations")

    @Property(str, notify=activeChanged)
    def singleRunMessage(self) -> str:  # noqa: N802
        if isinstance(self._artifact, StudyRevision):
            return (
                "No multi-treatment experiment is configured. This Study represents "
                "one controlled simulation."
            )
        if isinstance(self._artifact, ReferenceStudyRevision):
            return (
                "Reference Ecology currently has no generic controlled-experiment "
                "definition. Q2 does not invent one."
            )
        return ""

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    def activate_artifact(self, artifact: ConcreteWorkbenchArtifact) -> None:
        self._artifact = artifact
        self._candidate = None
        self._error = ""
        self._refresh_models()
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Experiment follows the active concrete Workbench definition.")

    def clear(self) -> None:
        self._artifact = None
        self._candidate = None
        self._error = ""
        self._levels.set_items(())
        self._runs.set_items(())
        self.activeChanged.emit()
        self.draftChanged.emit()
        self._set_status("Experiment authoring is inactive.")

    @Slot(int, bool)
    def setE3LevelSelected(self, level: int, selected: bool) -> None:  # noqa: N802
        definition = self._working_definition()
        if not isinstance(definition, MaxSpeedSweepDefinition):
            return
        if type(level) is not int or type(selected) is not bool:
            return
        if not SUPPORTED_MAX_SPEED_MINIMUM <= level <= SUPPORTED_MAX_SPEED_MAXIMUM:
            return
        levels = set(definition.levels)
        if selected:
            levels.add(level)
        else:
            levels.discard(level)
        self._try_e3(levels=tuple(sorted(levels)), seeds=definition.seeds)

    @Slot(str)
    def setReplicateSeeds(self, value: str) -> None:  # noqa: N802
        definition = self._working_definition()
        if not isinstance(
            definition,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            return
        try:
            seeds = parse_integer_sequence(value, name="Replicate seeds")
        except (TypeError, ValueError) as exc:
            self._set_invalid(str(exc))
            return
        if isinstance(definition, MaxSpeedSweepDefinition):
            self._try_e3(levels=definition.levels, seeds=seeds)
        else:
            self._try_e4(seeds=seeds)

    @Slot(result=bool)
    def applyExperimentDesign(self) -> bool:  # noqa: N802
        if self._candidate is None or self._candidate == self._artifact or self._error:
            self._set_status("No valid changed experiment definition to apply.")
            return False
        self.artifactReplaced.emit(self._candidate)
        return True

    def _working_definition(
        self,
    ) -> MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition | None:
        if self._candidate is not None:
            return self._candidate
        if isinstance(
            self._artifact,
            (MaxSpeedSweepDefinition, EnvironmentSelectionComparisonDefinition),
        ):
            return self._artifact
        return None

    def _try_e3(self, *, levels: tuple[int, ...], seeds: tuple[int, ...]) -> None:
        assert isinstance(self._artifact, MaxSpeedSweepDefinition)
        try:
            candidate = update_max_speed_sweep(
                self._artifact, levels=levels, seeds=seeds
            )
            max_speed_run_rows(candidate)
        except (TypeError, ValueError) as exc:
            self._set_invalid(str(exc))
            return
        self._set_candidate(candidate)

    def _try_e4(self, *, seeds: tuple[int, ...]) -> None:
        assert isinstance(self._artifact, EnvironmentSelectionComparisonDefinition)
        try:
            candidate = update_environment_selection_comparison(
                self._artifact, seeds=seeds
            )
            environment_run_rows(candidate)
        except (TypeError, ValueError) as exc:
            self._set_invalid(str(exc))
            return
        self._set_candidate(candidate)

    def _set_candidate(
        self,
        candidate: MaxSpeedSweepDefinition | EnvironmentSelectionComparisonDefinition,
    ) -> None:
        if candidate == self._candidate and not self._error:
            return
        self._candidate = candidate
        self._error = ""
        self._refresh_models()
        self.draftChanged.emit()
        self.scientificDraftChanged.emit()
        self._set_status("Unsaved experiment definition changed.")

    def _set_invalid(self, message: str) -> None:
        self._candidate = None
        self._error = message
        self._refresh_models()
        self.draftChanged.emit()
        self.scientificDraftChanged.emit()
        self._set_status(f"Experiment draft is invalid: {message}")

    def _refresh_models(self) -> None:
        definition = self._working_definition()
        if isinstance(definition, MaxSpeedSweepDefinition):
            selected = set(definition.levels)
            self._levels.set_items(
                tuple(
                    FactorLevelItem(value=value, selected=value in selected)
                    for value in range(
                        SUPPORTED_MAX_SPEED_MINIMUM, SUPPORTED_MAX_SPEED_MAXIMUM + 1
                    )
                )
            )
            self._runs.set_items(
                tuple(
                    ExperimentRunItem(
                        maximum_speed=str(row.maximum_speed),
                        seed=str(row.seed),
                        resource_geography=_humanize(row.resource_geography),
                    )
                    for row in max_speed_run_rows(definition)
                )
            )
            return
        self._levels.set_items(())
        if isinstance(definition, EnvironmentSelectionComparisonDefinition):
            self._runs.set_items(
                tuple(
                    ExperimentRunItem(
                        seed=str(row.seed),
                        role=row.role.title(),
                        environment=_humanize(row.environment),
                        standing_composition=_integer_text(
                            row.standing_focal_composition
                        ),
                        founder_order=_integer_text(row.founder_speed_order),
                    )
                    for row in environment_run_rows(definition)
                )
            )
            return
        self._runs.set_items(())

    def _b3_counts(self, field: str) -> int:
        if not isinstance(self._artifact, B3StudyRevision):
            return 0
        return int(getattr(b3_case_counts(self._artifact), field))

    def _set_status(self, value: str) -> None:
        self._status = value
        self.statusChanged.emit()


def _integer_text(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values)


def _humanize(value: object) -> str:
    return str(value).replace("_", " ").replace("-", " ").title()


__all__ = ["ExperimentAuthoringController"]
