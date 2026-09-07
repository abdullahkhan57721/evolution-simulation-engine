"""WB5 tests for Study-facing scientific result navigation."""

from __future__ import annotations

from typing import cast

import pytest

from evo_engine.experiments.science import ScientificRunProvenance
from evo_engine.workbench.b3_curated import (
    B3_REQUIRED_EVIDENCE_IDS,
    B3CuratedRunResult,
    B3MatchedRunArtifacts,
    B3SingleRunArtifacts,
    create_b3_study_revision,
)
from evo_engine.workbench.controlled_locomotion import (
    EVENT_EVIDENCE_ID,
    POPULATION_EVIDENCE_ID,
    ControlledLocomotionIntent,
    EvidencePlan,
)
from evo_engine.workbench.experiments import (
    EnvironmentSelectionComparisonDefinition,
    MaxSpeedSweepDefinition,
    run_environment_selection_comparison,
    run_max_speed_sweep,
)
from evo_engine.workbench.reference_ecology import (
    POPULATION_EVIDENCE_ID as REFERENCE_POPULATION_EVIDENCE_ID,
    ReferenceEvidencePlan,
    default_reference_ecology_intent,
)
from evo_engine.workbench.reference_study import (
    ReferenceRunResult,
    create_reference_study_revision,
)
from evo_engine.workbench.results import (
    inspect_b3_results,
    inspect_controlled_locomotion_results,
    inspect_environment_selection_results,
    inspect_max_speed_sweep_results,
    inspect_reference_study_results,
)
from evo_engine.workbench.study import (
    WorkbenchRunProvenance,
    create_study_revision,
    run_study_revision,
)


def test_controlled_results_remain_attached_to_exact_revision_and_manifest() -> None:
    revision = create_study_revision(
        revision_id="study-a",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="separated_corridor",
            seed=17,
        ),
    )
    result = run_study_revision(revision, run_id="run-a")

    view = inspect_controlled_locomotion_results(revision, result)

    assert view.provenance is result.provenance
    assert view.provenance.study_revision_id == revision.revision_id
    assert view.provenance.manifest_digest == revision.manifest.digest
    assert view.scientific_provenance is result.scientific_provenance
    assert view.population_observations is result.population_observations
    assert view.locomotion is result.locomotion
    assert view.population_availability.available
    assert view.locomotion_availability.available

    other_revision = create_study_revision(
        revision_id="study-b",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="separated_corridor",
            seed=29,
        ),
    )
    with pytest.raises(ValueError, match="different Study revision"):
        inspect_controlled_locomotion_results(other_revision, result)


def test_unrecorded_controlled_analysis_is_unavailable_not_reconstructed() -> None:
    revision = create_study_revision(
        revision_id="population-only",
        intent=ControlledLocomotionIntent(
            max_speed=3,
            resource_geography="local_resource",
            seed=5,
        ),
        evidence_plan=EvidencePlan(requested=(POPULATION_EVIDENCE_ID,)),
    )
    result = run_study_revision(revision, run_id="population-only-run")

    view = inspect_controlled_locomotion_results(revision, result)

    assert view.population_availability.available
    assert not view.locomotion_availability.available
    assert view.locomotion_availability.missing_evidence_ids == (EVENT_EVIDENCE_ID,)
    assert view.locomotion is None


def test_reference_results_report_missing_evidence() -> None:
    plan = ReferenceEvidencePlan(requested=(REFERENCE_POPULATION_EVIDENCE_ID,))
    revision = create_reference_study_revision(
        revision_id="reference-population-only",
        intent=default_reference_ecology_intent(),
        evidence_plan=plan,
    )
    provenance = WorkbenchRunProvenance(
        run_id="reference-run",
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=plan.requested,
        evidence_references=("reference-run:population-observations",),
        result_references=(),
    )
    result = ReferenceRunResult(
        provenance=provenance,
        scientific_provenance=_scientific_provenance(seed=42),
        population_observations=(),
        applied_events=(),
        pedigree_records=(),
        genetic_observations=(),
        spatial_observations=(),
    )

    view = inspect_reference_study_results(revision, result)

    assert view.provenance is provenance
    assert view.population_availability.available
    assert not view.event_availability.available
    assert not view.pedigree_availability.available
    assert not view.genetic_availability.available
    assert not view.spatial_availability.available
    assert view.spatial_observations == ()


