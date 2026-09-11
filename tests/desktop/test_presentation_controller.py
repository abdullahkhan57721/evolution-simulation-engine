from __future__ import annotations

import os
from types import SimpleNamespace
from typing import cast

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

import evo_engine.desktop.controllers.presentation as presentation_module
from evo_engine.desktop.artifacts import new_b3_flagship, new_reference_ecology
from evo_engine.desktop.controllers import ApplicationController, PresentationController
from evo_engine.desktop.models import (
    WorldCarcassModel,
    WorldOrganismModel,
    WorldResourceModel,
    WorldTrailModel,
)
from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.presentation.scientific import ContinuousTraitEncoding
from evo_engine.presentation.world import (
    CarcassPrimitive,
    MovementTrail,
    OrganismPrimitive,
    ResourcePrimitive,
    WorldPresentationFrame,
)
from evo_engine.workbench import (
    REFERENCE_SPATIAL_EVIDENCE_ID,
    B3CuratedRunResult,
    ReferenceRunResult,
    WorkbenchRunProvenance,
)
from evo_engine.workbench.results import AnalysisAvailability


def _app() -> QGuiApplication:
    return cast(QGuiApplication, QGuiApplication.instance() or QGuiApplication([]))


def _scientific_provenance() -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="q4-presentation-test",
        scenario_id="q4-test-scenario",
        treatment_id="q4-test-treatment",
        treatment_specification_json="{}",
        seed=7,
        horizon_step_index=3,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
        run_role="representative",
    )


def _workbench_provenance(revision, *, run_id: str) -> WorkbenchRunProvenance:
    return WorkbenchRunProvenance(
        run_id=run_id,
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=revision.evidence_plan.requested,
        evidence_references=(),
        result_references=(),
    )


def _reference_result(revision) -> ReferenceRunResult:
    return ReferenceRunResult(
        provenance=_workbench_provenance(revision, run_id="q4-reference-run"),
        scientific_provenance=_scientific_provenance(),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )


def _b3_result(revision) -> B3CuratedRunResult:
    return B3CuratedRunResult(
        provenance=_workbench_provenance(revision, run_id="q4-b3-run"),
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=(),
        radius_sensitivity=(),
        counterbalanced=(),
    )


def _available(analysis_id: str = "q4.spatial") -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id=analysis_id,
        source_contract="Q4 native Presentation test evidence",
        required_evidence_ids=(),
    )


def _missing() -> AnalysisAvailability:
    return AnalysisAvailability(
        analysis_id="q4.spatial",
        source_contract="Q4 native Presentation test evidence",
        required_evidence_ids=(REFERENCE_SPATIAL_EVIDENCE_ID,),
        missing_evidence_ids=(REFERENCE_SPATIAL_EVIDENCE_ID,),
    )


def _frame(
    step: int,
    *,
    organism_ids: tuple[int, ...] = (1, 2),
    selected: int | None = None,
    encoding: ContinuousTraitEncoding | None = None,
    offset: int = 0,
) -> WorldPresentationFrame:
    organisms = tuple(
        OrganismPrimitive(
            organism_id=organism_id,
            x=organism_id + step + offset,
            y=organism_id * 2 + step,
            age=step,
            energy=100 - step,
            body_mass=2,
            mating_type="A",
            marker_size=14,
            selected=organism_id == selected,
            focal_trait_value=3 if encoding is not None else None,
            focal_trait_normalized=0.25 if encoding is not None else None,
        )
        for organism_id in organism_ids
    )
    return WorldPresentationFrame(
        committed_step_index=step,
        world_width=20,
        world_height=15,
        organisms=organisms,
        resources=(ResourcePrimitive(x=2, y=3, amount=4),),
        carcasses=(CarcassPrimitive(carcass_id=9, x=4, y=5, resource_units=6),),
        trails=(MovementTrail(organism_id=organism_ids[0], points=((1, 1), (2, 2))),),
        selected_organism_id=selected,
        focal_encoding=encoding,
    )


