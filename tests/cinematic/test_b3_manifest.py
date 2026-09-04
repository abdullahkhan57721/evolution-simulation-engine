"""Tests for the concrete B3 cinematic reproducibility manifest."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from evo_engine.cinematic.b3_director import B3FlagshipDirectorPlan
from evo_engine.cinematic.b3_manifest import build_b3_flagship_render_manifest
from evo_engine.presentation import ContinuousTraitEncoding


def _plan() -> B3FlagshipDirectorPlan:
    plan = object.__new__(B3FlagshipDirectorPlan)
    timeline = SimpleNamespace(
        frames=(SimpleNamespace(step_index=0), SimpleNamespace(step_index=50))
    )
    object.__setattr__(plan, "control", SimpleNamespace(timeline=timeline))
    object.__setattr__(
        plan,
        "focal_encoding",
        ContinuousTraitEncoding(
            trait_name="max_speed",
            label="Maximum speed",
            lower_bound=1,
            upper_bound=4,
        ),
    )
    object.__setattr__(
        plan,
        "representative_focus",
        (
            SimpleNamespace(
                episode=SimpleNamespace(organism_id=16, completed_step_index=7)
            ),
            SimpleNamespace(
                episode=SimpleNamespace(organism_id=1, completed_step_index=5)
            ),
        ),
    )
    object.__setattr__(
        plan,
        "confirmation_points",
        (SimpleNamespace(seed=5), SimpleNamespace(seed=17)),
    )
    object.__setattr__(plan, "broad_patch_step30_mean", 0.5)
    return plan


def test_b3_manifest_records_stable_scalar_director_inputs() -> None:
    manifest = build_b3_flagship_render_manifest(
        _plan(),
        renderer_version="0.21.0",
        quality="high",
    )

    assert manifest.to_dict() == {
        "scenario_label": "b3-environment-dependent-max-speed",
        "director_mode": "b3_flagship",
        "representative_seed": 5,
        "first_step": 0,
        "last_step": 50,
        "primary_step": 30,
        "focal_trait_name": "max_speed",
        "focal_label": "Maximum speed",
        "focal_lower_bound": 1,
        "focal_upper_bound": 4,
        "low_speed_organism_id": 16,
        "low_speed_completed_step": 7,
        "high_speed_organism_id": 1,
        "high_speed_completed_step": 5,
        "confirmation_seed_count": 2,
        "confirmation_seeds": "5,17",
        "includes_radius2_sensitivity": True,
        "renderer_name": "manim",
        "renderer_version": "0.21.0",
        "quality": "high",
    }


def test_b3_manifest_represents_excerpt_without_confirmation_or_sensitivity() -> None:
    plan = _plan()
    object.__setattr__(plan, "confirmation_points", ())
    object.__setattr__(plan, "broad_patch_step30_mean", None)

    manifest = build_b3_flagship_render_manifest(
        plan,
        renderer_version=None,
        quality="low",
    )

    assert manifest.confirmation_seed_count == 0
    assert manifest.confirmation_seeds == ""
    assert manifest.includes_radius2_sensitivity is False
    assert manifest.renderer_version is None
    assert manifest.quality == "low"


def test_b3_manifest_rejects_wrong_plan_type() -> None:
    with pytest.raises(TypeError, match="B3FlagshipDirectorPlan"):
        build_b3_flagship_render_manifest(
            object(),  # type: ignore[arg-type]
            renderer_version="0.21.0",
            quality="low",
        )


def test_b3_manifest_rejects_unknown_quality() -> None:
    with pytest.raises(ValueError, match="quality"):
        build_b3_flagship_render_manifest(
            _plan(),
            renderer_version="0.21.0",
            quality="ultra",  # type: ignore[arg-type]
        )
