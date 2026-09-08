from __future__ import annotations

import os
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from evo_engine.desktop.artifacts import serialize_concrete_artifact
from evo_engine.desktop.controllers import (
    ApplicationController,
    EvidenceAuthoringController,
    ExperimentAuthoringController,
    ReferenceStudyController,
    SimulationAuthoringController,
)
from evo_engine.desktop.models import (
    EvidenceOptionModel,
    ExperimentRunModel,
    SemanticDiffModel,
)
from evo_engine.workbench import (
    B3_VALIDATED_SCENARIO_ID,
    REFERENCE_EXPERT_SLOT_IDS,
    REFERENCE_EXTENSION_CAPABILITIES,
    REFERENCE_SPATIAL_EVIDENCE_ID,
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    ReferenceStudyRevision,
    StudyRevision,
)


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _controller() -> ApplicationController:
    _app()
    return ApplicationController()


def _active(controller: ApplicationController):
    assert controller._artifact is not None
    return controller._artifact


def _simulation(controller: ApplicationController) -> SimulationAuthoringController:
    return cast(SimulationAuthoringController, controller.simulationController)


def _reference(controller: ApplicationController) -> ReferenceStudyController:
    return cast(ReferenceStudyController, controller.referenceController)


def _evidence(controller: ApplicationController) -> EvidenceAuthoringController:
    return cast(EvidenceAuthoringController, controller.evidenceController)


def _experiment(controller: ApplicationController) -> ExperimentAuthoringController:
    return cast(ExperimentAuthoringController, controller.experimentController)


def test_controlled_simulation_draft_is_bounded_and_commits_immutable_child() -> None:
    controller = _controller()
    assert controller.createStudy("controlled-run")
    parent = _active(controller)
    assert isinstance(parent, StudyRevision)
    parent_json = parent.to_json()
    parent_id = parent.revision_id
    simulation = _simulation(controller)

    simulation.set_controlled_max_speed(7)
    simulation.set_controlled_resource_geography("separated_corridor")
    simulation.set_controlled_seed(909)

    assert simulation.controlledDraftDirty
    assert simulation.controlledDraftReady
    assert serialize_concrete_artifact(_active(controller)) == parent_json
    assert simulation.saveControlledChildRevision()

    child = _active(controller)
    assert isinstance(child, StudyRevision)
    assert child.parent_revision_id == parent_id
    assert child.intent.max_speed == 7
    assert child.intent.resource_geography == "separated_corridor"
    assert child.intent.seed == 909
    assert parent.to_json() == parent_json
    assert controller.fileLocation == ""
    diff = cast(SemanticDiffModel, simulation.semanticDiffModel).items()
    assert any(item.group == "Explicit changes" for item in diff)
    assert any("Maximum speed" in item.label for item in diff)


def test_reference_applicability_reconciles_transient_draft_without_expert_controls() -> (
    None
):
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    reference = _reference(controller)

    assert reference.hasExpertControls is False
    assert REFERENCE_EXPERT_SLOT_IDS == ()
    assert REFERENCE_EXTENSION_CAPABILITIES

    reference.draftExplorationMovement = "gaussian"
    assert reference.gaussianApplicable
    reference.draftGaussianStandardDeviation = 4
    assert reference.draftGaussianStandardDeviation == 4
    reference.draftExplorationMovement = "moore"
    assert not reference.gaussianApplicable
    assert reference.draftGaussianStandardDeviation == 0
    assert reference.normalizationNotice

    reference.draftResourceGeography = "two_patches"
    assert reference.patchGeometryApplicable
    reference.draftPatch1Radius = 3
    reference.draftResourceGeography = "uniform"
    assert not reference.patchGeometryApplicable
    assert reference.draftPatch1Radius == 0

    reference.draftMutationEnabled = True
    assert reference.mutationParametersApplicable
    reference.draftMutationProbability = 500
    reference.draftMutationMaxChange = 2
    reference.draftMutationEnabled = False
    assert not reference.mutationParametersApplicable
    assert reference.draftMutationProbability == 0
    assert reference.draftMutationMaxChange == 0