def _bind_reference_owner(
    app: ApplicationController,
    monkeypatch: pytest.MonkeyPatch,
    *,
    steps: tuple[int, ...] = (0, 1, 2),
) -> list[tuple[int, int | None]]:
    revision = new_reference_ecology(revision_id="q4-reference")
    result = _reference_result(revision)
    calls: list[tuple[int, int | None]] = []
    view = SimpleNamespace(
        spatial_availability=_available(),
        spatial_observations=steps,
    )
    monkeypatch.setattr(
        presentation_module,
        "inspect_reference_study_results",
        lambda *_: view,
    )
    monkeypatch.setattr(
        presentation_module,
        "available_step_indices",
        lambda observations: tuple(observations),
    )

    def build_frame(*_args, step_index: int, selected_organism_id=None, **_kwargs):
        calls.append((step_index, selected_organism_id))
        return SimpleNamespace(frame=_frame(step_index, selected=selected_organism_id))

    monkeypatch.setattr(
        presentation_module,
        "build_reference_workbench_world_presentation",
        build_frame,
    )
    app._artifact = revision
    app._result = result
    app._presentation_owner = "q4-reference-owner"
    return calls


def test_world_models_project_only_presentation_values_and_discontinuities_reset(
) -> None:
    _app()
    first = _frame(0)
    second = _frame(1)
    birth = _frame(2, organism_ids=(1, 2, 3))

    organisms = WorldOrganismModel()
    resources = WorldResourceModel()
    carcasses = WorldCarcassModel()
    trails = WorldTrailModel()

    assert not organisms.set_items(first.organisms)
    assert organisms.set_items(second.organisms, preserve_delegates=True)
    assert organisms.items() == second.organisms
    assert not organisms.set_items(birth.organisms, preserve_delegates=True)
    resources.set_items(first.resources)
    carcasses.set_items(first.carcasses)
    trails.set_items(first.trails)

    assert resources.items() == first.resources
    assert carcasses.items() == first.carcasses
    assert trails.items() == first.trails


def test_reference_exact_seek_and_view_state_never_change_committed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    calls = _bind_reference_owner(app, monkeypatch)
    presentation = PresentationController(app)

    assert presentation.available
    assert presentation.family == "reference"
    assert presentation.committedStep == 2
    assert calls[-1] == (2, None)
    committed_before = cast(WorldOrganismModel, presentation.organismModel).items()

    presentation.toggleLabels()
    presentation.toggleTrails()
    presentation.toggleFocusMode()
    presentation.setPlaybackSpeed(4.0)

    assert presentation.committedStep == 2
    assert (
        cast(WorldOrganismModel, presentation.organismModel).items()
        == committed_before
    )

    presentation.seekStepPosition(0)
    assert presentation.committedStep == 0
    assert calls[-1] == (0, None)
    assert not presentation.transitionAnimated

    presentation.selectOrganism(1)
    selected = cast(WorldOrganismModel, presentation.organismModel).items()
    assert calls[-1] == (0, 1)
    assert next(item for item in selected if item.organism_id == 1).selected
    assert presentation.committedStep == 0


def test_animation_is_eligible_only_for_identity_stable_adjacent_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    revision = new_reference_ecology(revision_id="q4-animation")
    app._artifact = revision
    app._result = _reference_result(revision)
    app._presentation_owner = "q4-animation-owner"
    monkeypatch.setattr(
        presentation_module,
        "inspect_reference_study_results",
        lambda *_: SimpleNamespace(
            spatial_availability=_available(), spatial_observations=(0, 1, 2)
        ),
    )
    monkeypatch.setattr(
        presentation_module,
        "available_step_indices",
        lambda observations: tuple(observations),
    )

    def build_frame(*_args, step_index: int, selected_organism_id=None, **_kwargs):
        ids = (1, 2) if step_index < 2 else (1, 2, 3)
        return SimpleNamespace(
            frame=_frame(step_index, organism_ids=ids, selected=selected_organism_id)
        )

    monkeypatch.setattr(
        presentation_module,
        "build_reference_workbench_world_presentation",
        build_frame,
    )
    presentation = PresentationController(app)
    presentation.seekStepPosition(0)

    presentation.nextStep()
    assert presentation.committedStep == 1
    assert presentation.transitionAnimated
    assert (
        cast(WorldOrganismModel, presentation.organismModel).items()
        == _frame(1).organisms
    )

    presentation.nextStep()
    assert presentation.committedStep == 2
    assert not presentation.transitionAnimated
    assert tuple(
        item.organism_id
        for item in cast(WorldOrganismModel, presentation.organismModel).items()
    ) == (1, 2, 3)

    presentation.seekStepPosition(0)
    assert not presentation.transitionAnimated


