"""Tests for deterministic cinematic reproducibility metadata."""

from evo_engine.cinematic.manifest import build_cinematic_render_manifest
from evo_engine.cinematic.timeline import PortfolioAnimationTimeline
from evo_engine.presentation import ContinuousTraitEncoding


def test_manifest_records_shared_focal_encoding_without_paths() -> None:
    timeline = PortfolioAnimationTimeline(
        trait_name="growth_rate",
        focal_encoding=ContinuousTraitEncoding(
            trait_name="max_speed",
            label="Maximum speed",
            lower_bound=1,
            upper_bound=5,
        ),
    )

    manifest = build_cinematic_render_manifest(
        timeline,
        scenario_label="b2-tradeoff-proof",
        seed=23,
        renderer_version="test-version",
        quality="low",
    )

    assert manifest.to_dict() == {
        "scenario_label": "b2-tradeoff-proof",
        "seed": 23,
        "first_step": None,
        "last_step": None,
        "population_trait_name": "growth_rate",
        "focal_trait_name": "max_speed",
        "focal_label": "Maximum speed",
        "focal_lower_bound": 1,
        "focal_upper_bound": 5,
        "director_mode": "generic",
        "renderer_name": "manim",
        "renderer_version": "test-version",
        "quality": "low",
    }
    assert "path" not in " ".join(manifest.to_dict())


def test_manifest_is_deterministic_for_identical_inputs() -> None:
    timeline = PortfolioAnimationTimeline(trait_name="growth_rate")

    first = build_cinematic_render_manifest(timeline, seed=11)
    second = build_cinematic_render_manifest(timeline, seed=11)

    assert first == second
    assert first.to_dict() == second.to_dict()
