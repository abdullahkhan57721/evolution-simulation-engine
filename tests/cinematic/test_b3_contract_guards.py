"""Focused invariant guards for the concrete B3 cinematic director."""

from __future__ import annotations

import attrs
import pytest

from evo_engine.cinematic.b3_director import (
    B3_REPRESENTATIVE_SEED,
    B3ConfirmationPoint,
    B3FlagshipDirectorPlan,
    B3FounderContributionPoint,
    prepare_b3_flagship_director,
)
from evo_engine.experiments.b3_flagship import B3RunEvidence, run_b3_flagship
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_PRIMARY_STEP,
    build_b3_flagship_specification,
)


@pytest.fixture(scope="module")
def representative_plan() -> B3FlagshipDirectorPlan:
    """Prepare the frozen representative B3 plan once for invariant tests."""
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
    return prepare_b3_flagship_director(
        control_evidence=control,
        treatment_evidence=treatment,
    )


def test_representative_focus_exposes_committed_frame_bounds(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Focus bounds remain the committed frames around each authoritative event."""
    assert tuple(
        (focus.first_step, focus.last_step)
        for focus in representative_plan.representative_focus
    ) == ((6, 7), (4, 5))


def test_plan_rejects_changed_conclusion(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """The renderer cannot rewrite the confirmed scientific conclusion."""
    with pytest.raises(ValueError, match="confirmed handoff"):
        attrs.evolve(representative_plan, conclusion="A different conclusion.")


def test_plan_rejects_changed_scope_qualifier(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """The renderer cannot broaden the B3 claim boundary."""
    with pytest.raises(ValueError, match="scope qualifier"):
        attrs.evolve(representative_plan, scope_qualifier="A broader claim.")


def test_plan_rejects_changed_arm_label(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Matched-arm scientific labels remain fixed in the director value."""
    changed_control = attrs.evolve(representative_plan.control, label="Control")

    with pytest.raises(ValueError, match="arm labels"):
        attrs.evolve(representative_plan, control=changed_control)


def test_plan_rejects_changed_focal_encoding(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Matched arms cannot silently change the frozen max-speed scientific scale."""
    changed_encoding = attrs.evolve(
        representative_plan.focal_encoding,
        upper_bound=5,
    )

    with pytest.raises(ValueError, match="scale 1..4"):
        attrs.evolve(representative_plan, focal_encoding=changed_encoding)


def test_plan_rejects_changed_act_order(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """The concrete B3 explanatory order remains deterministic."""
    with pytest.raises(ValueError, match="act order"):
        attrs.evolve(
            representative_plan,
            acts=tuple(reversed(representative_plan.acts)),
        )


def test_plan_rejects_changed_representative_focus(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Renderer focus cannot replace the scientifically selected B3 episodes."""
    with pytest.raises(ValueError, match="match the handoff"):
        attrs.evolve(
            representative_plan,
            representative_focus=tuple(
                reversed(representative_plan.representative_focus)
            ),
        )


def test_plan_rejects_invalid_genetic_trajectory_shapes(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Representative genetic evidence must stay complete and time ordered."""
    with pytest.raises(ValueError, match="must not be empty"):
        attrs.evolve(representative_plan, representative_genetic_trajectory=())

    with pytest.raises(ValueError, match="unique and increasing"):
        attrs.evolve(
            representative_plan,
            representative_genetic_trajectory=tuple(
                reversed(representative_plan.representative_genetic_trajectory)
            ),
        )

    without_primary = tuple(
        point
        for point in representative_plan.representative_genetic_trajectory
        if point.step_index != B3_PRIMARY_STEP
    )
    with pytest.raises(ValueError, match="include the primary step"):
        attrs.evolve(
            representative_plan,
            representative_genetic_trajectory=without_primary,
        )


def test_confirmation_and_sensitivity_evidence_are_coupled(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Full confirmation and radius-2 sensitivity cannot be presented separately."""
    confirmation = tuple(
        B3ConfirmationPoint(
            seed=seed,
            control_high_speed_frequency=0.3,
            treatment_high_speed_frequency=0.6,
            paired_effect=0.3,
        )
        for seed in B3_CONFIRMATION_SEEDS
    )

    with pytest.raises(ValueError, match="requires broad-patch sensitivity"):
        attrs.evolve(representative_plan, confirmation_points=confirmation)

    with pytest.raises(ValueError, match="requires full confirmation"):
        attrs.evolve(representative_plan, broad_patch_step30_mean=0.5)


def test_founder_contribution_order_remains_matched(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """Founder-contribution evidence cannot be reordered or partially substituted."""
    partial = (
        B3FounderContributionPoint(
            seed=B3_CONFIRMATION_SEEDS[0],
            environment="uniform",
            low_speed_mean=1.0,
            high_speed_mean=2.0,
        ),
    )

    with pytest.raises(ValueError, match="matched run order"):
        attrs.evolve(representative_plan, founder_contribution_points=partial)


def test_prepare_rejects_non_b3_evidence() -> None:
    """The public preparation boundary rejects values outside committed B3 evidence."""
    not_evidence = object()

    with pytest.raises(TypeError, match="control_evidence"):
        prepare_b3_flagship_director(
            control_evidence=not_evidence,  # type: ignore[arg-type]
            treatment_evidence=not_evidence,  # type: ignore[arg-type]
        )


def test_prepare_rejects_nonstandard_representative_founder_assignment(
    representative_plan: B3FlagshipDirectorPlan,
) -> None:
    """The representative film remains tied to B3's standard founder assignment."""
    control: B3RunEvidence = attrs.evolve(
        representative_plan.control.evidence,
        specification=attrs.evolve(
            representative_plan.control.evidence.specification,
            founder_assignment="swapped",
        ),
    )
    treatment: B3RunEvidence = attrs.evolve(
        representative_plan.treatment.evidence,
        specification=attrs.evolve(
            representative_plan.treatment.evidence.specification,
            founder_assignment="swapped",
        ),
    )

    with pytest.raises(ValueError, match="standard founder assignment"):
        prepare_b3_flagship_director(
            control_evidence=control,
            treatment_evidence=treatment,
        )