def test_reference_missing_spatial_evidence_preserves_remediation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    revision = new_reference_ecology(revision_id="q4-missing")
    app._artifact = revision
    app._result = _reference_result(revision)
    app._presentation_owner = "q4-missing-owner"
    monkeypatch.setattr(
        presentation_module,
        "inspect_reference_study_results",
        lambda *_: SimpleNamespace(
            spatial_availability=_missing(), spatial_observations=()
        ),
    )
    presentation = PresentationController(app)

    assert not presentation.available
    assert REFERENCE_SPATIAL_EVIDENCE_ID in cast(str, presentation.message)
    assert presentation.remediation
    assert cast(WorldOrganismModel, presentation.organismModel).items() == ()


def test_b3_uses_one_seed_common_step_fixed_encoding_and_arm_local_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    revision = new_b3_flagship(revision_id="q4-b3")
    result = _b3_result(revision)
    app._artifact = revision
    app._result = result
    app._presentation_owner = "q4-b3-owner"
    pair = SimpleNamespace(
        summary=SimpleNamespace(seed=17),
        control_evidence=SimpleNamespace(spatial_observations=(0, 1, 2)),
        treatment_evidence=SimpleNamespace(spatial_observations=(1, 2, 3)),
    )
    monkeypatch.setattr(
        presentation_module,
        "inspect_b3_results",
        lambda *_: SimpleNamespace(confirmation=(pair,)),
    )
    monkeypatch.setattr(
        presentation_module,
        "available_step_indices",
        lambda observations: tuple(observations),
    )
    encoding = ContinuousTraitEncoding(
        trait_name="max_speed",
        label="Maximum speed",
        lower_bound=1,
        upper_bound=9,
    )
    calls: list[tuple[str, int, int, int | None]] = []

    def build_frame(
        *_args,
        seed: int,
        arm: str,
        step_index: int,
        selected_organism_id=None,
        **_kwargs,
    ):
        calls.append((arm, seed, step_index, selected_organism_id))
        return SimpleNamespace(
            frame=_frame(
                step_index,
                selected=selected_organism_id,
                encoding=encoding,
                offset=0 if arm == "control" else 3,
            )
        )

    monkeypatch.setattr(
        presentation_module,
        "build_b3_workbench_world_presentation",
        build_frame,
    )
    presentation = PresentationController(app)

    assert presentation.available
    assert presentation.family == "b3"
    assert presentation.b3Seed == 17
    assert presentation.committedStep == 1
    assert presentation.stepCount == 2
    assert presentation.legendLabel == "Maximum speed"
    assert presentation.legendLower == 1
    assert presentation.legendUpper == 9
    assert "does not imply RNG lockstep" in cast(str, presentation.matchedLanguage)
    assert calls[-2:] == [("control", 17, 1, None), ("treatment", 17, 1, None)]

    presentation.selectControlOrganism(1)
    assert calls[-2:] == [("control", 17, 1, 1), ("treatment", 17, 1, None)]
    control = cast(WorldOrganismModel, presentation.controlOrganismModel).items()
    treatment = cast(WorldOrganismModel, presentation.treatmentOrganismModel).items()
    assert next(item for item in control if item.organism_id == 1).selected
    assert not next(item for item in treatment if item.organism_id == 1).selected


def test_presentation_resets_view_state_when_exact_owner_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app()
    app = ApplicationController()
    _bind_reference_owner(app, monkeypatch)
    presentation = PresentationController(app)
    presentation.toggleLabels()
    presentation.toggleTrails()
    presentation.toggleFocusMode()
    presentation.setPlaybackSpeed(4.0)
    presentation.selectOrganism(1)

    second = new_reference_ecology(revision_id="q4-reference-next")
    app._artifact = second
    app._result = _reference_result(second)
    app._presentation_owner = "q4-reference-owner-next"
    app.presentationChanged.emit()

    assert presentation.labelsVisible
    assert presentation.trailsVisible
    assert not presentation.focusMode
    assert presentation.playbackSpeed == 1.0
    assert "No organism selected" == presentation.inspectorTitle