def test_reference_simulation_commit_preserves_parent_lineage_and_diff() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    parent = _active(controller)
    assert isinstance(parent, ReferenceStudyRevision)
    parent_json = parent.to_json()
    parent_id = parent.revision_id
    reference = _reference(controller)

    reference.set_draft_max_speed(4 if reference.draftMaxSpeed != 4 else 3)
    assert reference.draftDirty
    assert reference.draftReady
    assert reference.saveChildRevision()

    child = _active(controller)
    assert isinstance(child, ReferenceStudyRevision)
    assert child.parent_revision_id == parent_id
    assert parent.to_json() == parent_json
    diff = cast(SemanticDiffModel, _simulation(controller).semanticDiffModel).items()
    assert any(item.group == "Explicit changes" for item in diff)


def test_b3_simulation_is_curated_and_supported_fork_shows_identity_loss() -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    assert controller.scenarioIdentity == B3_VALIDATED_SCENARIO_ID
    assert _simulation(controller).readOnlyMessage

    assert controller.forkStudy()

    assert controller.scenarioOrigin
    assert controller.scenarioIdentity == ""
    diff = cast(SemanticDiffModel, _simulation(controller).semanticDiffModel).items()
    assert any(
        item.group == "Identity changes" and item.tone == "warning" for item in diff
    )


def test_e3_and_e4_simulation_assumptions_remain_read_only() -> None:
    controller = _controller()
    for kind in ("max-speed-sweep", "environment-selection-comparison"):
        assert controller.createStudy(kind)
        assert _simulation(controller).readOnlyMessage
        before = serialize_concrete_artifact(_active(controller))
        assert controller.selectSection("Simulation")
        assert serialize_concrete_artifact(_active(controller)) == before


def test_controlled_evidence_draft_commits_new_revision_and_missing_implication() -> (
    None
):
    controller = _controller()
    assert controller.createStudy("controlled-run")
    parent = _active(controller)
    assert isinstance(parent, StudyRevision)
    parent_id = parent.revision_id
    evidence = _evidence(controller)
    options = cast(EvidenceOptionModel, evidence.optionModel).items()
    assert len(options) == 2
    assert all(item.editable for item in options)

    first = options[0]
    evidence.setEvidenceSelected(first.evidence_id, False)
    assert evidence.draftDirty
    assert evidence.draftReady
    assert "cannot be reconstructed" in str(evidence.missingEvidenceMessage)
    assert evidence.saveEvidenceChildRevision()

    child = _active(controller)
    assert isinstance(child, StudyRevision)
    assert child.parent_revision_id == parent_id
    assert first.evidence_id not in child.evidence_plan.requested


def test_reference_spatial_evidence_warning_and_immutable_child() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    parent = _active(controller)
    assert isinstance(parent, ReferenceStudyRevision)
    parent_id = parent.revision_id
    evidence = _evidence(controller)
    options = cast(EvidenceOptionModel, evidence.optionModel).items()
    spatial = next(
        item for item in options if item.evidence_id == REFERENCE_SPATIAL_EVIDENCE_ID
    )

    evidence.setEvidenceSelected(spatial.evidence_id, True)
    assert evidence.draftReady
    assert "storage grows" in str(evidence.advisoryMessage)
    assert evidence.saveEvidenceChildRevision()

    child = _active(controller)
    assert isinstance(child, ReferenceStudyRevision)
    assert child.parent_revision_id == parent_id
    assert REFERENCE_SPATIAL_EVIDENCE_ID in child.evidence_plan.requested