def test_e3_navigation_preserves_authoritative_outcomes_and_factor_identity() -> None:
    definition = MaxSpeedSweepDefinition(
        base_intent=ControlledLocomotionIntent(
            resource_geography="separated_corridor",
        ),
        levels=(2, 3),
        seeds=(17,),
    )
    result = run_max_speed_sweep(definition)

    view = inspect_max_speed_sweep_results(result)

    assert view.definition is result.definition
    assert view.treatment_summaries is result.treatment_summaries
    assert tuple(item.outcome for item in view.replicates) == result.replicate_outcomes
    assert tuple(item.factor_level for item in view.replicates) == (2, 3)
    assert tuple(item.seed for item in view.replicates) == (17, 17)
    assert tuple(item.manifest_digest for item in view.replicates) == tuple(
        treatment.manifest.digest for treatment in result.treatments
    )


def test_e4_navigation_preserves_full_composition_and_counterbalance_identity() -> None:
    definition = EnvironmentSelectionComparisonDefinition(seeds=(5,))
    result = run_environment_selection_comparison(definition)

    view = inspect_environment_selection_results(result)

    assert view.definition is result.definition
    assert view.environment_summaries is result.environment_summaries
    assert tuple(item.outcome for item in view.replicates) == result.replicate_outcomes
    assert tuple(item.role for item in view.replicates) == ("control", "treatment")
    assert tuple(item.factor_level for item in view.replicates) == (
        "local_resource",
        "separated_corridor",
    )
    assert all(item.standing_focal_composition == (1, 3, 9) for item in view.replicates)
    assert (
        view.replicates[0].founder_speed_order == view.replicates[1].founder_speed_order
    )
    assert (
        view.replicates[0].outcome.focal_trajectory
        is result.replicate_outcomes[0].focal_trajectory
    )
    assert (
        view.replicates[1].outcome.mechanisms is result.replicate_outcomes[1].mechanisms
    )


def test_b3_navigation_keeps_representative_support_artifact_roles_separate() -> None:
    revision = create_b3_study_revision(revision_id="b3")
    provenance = WorkbenchRunProvenance(
        run_id="b3-run",
        study_revision_id=revision.revision_id,
        manifest_digest=revision.manifest.digest,
        evidence_ids=B3_REQUIRED_EVIDENCE_IDS,
        evidence_references=("b3-run:evidence",),
        result_references=("b3-run:results",),
    )
    confirmation = (cast(B3MatchedRunArtifacts, object()),)
    sensitivity = (cast(B3SingleRunArtifacts, object()),)
    counterbalanced = (cast(B3MatchedRunArtifacts, object()),)
    result = B3CuratedRunResult(
        provenance=provenance,
        scenario_origin=revision.scenario_origin,
        scenario_identity=revision.scenario_identity,
        confirmation=confirmation,
        radius_sensitivity=sensitivity,
        counterbalanced=counterbalanced,
    )

    view = inspect_b3_results(revision, result)

    assert view.confirmation is confirmation
    assert view.radius_sensitivity is sensitivity
    assert view.counterbalanced is counterbalanced
    assert view.cinematic_handoff_availability.available


def _scientific_provenance(*, seed: int) -> ScientificRunProvenance:
    return ScientificRunProvenance(
        experiment_id="test",
        scenario_id="test",
        treatment_id="test",
        treatment_specification_json="{}",
        seed=seed,
        horizon_step_index=1,
        observation_every_n_steps=1,
        observation_include_step_zero=True,
        focal_variables=("population_size",),
    )
