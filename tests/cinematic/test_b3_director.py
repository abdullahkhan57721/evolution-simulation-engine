"""Tests for the concrete confirmed-B3 cinematic director preparation."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.cinematic.b3_director import (
    B3_BOUNDED_CONCLUSION,
    B3_FLAGSHIP_ACTS,
    B3_REPRESENTATIVE_SEED,
    B3_SCOPE_QUALIFIER,
    prepare_b3_flagship_director,
)
from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3RunEvidence,
    B3RunSummary,
    run_b3_flagship,
    summarize_b3_run,
)
from evo_engine.genetics import MAX_SPEED
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_PRIMARY_STEP,
    build_b3_flagship_specification,
)


@pytest.fixture(scope="module")
def representative_evidence() -> tuple[B3RunEvidence, B3RunEvidence]:
    """Run the frozen B3 representative matched pair once for director tests."""
    control = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="uniform",
        )
    )
    treatment = run_b3_flagship(
        build_b3_flagship_specification(
            seed=B3_REPRESENTATIVE_SEED,
            environment="compact_patch",
        )
    )
    return control, treatment


def test_representative_plan_uses_fixed_science_and_real_episodes(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control, treatment = representative_evidence

    plan = prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
    )

    assert plan.focal_encoding.trait_name == MAX_SPEED
    assert plan.focal_encoding.label == "Maximum speed"
    assert plan.focal_encoding.lower_bound == B3_LOW_MAX_SPEED
    assert plan.focal_encoding.upper_bound == B3_HIGH_MAX_SPEED
    assert plan.control.timeline.focal_encoding is plan.focal_encoding
    assert plan.treatment.timeline.focal_encoding is plan.focal_encoding
    assert plan.acts == B3_FLAGSHIP_ACTS
    assert plan.conclusion == B3_BOUNDED_CONCLUSION
    assert plan.scope_qualifier == B3_SCOPE_QUALIFIER
    assert not plan.is_full_flagship

    episodes = tuple(focus.episode for focus in plan.representative_focus)
    assert tuple(
        (episode.organism_id, episode.completed_step_index, episode.max_speed_capacity)
        for episode in episodes
    ) == ((16, 7, 1), (1, 5, 4))
    assert (episodes[0].start, episodes[0].end) == ((4, 5), (3, 5))
    assert episodes[0].realized_displacement == pytest.approx(1.0)
    assert episodes[0].movement_energy_cost == 1
    assert episodes[0].resource_consumed_same_step == 8
    assert (episodes[1].start, episodes[1].end) == ((2, 0), (2, 4))
    assert episodes[1].realized_displacement == pytest.approx(4.0)
    assert episodes[1].movement_energy_cost == 2
    assert episodes[1].resource_consumed_same_step == 8


def test_focus_remains_separate_from_scientific_fill_and_body_mass(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control, treatment = representative_evidence
    plan = prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
    )
    focus = plan.representative_focus[1]
    frame = next(
        frame
        for frame in plan.treatment.timeline.frames
        if frame.step_index == focus.last_step
    )
    primitive = frame.organism(focus.episode.organism_id)
    spatial = next(
        item
        for item in frame.spatial.organisms
        if item.organism_id == focus.episode.organism_id
    )

    assert primitive.focal_value == focus.episode.max_speed_capacity
    assert primitive.focal_normalized == pytest.approx(1.0)
    assert primitive.body_mass == spatial.body_mass
    assert not hasattr(primitive, "selected")
    assert not hasattr(primitive, "focused")


def test_representative_frames_attach_authoritative_events_not_identity_claims(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control, treatment = representative_evidence
    plan = prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
    )

    for focus in plan.representative_focus:
        frame = next(
            frame
            for frame in plan.treatment.timeline.frames
            if frame.step_index == focus.last_step
        )
        process_names = tuple(event.process_name for event in frame.applied_events)
        assert "Movement" in process_names
        assert "ResourceConsumption" in process_names
        # Appearance/departure remain separate continuity metadata and are never
        # reclassified by the director as biological events.
        assert isinstance(frame.appeared_organism_ids, tuple)
        assert isinstance(frame.departed_organism_ids, tuple)


def test_matched_representative_trajectory_uses_common_fixed_timestep_scale(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control, treatment = representative_evidence
    plan = prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
    )

    assert plan.control.timeline.world_bounds == plan.treatment.timeline.world_bounds == (
        12,
        12,
    )
    steps = tuple(point.step_index for point in plan.representative_genetic_trajectory)
    assert steps == tuple(range(51))
    assert B3_PRIMARY_STEP in steps
    primary = next(
        point
        for point in plan.representative_genetic_trajectory
        if point.step_index == B3_PRIMARY_STEP
    )
    assert primary.control_high_speed_frequency == pytest.approx(0.425)
    assert primary.treatment_high_speed_frequency == pytest.approx(0.6571428571428571)


def test_wrong_representative_seed_fails_before_direction(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control, treatment = representative_evidence
    wrong_specification = attrs.evolve(control.specification, seed=17)
    wrong_control = attrs.evolve(control, specification=wrong_specification)

    with pytest.raises(ValueError, match="representative seed 5"):
        prepare_b3_flagship_director(
            control_evidence=wrong_control,
            treatment_evidence=treatment,
        )


def test_full_plan_derives_run_level_confirmation_and_sensitivity_values(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control_evidence, treatment_evidence = representative_evidence
    control = summarize_b3_run(control_evidence)
    treatment = summarize_b3_run(treatment_evidence)
    confirmation = tuple(
        B3MatchedPairSummary(
            seed=seed,
            founder_assignment="standard",
            control=_summary_with_primary(
                control,
                seed=seed,
                value=0.30 + index * 0.01,
            ),
            treatment=_summary_with_primary(
                treatment,
                seed=seed,
                value=0.55 + index * 0.01,
            ),
        )
        for index, seed in enumerate(B3_CONFIRMATION_SEEDS)
    )
    broad = tuple(
        _summary_with_primary(
            attrs.evolve(treatment, environment="broad_patch"),
            seed=seed,
            value=0.45 + index * 0.01,
        )
        for index, seed in enumerate(B3_CONFIRMATION_SEEDS)
    )

    plan = prepare_b3_flagship_director(
        control_evidence=control_evidence,
        treatment_evidence=treatment_evidence,
        confirmation_pairs=confirmation,
        broad_patch_summaries=broad,
    )

    assert plan.is_full_flagship
    assert tuple(point.seed for point in plan.confirmation_points) == B3_CONFIRMATION_SEEDS
    assert plan.confirmation_points[0].paired_effect == pytest.approx(0.25)
    assert len(plan.founder_contribution_points) == 16
    assert plan.broad_patch_step30_mean == pytest.approx(0.485)


def test_partial_confirmation_set_is_rejected(
    representative_evidence: tuple[B3RunEvidence, B3RunEvidence],
) -> None:
    control_evidence, treatment_evidence = representative_evidence
    control = summarize_b3_run(control_evidence)
    treatment = summarize_b3_run(treatment_evidence)
    one_pair = (
        B3MatchedPairSummary(
            seed=B3_CONFIRMATION_SEEDS[0],
            founder_assignment="standard",
            control=control,
            treatment=treatment,
        ),
    )

    with pytest.raises(ValueError, match="frozen independent seeds"):
        prepare_b3_flagship_director(
            control_evidence=control_evidence,
            treatment_evidence=treatment_evidence,
            confirmation_pairs=one_pair,
        )


def _summary_with_primary(
    summary: B3RunSummary,
    *,
    seed: int,
    value: float,
) -> B3RunSummary:
    trajectory = tuple(
        attrs.evolve(point, high_speed_allele_frequency=value)
        if point.step_index == B3_PRIMARY_STEP
        else point
        for point in summary.genetic_trajectory
    )
    return attrs.evolve(summary, seed=seed, genetic_trajectory=trajectory)