def test_b3_e3_e4_evidence_is_locked_and_required() -> None:
    controller = _controller()
    for kind in (
        "b3-flagship",
        "max-speed-sweep",
        "environment-selection-comparison",
    ):
        assert controller.createStudy(kind)
        evidence = _evidence(controller)
        options = cast(EvidenceOptionModel, evidence.optionModel).items()
        assert options
        assert not evidence.editable
        assert evidence.lockMessage
        assert all(item.required and not item.editable for item in options)
        before = serialize_concrete_artifact(_active(controller))
        evidence.setEvidenceSelected(options[0].evidence_id, False)
        assert serialize_concrete_artifact(_active(controller)) == before


def test_e3_levels_and_seeds_use_authoritative_expansion_before_apply() -> None:
    controller = _controller()
    assert controller.createStudy("max-speed-sweep")
    experiment = _experiment(controller)
    saved = _active(controller)
    assert isinstance(saved, MaxSpeedSweepDefinition)

    experiment.setE3LevelSelected(10, True)
    experiment.setReplicateSeeds("101, 202")

    assert experiment.draftDirty
    assert experiment.draftValid
    runs = cast(ExperimentRunModel, experiment.runModel).items()
    selected_levels = set(saved.levels) | {10}
    assert len(runs) == len(selected_levels) * 2
    assert {item.seed for item in runs} == {"101", "202"}
    assert _active(controller) == saved

    assert experiment.applyExperimentDesign()
    applied = _active(controller)
    assert isinstance(applied, MaxSpeedSweepDefinition)
    assert applied.seeds == (101, 202)
    assert 10 in applied.levels


def test_e4_seed_authoring_preserves_factor_roles_composition_and_counterbalance() -> (
    None
):
    controller = _controller()
    assert controller.createStudy("environment-selection-comparison")
    experiment = _experiment(controller)
    saved = _active(controller)
    assert isinstance(saved, EnvironmentSelectionComparisonDefinition)

    experiment.setReplicateSeeds("11, 22, 33")

    assert experiment.draftDirty
    assert experiment.controlEnvironment == "Local Resource"
    assert experiment.treatmentEnvironment == "Separated Corridor"
    assert experiment.standingComposition == "1, 3, 9"
    assert "Founder-order counterbalance" in str(experiment.counterbalanceLabel)
    runs = cast(ExperimentRunModel, experiment.runModel).items()
    assert len(runs) == 6
    assert {item.role for item in runs} == {"Control", "Treatment"}
    assert all(item.standing_composition == "1, 3, 9" for item in runs)
    assert all(item.founder_order for item in runs)

    assert experiment.applyExperimentDesign()
    applied = _active(controller)
    assert isinstance(applied, EnvironmentSelectionComparisonDefinition)
    assert applied.seeds == (11, 22, 33)
    assert applied.control_environment == saved.control_environment
    assert applied.treatment_environment == saved.treatment_environment
    assert applied.focal_speeds == saved.focal_speeds


def test_b3_and_single_run_experiment_pages_do_not_invent_generic_experiments() -> None:
    controller = _controller()
    assert controller.createStudy("b3-flagship")
    experiment = _experiment(controller)
    assert experiment.mode == "b3"
    assert int(experiment.b3TotalSimulations) > 0
    assert not experiment.draftDirty

    for kind in ("controlled-run", "reference-ecology"):
        assert controller.createStudy(kind)
        experiment = _experiment(controller)
        assert experiment.singleRunMessage
        assert experiment.totalSimulations == 0


def test_authoring_draft_change_clears_q1_transient_result_ownership_state() -> None:
    controller = _controller()
    assert controller.createStudy("reference-ecology")
    controller.set_run_plan_open(True)
    controller._presentation_owner = "stale-owner"
    epoch = controller._presentation_epoch

    evidence = _evidence(controller)
    option = next(
        item
        for item in cast(EvidenceOptionModel, evidence.optionModel).items()
        if not item.selected
    )
    evidence.setEvidenceSelected(option.evidence_id, True)

    assert not controller.runPlanOpen
    assert controller.presentationOwner == ""
    assert controller._presentation_epoch > epoch
